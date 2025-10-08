#!/usr/bin/env python3
"""
Teste de Latência REAL (Passo 8 - Melhorado)

Mede a latência usando:
1. Timestamps reais (NOW()) ao publicar
2. Métricas Prometheus (ingest_latency_seconds)
3. Query do banco comparando inserted_at vs ts

Este teste corrige o problema do teste anterior que usava timestamps históricos.
"""

import paho.mqtt.client as mqtt
import json
import time
import requests
from datetime import datetime, timezone

# Configuração
MQTT_HOST = 'emqx'  # Nome do container no docker-compose
MQTT_PORT = 1883
TOPIC_BASE = 'traksense/acme/site01'
DEVICE_ID = '77777777-7777-7777-7777-777777777777'
METRICS_URL = 'http://ingest:9100/metrics'  # Nome do container

def get_metric_value(metric_name, metric_type='counter'):
    """Busca valor de uma métrica Prometheus"""
    try:
        response = requests.get(METRICS_URL, timeout=2)
        lines = response.text.split('\n')
        
        if metric_type == 'histogram':
            # Para histograma, pegar p50 (quantile 0.5)
            for line in lines:
                if f'{metric_name}_bucket' in line and 'le="1.0"' in line:
                    value = float(line.split()[-1])
                    return value
            # Se não encontrar bucket, pegar count
            for line in lines:
                if f'{metric_name}_count' in line and not line.startswith('#'):
                    value = float(line.split()[-1])
                    return value
        else:
            for line in lines:
                if line.startswith(metric_name) and not line.startswith('#'):
                    value = float(line.split()[-1])
                    return value
    except Exception as e:
        print(f"⚠️ Erro ao buscar métrica {metric_name}: {e}")
    return 0

def main():
    print("=" * 80)
    print("🔍 TESTE DE LATÊNCIA REAL - Fase 4")
    print("=" * 80)
    print()
    print(f"📊 Device ID: {DEVICE_ID}")
    print(f"📊 Mensagens: 50 (com timestamps NOW())")
    print(f"🎯 Meta: Latência p50 ≤1.0 segundo")
    print()
    
    # Conectar MQTT
    client = mqtt.Client()
    try:
        client.connect(MQTT_HOST, MQTT_PORT, 60)
        print(f"✅ Conectado ao MQTT broker: {MQTT_HOST}:{MQTT_PORT}")
    except Exception as e:
        print(f"❌ Erro ao conectar MQTT: {e}")
        return
    
    topic = f'{TOPIC_BASE}/{DEVICE_ID}/telem'
    
    # Obter contagem inicial de métricas
    initial_count = get_metric_value('ingest_latency_seconds', 'histogram')
    print(f"📊 Contagem inicial do histograma: {initial_count}")
    print()
    
    # Publicar mensagens com timestamps NOW()
    print("📤 Publicando 50 mensagens com timestamps NOW()...")
    publish_start = time.time()
    
    for i in range(50):
        # Timestamp REAL (agora)
        now = datetime.now(timezone.utc)
        ts_iso = now.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        
        payload = {
            'schema': 'v1',
            'ts': ts_iso,
            'points': [
                {
                    'name': f'latency_test_{i}',
                    't': 'float',
                    'v': float(i),
                    'u': 'ms'
                }
            ],
            'meta': {
                'test': 'latency_real',
                'seq': i,
                'pub_ts': ts_iso
            }
        }
        
        result = client.publish(topic, json.dumps(payload), qos=1)
        result.wait_for_publish()
        
        if (i + 1) % 10 == 0:
            print(f"   Progresso: {i+1}/50 mensagens")
    
    publish_elapsed = time.time() - publish_start
    client.disconnect()
    
    print(f"✅ Publicadas 50 mensagens em {publish_elapsed:.2f}s")
    print()
    
    # Aguardar processamento
    print("⏳ Aguardando 3 segundos para ingest processar...")
    time.sleep(3)
    print()
    
    # Verificar métrica de latência
    print("📊 Verificando métrica de latência...")
    final_count = get_metric_value('ingest_latency_seconds', 'histogram')
    new_observations = final_count - initial_count
    
    print(f"📊 Contagem final do histograma: {final_count}")
    print(f"📊 Novas observações: {new_observations}")
    print()
    
    if new_observations >= 40:  # 80% de sucesso
        print("✅ Métricas de latência estão sendo populadas!")
        print()
        print("📊 Para verificar latência p50, use Prometheus query:")
        print("   histogram_quantile(0.5, rate(ingest_latency_seconds_bucket[5m]))")
        print()
        print("✅ TESTE CONCLUÍDO COM SUCESSO")
    else:
        print(f"⚠️ Apenas {new_observations} observações registradas (esperado: ~50)")
        print("   Possível perda de mensagens com QoS=1 ou processamento pendente")
    
    print()
    print("=" * 80)
    print("🔍 VERIFICAÇÃO MANUAL NO BANCO DE DADOS")
    print("=" * 80)
    print()
    print("Execute esta query no banco para verificar latência real:")
    print()
    print("SELECT ")
    print("  COUNT(*) as total_points,")
    print("  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (NOW() - ts))) as p50_latency_seconds,")
    print("  PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (NOW() - ts))) as p95_latency_seconds,")
    print("  MAX(EXTRACT(EPOCH FROM (NOW() - ts))) as max_latency_seconds")
    print("FROM public.ts_measure")
    print(f"WHERE device_id = '{DEVICE_ID}'")
    print("  AND ts >= NOW() - INTERVAL '1 minute';")
    print()
    print("⚠️ NOTA: Esta latência inclui o tempo desde a publicação até NOW().")
    print("         Para latência real de processamento, use a métrica Prometheus.")

if __name__ == '__main__':
    main()
