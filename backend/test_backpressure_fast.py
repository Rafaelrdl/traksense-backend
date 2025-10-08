#!/usr/bin/env python3
"""
Teste de Backpressure RÁPIDO (Passo 10)

Versão reduzida para validação rápida:
- 10,000 pontos (vs 100,000 do original)
- QoS=1 para garantir entrega  
- Monitora queue_size em tempo real
- Tempo estimado: ~30 segundos
"""

import paho.mqtt.client as mqtt
import json
import time
import requests
import threading
from datetime import datetime, timezone

# Configuração
MQTT_HOST = 'emqx'
MQTT_PORT = 1883
# Usar UUID válido para tenant
TENANT_UUID = '11111111-1111-1111-1111-111111111111'
SITE_ID = 'site01'
DEVICE_ID = '66666666-6666-6666-6666-666666666666'
TOPIC_BASE = f'traksense/{TENANT_UUID}/{SITE_ID}'

# Parâmetros do teste (reduzido)
TOTAL_POINTS = 10000
POINTS_PER_MESSAGE = 10
TOTAL_MESSAGES = TOTAL_POINTS // POINTS_PER_MESSAGE

# Monitoramento
monitoring = True
max_queue_size = 0
queue_sizes = []

def get_metric_value(metric_name):
    """Busca valor de uma métrica Prometheus via API container"""
    try:
        response = requests.get('http://localhost:9100/metrics', timeout=1)
        for line in response.text.split('\n'):
            if line.startswith(metric_name) and not line.startswith('#'):
                return float(line.split()[-1])
    except:
        pass
    return 0

def monitor_queue():
    """Thread para monitorar tamanho da fila"""
    global max_queue_size, monitoring, queue_sizes
    
    while monitoring:
        size = get_metric_value('ingest_queue_size')
        queue_sizes.append(size)
        if size > max_queue_size:
            max_queue_size = size
        time.sleep(0.1)  # Monitorar a cada 100ms

def main():
    print("=" * 60)
    print("🚀 TESTE DE BACKPRESSURE RÁPIDO")
    print("=" * 60)
    print()
    print(f"📊 Device: {DEVICE_ID}")
    print(f"📊 Total de pontos: {TOTAL_POINTS:,}")
    print(f"📊 Mensagens: {TOTAL_MESSAGES:,} (10 pontos cada)")
    print(f"📊 QoS: 1 (guaranteed delivery)")
    print()
    
    # Iniciar monitoramento da fila
    print("🔍 Iniciando monitoramento da fila...")
    monitor_thread = threading.Thread(target=monitor_queue, daemon=True)
    monitor_thread.start()
    time.sleep(0.5)
    
    # Conectar MQTT
    client = mqtt.Client()
    
    try:
        print("🔌 Conectando ao MQTT...")
        client.connect(MQTT_HOST, MQTT_PORT, 60)
        client.loop_start()
        time.sleep(0.5)
        print("✅ Conectado!")
        print()
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        return
    
    topic = f'{TOPIC_BASE}/{DEVICE_ID}/telem'
    
    # Métricas iniciais
    initial_points = get_metric_value('ingest_points_total')
    initial_errors = get_metric_value('ingest_errors_total')
    
    print(f"📊 Pontos antes: {initial_points:.0f}")
    print(f"📊 Erros antes: {initial_errors:.0f}")
    print()
    
    # Publicar mensagens em rajada
    print(f"📤 Publicando {TOTAL_MESSAGES:,} mensagens...")
    start = time.time()
    
    for i in range(TOTAL_MESSAGES):
        now = datetime.now(timezone.utc)
        ts_iso = now.isoformat().replace('+00:00', 'Z')
        
        # 10 pontos por mensagem
        points = []
        for j in range(10):
            points.append({
                'name': f'sensor_{j}',
                't': 'float',
                'v': float(i * 10 + j),
                'u': 'units'
            })
        
        payload = {
            'schema': 'v1',
            'ts': ts_iso,
            'points': points,
            'meta': {'test': 'backpressure_fast', 'batch': i}
        }
        
        result = client.publish(topic, json.dumps(payload), qos=1)
        result.wait_for_publish(timeout=5.0)
        
        # Progresso a cada 10%
        if (i + 1) % (TOTAL_MESSAGES // 10) == 0:
            pct = ((i + 1) / TOTAL_MESSAGES) * 100
            elapsed = time.time() - start
            queue = get_metric_value('ingest_queue_size')
            print(f"   {pct:3.0f}% - {i+1:,}/{TOTAL_MESSAGES:,} msgs - queue: {queue:,.0f} - {elapsed:.1f}s")
    
    publish_elapsed = time.time() - start
    print()
    print(f"✅ Publicação concluída em {publish_elapsed:.2f}s")
    print(f"📊 Taxa de publicação: {TOTAL_MESSAGES/publish_elapsed:.0f} msgs/s")
    print()
    
    # Aguardar processamento
    print("⏳ Aguardando processamento completo (máx 30s)...")
    wait_start = time.time()
    
    while time.time() - wait_start < 30:
        current_points = get_metric_value('ingest_points_total')
        processed = current_points - initial_points
        queue = get_metric_value('ingest_queue_size')
        
        if processed >= TOTAL_POINTS and queue == 0:
            print(f"✅ Processamento completo em {time.time() - wait_start:.1f}s")
            break
        
        if int(time.time() - wait_start) % 5 == 0:
            print(f"   Aguardando... processados: {processed:.0f}/{TOTAL_POINTS} - queue: {queue:.0f}")
        
        time.sleep(1)
    
    # Parar monitoramento
    global monitoring
    monitoring = False
    time.sleep(0.2)
    
    client.loop_stop()
    client.disconnect()
    
    # Métricas finais
    final_points = get_metric_value('ingest_points_total')
    final_errors = get_metric_value('ingest_errors_total')
    
    processed = final_points - initial_points
    errors = final_errors - initial_errors
    
    print()
    print("=" * 60)
    print("📊 RESULTADOS")
    print("=" * 60)
    print()
    print(f"✅ Pontos processados: {processed:.0f}/{TOTAL_POINTS}")
    print(f"❌ Erros: {errors:.0f}")
    print(f"📊 Taxa de sucesso: {(processed/TOTAL_POINTS)*100:.1f}%")
    print()
    print(f"📈 Fila - Tamanho máximo: {max_queue_size:.0f}")
    print(f"📈 Fila - Tamanho médio: {sum(queue_sizes)/len(queue_sizes):.1f}" if queue_sizes else "")
    print()
    
    # Validação
    if processed >= TOTAL_POINTS * 0.95:  # 95% de sucesso
        print("✅ TESTE DE BACKPRESSURE APROVADO!")
        print("   Sistema processou ≥95% dos pontos sob carga")
    else:
        print(f"⚠️ TESTE PARCIAL: {(processed/TOTAL_POINTS)*100:.1f}% processados")
    
    print()

if __name__ == '__main__':
    main()
