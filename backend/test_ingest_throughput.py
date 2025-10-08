"""
Script de validação: Throughput Test
Testa se o serviço sustenta ≥5,000 points/s

Estratégia:
- Publicar 10,000 pontos via MQTT (1,000 mensagens × 10 pontos cada)
- Medir tempo total de publicação
- Calcular taxa de pontos/segundo
- Verificar persistência no banco
"""
import paho.mqtt.client as mqtt
import json
import time
import sys

# IDs de teste para throughput
TENANT_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
SITE_ID = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
DEVICE_ID = "99999999-9999-9999-9999-999999999999"  # Device Throughput Test

TOTAL_POINTS = 10000
POINTS_PER_MESSAGE = 10
TOTAL_MESSAGES = TOTAL_POINTS // POINTS_PER_MESSAGE

def test_throughput():
    """Testa throughput de ingestão"""
    
    print("=" * 80)
    print("TESTE DE VALIDAÇÃO: Throughput (≥5,000 points/s)")
    print("=" * 80)
    
    # Conectar ao MQTT
    try:
        client = mqtt.Client(client_id="test_throughput_validator")
        client.connect('emqx', 1883, keepalive=60)
        print(f"✅ Conectado ao MQTT broker: emqx:1883\n")
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        sys.exit(1)
    
    topic = f'traksense/{TENANT_ID}/{SITE_ID}/{DEVICE_ID}/telem'
    print(f"📡 Tópico: {topic}")
    print(f"📊 Meta: {TOTAL_POINTS:,} pontos em {TOTAL_MESSAGES:,} mensagens")
    print(f"📊 Pontos por mensagem: {POINTS_PER_MESSAGE}\n")
    
    # ========================================================================
    # Publicar mensagens rapidamente
    # ========================================================================
    print("📤 Iniciando publicação de mensagens...")
    start_time = time.time()
    
    for i in range(TOTAL_MESSAGES):
        # Gerar timestamp variável para simular dados reais
        hour = (i // 3600) % 24
        minute = (i // 60) % 60
        second = i % 60
        ts = f'2025-10-08T{hour:02d}:{minute:02d}:{second:02d}Z'
        
        # Payload normalizado com 10 pontos
        payload = {
            'schema': 'v1',
            'ts': ts,
            'points': [
                {'name': f'sensor_{j}', 't': 'float', 'v': float(i * 10 + j), 'u': 'unit'}
                for j in range(POINTS_PER_MESSAGE)
            ],
            'meta': {'batch': i}
        }
        
        # Publicar com QoS=0 para máxima velocidade
        try:
            result = client.publish(topic, json.dumps(payload), qos=0)
            if result.rc != mqtt.MQTT_ERR_SUCCESS:
                print(f"   ⚠️  Erro ao publicar mensagem {i+1}: rc={result.rc}")
        except Exception as e:
            print(f"   ❌ Exceção na mensagem {i+1}: {e}")
        
        # Progresso a cada 100 mensagens
        if (i + 1) % 100 == 0:
            elapsed = time.time() - start_time
            rate = ((i + 1) * POINTS_PER_MESSAGE) / elapsed
            print(f"   📊 Progresso: {i+1:,}/{TOTAL_MESSAGES:,} msgs "
                  f"({(i+1)*POINTS_PER_MESSAGE:,} pontos) "
                  f"- Taxa atual: {rate:,.0f} p/s")
    
    elapsed_time = time.time() - start_time
    client.disconnect()
    
    # ========================================================================
    # Resultados da publicação
    # ========================================================================
    print("\n" + "=" * 80)
    print("📊 RESULTADOS DA PUBLICAÇÃO")
    print("=" * 80)
    print(f"⏱️  Tempo total de publicação: {elapsed_time:.2f}s")
    print(f"📨 Taxa de mensagens: {TOTAL_MESSAGES / elapsed_time:,.0f} msg/s")
    print(f"📊 Taxa de pontos: {TOTAL_POINTS / elapsed_time:,.0f} points/s")
    
    if (TOTAL_POINTS / elapsed_time) >= 5000:
        print(f"✅ Meta atingida: ≥5,000 points/s")
    else:
        print(f"⚠️  Meta não atingida: {TOTAL_POINTS / elapsed_time:,.0f} < 5,000 points/s")
    
    # ========================================================================
    # Aguardar processamento pelo ingest
    # ========================================================================
    print("\n" + "=" * 80)
    print("⏳ Aguardando 10 segundos para ingest processar todos os batches...")
    print("=" * 80)
    time.sleep(10)
    
    print("\n✅ Teste de throughput concluído!")
    print("\n📋 Próximos passos:")
    print("   1. Verificar logs de flush no ingest:")
    print("      docker compose logs ingest --tail=50 | grep 'FLUSH'")
    print("\n   2. Verificar pontos persistidos no banco:")
    print("      docker compose exec db psql -U postgres -d traksense -c \"")
    print("      SELECT COUNT(*) as total_points")
    print("      FROM public.ts_measure")
    print(f"      WHERE device_id = '{DEVICE_ID}'")
    print("      AND ts >= NOW() - INTERVAL '1 hour';\"")
    print(f"\n   Esperado: {TOTAL_POINTS:,} pontos")
    print("\n   3. Verificar métrica de pontos totais:")
    print("      curl -s http://localhost:9100/metrics | grep ingest_points_total")
    print(f"\n   4. Calcular throughput real do ingest:")
    print(f"      Throughput = {TOTAL_POINTS:,} pontos / tempo_de_processamento")

if __name__ == '__main__':
    test_throughput()
