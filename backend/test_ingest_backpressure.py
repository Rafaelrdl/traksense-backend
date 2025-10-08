"""
Script de validação: Backpressure + Latência (100k pontos)
Testa se a fila bloqueia corretamente quando cheia e mede latência

Estratégia:
- Publicar 100,000 pontos rapidamente (10k mensagens × 10 pontos)
- Monitorar gauge ingest_queue_size durante o processo
- Verificar se fila atinge limite (maxsize=50000) e producer bloqueia
- Medir latência p50 com timestamps reais
- Verificar que não há perda de dados
"""
import paho.mqtt.client as mqtt
import json
import time
import sys
from datetime import datetime, timezone
import threading

# IDs de teste para backpressure
TENANT_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
SITE_ID = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
DEVICE_ID = "66666666-6666-6666-6666-666666666666"  # Device Backpressure Test

TOTAL_POINTS = 100000
POINTS_PER_MESSAGE = 10
TOTAL_MESSAGES = TOTAL_POINTS // POINTS_PER_MESSAGE

# Flag para monitoramento de métricas
monitoring = True

def monitor_metrics():
    """Thread para monitorar métricas em tempo real"""
    import urllib.request
    
    print("\n📊 Monitoramento de métricas iniciado...")
    max_queue_size = 0
    
    while monitoring:
        try:
            response = urllib.request.urlopen('http://emqx:9100/metrics', timeout=1)
            content = response.read().decode('utf-8')
            
            for line in content.split('\n'):
                if line.startswith('ingest_queue_size'):
                    try:
                        queue_size = float(line.split()[1])
                        if queue_size > max_queue_size:
                            max_queue_size = queue_size
                            print(f"   📈 Queue size: {int(queue_size):,} (máximo até agora)")
                    except:
                        pass
        except:
            pass
        
        time.sleep(0.5)
    
    print(f"\n✅ Monitoramento finalizado. Tamanho máximo da fila: {int(max_queue_size):,}")

def test_backpressure():
    """Testa backpressure e latência com 100k pontos"""
    global monitoring
    
    print("=" * 80)
    print("TESTE DE VALIDAÇÃO: Backpressure + Latência (100k pontos)")
    print("=" * 80)
    
    # Conectar ao MQTT
    try:
        client = mqtt.Client(client_id="test_backpressure_validator")
        client.connect('emqx', 1883, keepalive=60)
        print(f"✅ Conectado ao MQTT broker: emqx:1883\n")
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        sys.exit(1)
    
    topic = f'traksense/{TENANT_ID}/{SITE_ID}/{DEVICE_ID}/telem'
    print(f"📡 Tópico: {topic}")
    print(f"📊 Total: {TOTAL_POINTS:,} pontos em {TOTAL_MESSAGES:,} mensagens")
    print(f"📊 Pontos por mensagem: {POINTS_PER_MESSAGE}")
    print(f"🎯 Metas:")
    print(f"   - Fila atinge limite (~50k) e drena")
    print(f"   - Producer bloqueia quando fila cheia")
    print(f"   - Latência p50 ≤1.0s")
    print(f"   - Sem perda de dados\n")
    
    # Iniciar monitoramento em thread separada
    monitor_thread = threading.Thread(target=monitor_metrics, daemon=True)
    monitor_thread.start()
    
    # ========================================================================
    # Publicar mensagens rapidamente
    # ========================================================================
    print("📤 Iniciando publicação de mensagens (burst mode)...")
    start_time = time.time()
    first_ts = None
    last_ts = None
    
    for i in range(TOTAL_MESSAGES):
        # Timestamp atual
        ts_now = datetime.now(timezone.utc)
        ts_str = ts_now.isoformat().replace('+00:00', 'Z')
        
        if i == 0:
            first_ts = ts_now
        if i == TOTAL_MESSAGES - 1:
            last_ts = ts_now
        
        # Payload com 10 pontos
        payload = {
            'schema': 'v1',
            'ts': ts_str,
            'points': [
                {'name': f'bp_sensor_{j}', 't': 'float', 'v': float(i * 10 + j), 'u': 'unit'}
                for j in range(POINTS_PER_MESSAGE)
            ],
            'meta': {'batch': i // 100, 'seq': i}
        }
        
        try:
            # QoS=0 para máxima velocidade
            result = client.publish(topic, json.dumps(payload), qos=0)
            if result.rc != mqtt.MQTT_ERR_SUCCESS:
                print(f"   ⚠️  Erro ao publicar mensagem {i+1}: rc={result.rc}")
        except Exception as e:
            print(f"   ❌ Exceção na mensagem {i+1}: {e}")
        
        # Progresso a cada 1000 mensagens
        if (i + 1) % 1000 == 0:
            elapsed = time.time() - start_time
            rate = ((i + 1) * POINTS_PER_MESSAGE) / elapsed
            print(f"   📊 Progresso: {i+1:,}/{TOTAL_MESSAGES:,} msgs "
                  f"({(i+1)*POINTS_PER_MESSAGE:,} pontos) "
                  f"- Taxa: {rate:,.0f} p/s")
    
    elapsed_time = time.time() - start_time
    client.disconnect()
    
    # Parar monitoramento
    time.sleep(1)
    monitoring = False
    
    # ========================================================================
    # Resultados da publicação
    # ========================================================================
    print("\n" + "=" * 80)
    print("📊 RESULTADOS DA PUBLICAÇÃO")
    print("=" * 80)
    print(f"⏱️  Tempo de publicação: {elapsed_time:.2f}s")
    print(f"📨 Taxa de mensagens: {TOTAL_MESSAGES / elapsed_time:,.0f} msg/s")
    print(f"📊 Taxa de pontos: {TOTAL_POINTS / elapsed_time:,.0f} points/s")
    
    # ========================================================================
    # Aguardar processamento
    # ========================================================================
    print("\n" + "=" * 80)
    print("⏳ Aguardando 30 segundos para ingest processar todos os batches...")
    print("=" * 80)
    time.sleep(30)
    
    print("\n✅ Teste de backpressure concluído!")
    print("\n📋 Próximos passos:")
    print("   1. Verificar pontos persistidos:")
    print("      docker compose exec db psql -U postgres -d traksense -c \"")
    print("      SELECT COUNT(*) as total_points")
    print("      FROM public.ts_measure")
    print(f"      WHERE device_id = '{DEVICE_ID}';\"")
    print(f"\n   Esperado: ~{TOTAL_POINTS:,} pontos")
    print("\n   2. Calcular latência p50:")
    print("      docker compose exec db psql -U postgres -d traksense -c \"")
    print("      WITH latencies AS (")
    print("        SELECT EXTRACT(EPOCH FROM (NOW() - ts)) as latency_seconds")
    print("        FROM public.ts_measure")
    print(f"        WHERE device_id = '{DEVICE_ID}'")
    print("      )")
    print("      SELECT ")
    print("        COUNT(*) as total,")
    print("        ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY latency_seconds)::numeric, 3) as p50_latency,")
    print("        ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_seconds)::numeric, 3) as p95_latency")
    print("      FROM latencies;\"")
    print("\n   3. Verificar métricas finais:")
    print("      curl -s http://localhost:9100/metrics | grep 'ingest_queue_size\\|ingest_points_total'")

if __name__ == '__main__':
    test_backpressure()
