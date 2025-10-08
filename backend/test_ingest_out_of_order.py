"""
Script de validação: Out-of-Order Timestamps
Testa se o ingest aceita timestamps fora de ordem sem erros

Estratégia:
- Publicar 5 mensagens com timestamps em ordem invertida
- Verificar que todas foram aceitas e persistidas
- Confirmar que não há erros de constraint ou ordenação
"""
import paho.mqtt.client as mqtt
import json
import time
import sys

# IDs de teste para out-of-order
TENANT_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
SITE_ID = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
DEVICE_ID = "88888888-8888-8888-8888-888888888888"  # Device Out-of-Order Test

def test_out_of_order():
    """Testa aceitação de timestamps fora de ordem"""
    
    print("=" * 80)
    print("TESTE DE VALIDAÇÃO: Out-of-Order Timestamps")
    print("=" * 80)
    
    # Conectar ao MQTT
    try:
        client = mqtt.Client(client_id="test_out_of_order_validator")
        client.connect('emqx', 1883, keepalive=60)
        print(f"✅ Conectado ao MQTT broker: emqx:1883\n")
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        sys.exit(1)
    
    topic = f'traksense/{TENANT_ID}/{SITE_ID}/{DEVICE_ID}/telem'
    print(f"📡 Tópico: {topic}\n")
    
    # ========================================================================
    # Timestamps fora de ordem (propositalmente invertidos)
    # ========================================================================
    timestamps = [
        '2025-10-08T10:05:00Z',  # 5º (mais recente)
        '2025-10-08T10:02:00Z',  # 2º
        '2025-10-08T10:04:00Z',  # 4º
        '2025-10-08T10:01:00Z',  # 1º (mais antigo)
        '2025-10-08T10:03:00Z',  # 3º (meio)
    ]
    
    print("📤 Publicando mensagens com timestamps FORA DE ORDEM:")
    print("=" * 80)
    
    for i, ts in enumerate(timestamps):
        payload = {
            'schema': 'v1',
            'ts': ts,
            'points': [
                {'name': 'test_value', 't': 'float', 'v': float(i), 'u': 'unit'}
            ],
            'meta': {'seq': i}
        }
        
        try:
            payload_str = json.dumps(payload)
            result = client.publish(topic, payload_str, qos=1)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"   ✅ Msg {i+1}/5: ts={ts}, value={float(i):.1f} - Publicado")
            else:
                print(f"   ❌ Msg {i+1}/5: FALHOU (rc={result.rc})")
        except Exception as e:
            print(f"   ❌ Msg {i+1}/5: Exceção: {e}")
        
        time.sleep(0.3)
    
    client.disconnect()
    
    # ========================================================================
    # Aguardar processamento
    # ========================================================================
    print("\n" + "=" * 80)
    print("⏳ Aguardando 4 segundos para ingest processar...")
    print("=" * 80)
    time.sleep(4)
    
    print("\n✅ Teste de out-of-order timestamps concluído!")
    print("\n📋 Próximos passos:")
    print("   1. Verificar logs do ingest (não deve ter erros):")
    print("      docker compose logs ingest --tail=20 | grep -i 'error\\|constraint'")
    print("\n   2. Verificar pontos no banco (devem estar todos lá):")
    print("      docker compose exec db psql -U postgres -d traksense -c \"")
    print("      SELECT ts, v_num")
    print("      FROM public.ts_measure")
    print(f"      WHERE device_id = '{DEVICE_ID}'")
    print("      ORDER BY ts;\"")
    print("\n   Esperado: 5 linhas ordenadas por timestamp (não por ordem de inserção)")
    print("\n   3. Resultado esperado:")
    print("             ts          | v_num")
    print("      -------------------+-------")
    print("       2025-10-08 10:01:00 |   3.0  (4ª inserção)")
    print("       2025-10-08 10:02:00 |   1.0  (2ª inserção)")
    print("       2025-10-08 10:03:00 |   4.0  (5ª inserção)")
    print("       2025-10-08 10:04:00 |   2.0  (3ª inserção)")
    print("       2025-10-08 10:05:00 |   0.0  (1ª inserção)")

if __name__ == '__main__':
    test_out_of_order()
