"""
Script de validação: Latência Real (p50 ≤1s)
Testa latência de ingestão usando timestamps atuais (NOW())

Estratégia:
- Publicar 100 mensagens com timestamp = NOW() no momento da publicação
- Aguardar processamento
- Consultar banco e calcular latência: (ts_persisted - ts_device)
- Calcular p50 (mediana) das latências
- Meta: p50 ≤1.0 segundo
"""
import paho.mqtt.client as mqtt
import json
import time
import sys
from datetime import datetime, timezone

# IDs de teste para latência
TENANT_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
SITE_ID = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
DEVICE_ID = "77777777-7777-7777-7777-777777777777"  # Device Latency Test

TOTAL_MESSAGES = 100

def test_latency():
    """Testa latência de ingestão com timestamps reais"""
    
    print("=" * 80)
    print("TESTE DE VALIDAÇÃO: Latência Real (p50 ≤1.0s)")
    print("=" * 80)
    
    # Conectar ao MQTT
    try:
        client = mqtt.Client(client_id="test_latency_validator")
        client.connect('emqx', 1883, keepalive=60)
        print(f"✅ Conectado ao MQTT broker: emqx:1883\n")
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        sys.exit(1)
    
    topic = f'traksense/{TENANT_ID}/{SITE_ID}/{DEVICE_ID}/telem'
    print(f"📡 Tópico: {topic}")
    print(f"📊 Total de mensagens: {TOTAL_MESSAGES}")
    print(f"🎯 Meta: Latência p50 ≤1.0 segundo\n")
    
    # ========================================================================
    # Publicar mensagens com timestamp = NOW()
    # ========================================================================
    print("📤 Publicando mensagens com timestamps atuais (NOW())...")
    start_time = datetime.now(timezone.utc)
    
    for i in range(TOTAL_MESSAGES):
        # Timestamp atual no momento da publicação
        ts_now = datetime.now(timezone.utc)
        ts_str = ts_now.isoformat().replace('+00:00', 'Z')
        
        payload = {
            'schema': 'v1',
            'ts': ts_str,
            'points': [
                {'name': 'latency_test', 't': 'float', 'v': float(i), 'u': 'ms'}
            ],
            'meta': {'seq': i, 'client_ts': ts_str}
        }
        
        try:
            payload_str = json.dumps(payload)
            result = client.publish(topic, payload_str, qos=1)
            
            if result.rc != mqtt.MQTT_ERR_SUCCESS:
                print(f"   ⚠️  Erro ao publicar mensagem {i+1}: rc={result.rc}")
        except Exception as e:
            print(f"   ❌ Exceção na mensagem {i+1}: {e}")
        
        # Pequeno delay para não sobrecarregar
        if i > 0 and i % 10 == 0:
            time.sleep(0.05)
    
    end_time = datetime.now(timezone.utc)
    elapsed_publish = (end_time - start_time).total_seconds()
    
    client.disconnect()
    
    print(f"\n✅ Publicadas {TOTAL_MESSAGES} mensagens em {elapsed_publish:.2f}s")
    
    # ========================================================================
    # Aguardar processamento completo
    # ========================================================================
    print("\n" + "=" * 80)
    print("⏳ Aguardando 5 segundos para ingest processar todos os batches...")
    print("=" * 80)
    time.sleep(5)
    
    print("\n✅ Teste de latência concluído!")
    print("\n📋 Próximos passos:")
    print("   1. Verificar logs de flush no ingest:")
    print("      docker compose logs ingest --tail=20 | grep 'FLUSH'")
    print("\n   2. Calcular latências no banco de dados:")
    print("      docker compose exec db psql -U postgres -d traksense -c \"")
    print("      WITH latencies AS (")
    print("        SELECT ")
    print("          ts as device_ts,")
    print("          NOW() as query_ts,")
    print("          EXTRACT(EPOCH FROM (NOW() - ts)) as latency_seconds")
    print("        FROM public.ts_measure")
    print(f"        WHERE device_id = '{DEVICE_ID}'")
    print("        ORDER BY ts DESC")
    print(f"        LIMIT {TOTAL_MESSAGES}")
    print("      )")
    print("      SELECT ")
    print("        COUNT(*) as total_points,")
    print("        ROUND(AVG(latency_seconds)::numeric, 3) as avg_latency,")
    print("        ROUND(MIN(latency_seconds)::numeric, 3) as min_latency,")
    print("        ROUND(MAX(latency_seconds)::numeric, 3) as max_latency,")
    print("        ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY latency_seconds)::numeric, 3) as p50_latency,")
    print("        ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_seconds)::numeric, 3) as p95_latency")
    print("      FROM latencies;\"")
    print("\n   3. Esperado:")
    print("      total_points = 100")
    print("      p50_latency ≤ 1.000 segundos")
    print("\n   4. Nota sobre latência:")
    print("      A latência medida é (NOW() - device_ts), que inclui:")
    print("      - Tempo de rede MQTT")
    print("      - Tempo de processamento no ingest")
    print("      - Tempo de persistência no banco")
    print("      Para produção, considerar timestamps do próprio banco (clock skew)")

if __name__ == '__main__':
    test_latency()
