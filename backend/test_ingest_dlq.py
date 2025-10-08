"""
Script de validação: Dead Letter Queue (DLQ)
Testa captura de payloads inválidos na tabela ingest_errors

Casos de teste:
1. JSON inválido (sintaxe)
2. Payload sem campo obrigatório 'ts'
3. Payload com tipo errado
"""
import paho.mqtt.client as mqtt
import json
import time
import sys

# IDs de teste para DLQ
TENANT_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
SITE_ID = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
DEVICE_ID = "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee"  # Device DLQ

def test_dlq():
    """Testa captura de erros na DLQ"""
    
    print("=" * 80)
    print("TESTE DE VALIDAÇÃO: Dead Letter Queue (DLQ)")
    print("=" * 80)
    
    # Conectar ao MQTT
    try:
        client = mqtt.Client(client_id="test_dlq_validator")
        client.connect('emqx', 1883, keepalive=60)
        print(f"✅ Conectado ao MQTT broker: emqx:1883\n")
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        sys.exit(1)
    
    topic = f'traksense/{TENANT_ID}/{SITE_ID}/{DEVICE_ID}/telem'
    print(f"📡 Tópico: {topic}\n")
    
    # ========================================================================
    # Teste 1: JSON inválido (sintaxe)
    # ========================================================================
    print("📤 Teste 1: JSON inválido (sintaxe quebrada)")
    invalid_json = '{invalid json syntax, missing quotes}'
    try:
        result = client.publish(topic, invalid_json, qos=1)
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            print(f"   Payload: {invalid_json}")
            print(f"   Status: Publicado (QoS=1)")
            print(f"   Esperado: DLQ deve capturar erro de parse JSON\n")
        else:
            print(f"   ❌ Erro ao publicar: {result.rc}\n")
    except Exception as e:
        print(f"   ❌ Exceção: {e}\n")
    
    time.sleep(0.5)
    
    # ========================================================================
    # Teste 2: Payload sem campo obrigatório 'ts'
    # ========================================================================
    print("📤 Teste 2: Payload sem campo obrigatório 'ts'")
    payload_no_ts = {
        'schema': 'v1',
        'points': [{'name': 'temp', 't': 'float', 'v': 25.0}],
        'meta': {}
        # 'ts' FALTANDO!
    }
    try:
        payload_str = json.dumps(payload_no_ts)
        result = client.publish(topic, payload_str, qos=1)
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            print(f"   Payload: {payload_str}")
            print(f"   Status: Publicado (QoS=1)")
            print(f"   Esperado: DLQ deve capturar ValidationError (campo 'ts' ausente)\n")
        else:
            print(f"   ❌ Erro ao publicar: {result.rc}\n")
    except Exception as e:
        print(f"   ❌ Exceção: {e}\n")
    
    time.sleep(0.5)
    
    # ========================================================================
    # Teste 3: Payload com tipo errado
    # ========================================================================
    print("📤 Teste 3: Payload com tipos errados")
    payload_wrong_type = {
        'schema': 'v1',
        'ts': 'not-a-valid-timestamp',  # String inválida
        'points': 'not-a-list',          # Deveria ser lista
        'meta': {}
    }
    try:
        payload_str = json.dumps(payload_wrong_type)
        result = client.publish(topic, payload_str, qos=1)
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            print(f"   Payload: {payload_str}")
            print(f"   Status: Publicado (QoS=1)")
            print(f"   Esperado: DLQ deve capturar ValidationError (tipo inválido)\n")
        else:
            print(f"   ❌ Erro ao publicar: {result.rc}\n")
    except Exception as e:
        print(f"   ❌ Exceção: {e}\n")
    
    client.disconnect()
    
    # ========================================================================
    # Aguardar processamento
    # ========================================================================
    print("=" * 80)
    print("⏳ Aguardando 4 segundos para ingest processar e flush...")
    print("=" * 80)
    time.sleep(4)
    
    print("\n✅ Teste concluído!")
    print("\n📋 Próximos passos:")
    print("   1. Verificar logs de erro no ingest:")
    print("      docker compose logs ingest | grep -i 'DLQ\\|erro\\|error'")
    print("\n   2. Verificar DLQ no banco de dados:")
    print("      docker compose exec db psql -U postgres -d traksense -c \"")
    print("      SELECT tenant_id, LEFT(payload, 60) as payload_preview, reason")
    print("      FROM public.ingest_errors")
    print(f"      WHERE device_id = '{DEVICE_ID}'")
    print("      ORDER BY ts DESC LIMIT 5;\"")
    print("\n   3. Verificar métrica de erros:")
    print("      curl -s http://localhost:9100/metrics | grep ingest_errors_total")

if __name__ == '__main__':
    test_dlq()
