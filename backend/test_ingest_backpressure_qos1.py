#!/usr/bin/env python3
"""
Teste de Backpressure com QoS=1 (Passo 10 - Melhorado)

Este teste corrige o problema do teste anterior:
- Usa QoS=1 (não QoS=0) para garantir entrega
- Publica mais rápido para forçar acúmulo na fila
- Monitora queue_size em tempo real
- Volume: 100,000 pontos em rajada
"""

import paho.mqtt.client as mqtt
import json
import time
import requests
import threading
from datetime import datetime, timezone

# Configuração
MQTT_HOST = 'emqx'  # Nome do container no docker-compose
MQTT_PORT = 1883
TOPIC_BASE = 'traksense/acme/site01'
DEVICE_ID = '55555555-5555-5555-5555-555555555555'
METRICS_URL = 'http://ingest:9100/metrics'  # Nome do container

# Parâmetros do teste
TOTAL_POINTS = 100000
POINTS_PER_MESSAGE = 10
TOTAL_MESSAGES = TOTAL_POINTS // POINTS_PER_MESSAGE

# Monitoramento
monitoring = True
max_queue_size = 0
queue_sizes = []

def get_metric_value(metric_name):
    """Busca valor de uma métrica Prometheus"""
    try:
        response = requests.get(METRICS_URL, timeout=1)
        for line in response.text.split('\n'):
            if line.startswith(metric_name) and not line.startswith('#'):
                return float(line.split()[-1])
    except:
        pass
    return 0

def monitor_queue():
    """Thread para monitorar tamanho da fila em tempo real"""
    global max_queue_size, monitoring, queue_sizes
    
    print("🔍 Iniciando monitoramento da fila...")
    
    while monitoring:
        size = get_metric_value('ingest_queue_size')
        queue_sizes.append(size)
        
        if size > max_queue_size:
            max_queue_size = size
            if size > 0:
                print(f"   📊 Queue size: {int(size):,} (novo máximo!)")
        
        time.sleep(0.1)  # Monitorar a cada 100ms

def main():
    global monitoring
    
    print("=" * 80)
    print("🚀 TESTE DE BACKPRESSURE COM QoS=1 - Fase 4")
    print("=" * 80)
    print()
    print(f"📊 Device ID: {DEVICE_ID}")
    print(f"📊 Total: {TOTAL_POINTS:,} pontos em {TOTAL_MESSAGES:,} mensagens")
    print(f"📊 QoS: 1 (garantia de entrega)")
    print(f"🎯 Objetivo: Verificar se fila acumula (maxsize=50,000)")
    print()
    
    # Iniciar monitoramento em thread separada
    monitor_thread = threading.Thread(target=monitor_queue, daemon=True)
    monitor_thread.start()
    
    # Conectar MQTT
    client = mqtt.Client()
    client.enable_logger()
    
    try:
        client.connect(MQTT_HOST, MQTT_PORT, 60)
        client.loop_start()
        print(f"✅ Conectado ao MQTT broker: {MQTT_HOST}:{MQTT_PORT}")
    except Exception as e:
        print(f"❌ Erro ao conectar MQTT: {e}")
        monitoring = False
        return
    
    topic = f'{TOPIC_BASE}/{DEVICE_ID}/telem'
    
    # Obter contagens iniciais
    initial_points = get_metric_value('ingest_points_total')
    print(f"📊 Pontos iniciais no ingest: {int(initial_points):,}")
    print()
    
    # Publicar mensagens em rajada
    print(f"📤 Publicando {TOTAL_MESSAGES:,} mensagens com QoS=1...")
    print("   (Isso pode demorar alguns minutos...)")
    print()
    
    publish_start = time.time()
    published = 0
    failed = 0
    
    for i in range(TOTAL_MESSAGES):
        # Timestamp base para simular dados históricos (evita clock skew)
        base_ts = datetime(2025, 10, 8, 10, 0, 0, tzinfo=timezone.utc)
        offset_seconds = i * 10  # 10 segundos entre cada mensagem
        ts = base_ts.replace(second=(base_ts.second + offset_seconds) % 60)
        ts_iso = ts.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        
        payload = {
            'schema': 'v1',
            'ts': ts_iso,
            'points': [
                {
                    'name': f'bp_test_{j}',
                    't': 'float',
                    'v': float(i * POINTS_PER_MESSAGE + j),
                    'u': 'unit'
                }
                for j in range(POINTS_PER_MESSAGE)
            ],
            'meta': {
                'test': 'backpressure_qos1',
                'batch': i
            }
        }
        
        # Publicar com QoS=1 e aguardar confirmação
        try:
            result = client.publish(topic, json.dumps(payload), qos=1)
            result.wait_for_publish(timeout=5.0)
            published += 1
        except Exception as e:
            failed += 1
            if failed < 10:  # Só mostrar primeiros 10 erros
                print(f"   ⚠️ Erro ao publicar mensagem {i}: {e}")
        
        # Progresso a cada 1000 mensagens
        if (i + 1) % 1000 == 0:
            elapsed = time.time() - publish_start
            rate = (i + 1) * POINTS_PER_MESSAGE / elapsed
            current_queue = int(get_metric_value('ingest_queue_size'))
            print(f"   📊 Progresso: {i+1:,}/{TOTAL_MESSAGES:,} msgs ({(i+1)*POINTS_PER_MESSAGE:,} pontos) - Taxa: {rate:,.0f} p/s - Queue: {current_queue:,}")
    
    publish_elapsed = time.time() - publish_start
    client.loop_stop()
    client.disconnect()
    
    print()
    print(f"✅ Publicação concluída!")
    print(f"   ⏱️  Tempo de publicação: {publish_elapsed:.2f}s")
    print(f"   📊 Taxa de pontos: {TOTAL_POINTS / publish_elapsed:,.0f} points/s")
    print(f"   ✅ Publicadas: {published:,} mensagens")
    print(f"   ❌ Falhadas: {failed:,} mensagens")
    print()
    
    # Aguardar processamento
    print("⏳ Aguardando 10 segundos para ingest processar...")
    time.sleep(10)
    
    # Parar monitoramento
    monitoring = False
    time.sleep(0.5)
    
    # Resultados finais
    print()
    print("=" * 80)
    print("📊 RESULTADOS")
    print("=" * 80)
    print()
    
    final_points = get_metric_value('ingest_points_total')
    persisted = int(final_points - initial_points)
    
    print(f"📊 Pontos publicados: {published * POINTS_PER_MESSAGE:,}")
    print(f"📊 Pontos persistidos: {persisted:,}")
    print(f"📊 Taxa de sucesso: {persisted / (published * POINTS_PER_MESSAGE) * 100:.1f}%")
    print()
    
    print(f"📊 Tamanho máximo da fila: {int(max_queue_size):,}")
    if max_queue_size > 1000:
        print("✅ Fila acumulou significativamente! Backpressure testado.")
    elif max_queue_size > 0:
        print("⚠️ Fila acumulou um pouco, mas não muito.")
    else:
        print("⚠️ Fila não acumulou (size=0). Sistema muito rápido ou QoS=1 atrasou publicação.")
    print()
    
    if queue_sizes:
        avg_queue = sum(queue_sizes) / len(queue_sizes)
        print(f"📊 Tamanho médio da fila: {avg_queue:.1f}")
    
    print()
    print("=" * 80)
    print("🔍 VERIFICAÇÃO NO BANCO DE DADOS")
    print("=" * 80)
    print()
    print("Execute esta query para verificar os dados:")
    print()
    print(f"SELECT COUNT(*) FROM public.ts_measure WHERE device_id = '{DEVICE_ID}';")
    print()
    
    if persisted >= TOTAL_POINTS * 0.95:
        print("✅ TESTE CONCLUÍDO COM SUCESSO (≥95% de sucesso)")
    elif persisted >= TOTAL_POINTS * 0.8:
        print("⚠️ TESTE PARCIALMENTE CONCLUÍDO (≥80% de sucesso)")
    else:
        print("❌ TESTE FALHOU (<80% de sucesso)")

if __name__ == '__main__':
    main()
