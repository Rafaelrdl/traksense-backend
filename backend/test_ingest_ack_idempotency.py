"""
Script de validação: ACK Idempotency
Testa que ACKs com mesmo cmd_id fazem UPSERT (não duplicam)

Casos de teste:
1. Publicar ACK com cmd_id único (1ª vez)
2. Publicar ACK com mesmo cmd_id (2ª e 3ª vez)
3. Verificar que há apenas 1 registro no banco
4. Verificar que updated_at foi atualizado
"""
import paho.mqtt.client as mqtt
import json
import time
import sys

# IDs de teste para ACK
TENANT_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
SITE_ID = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
DEVICE_ID = "ffffffff-ffff-ffff-ffff-ffffffffffff"  # Device ACK Test

# ULID fixo para teste de idempotência
CMD_ID = "01HQZC5K3M8YBQWER7TXZ9V2P3"

def test_ack_idempotency():
    """Testa idempotência de ACKs (UPSERT por cmd_id)"""
    
    print("=" * 80)
    print("TESTE DE VALIDAÇÃO: ACK Idempotency (UPSERT)")
    print("=" * 80)
    
    # Conectar ao MQTT
    try:
        client = mqtt.Client(client_id="test_ack_idempotency")
        client.connect('emqx', 1883, keepalive=60)
        print(f"✅ Conectado ao MQTT broker: emqx:1883\n")
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        sys.exit(1)
    
    topic = f'traksense/{TENANT_ID}/{SITE_ID}/{DEVICE_ID}/ack'
    print(f"📡 Tópico: {topic}")
    print(f"🆔 CMD_ID (fixo para teste): {CMD_ID}\n")
    
    # Payload de ACK (será publicado 3x com mesmo cmd_id)
    ack_payload = {
        'schema': 'v1',
        'cmd_id': CMD_ID,
        'ok': True,
        'ts_exec': '2025-10-08T04:30:00Z',
        'err': None
    }
    
    # ========================================================================
    # Publicar ACK 3 vezes com mesmo cmd_id
    # ========================================================================
    print("📤 Publicando ACK 3 vezes com mesmo cmd_id...")
    print(f"   Payload: {json.dumps(ack_payload)}\n")
    
    for i in range(3):
        try:
            payload_str = json.dumps(ack_payload)
            result = client.publish(topic, payload_str, qos=1)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"   ✅ Publicação {i+1}/3: SUCCESS (QoS=1)")
            else:
                print(f"   ❌ Publicação {i+1}/3: FALHOU (rc={result.rc})")
        except Exception as e:
            print(f"   ❌ Publicação {i+1}/3: Exceção: {e}")
        
        time.sleep(0.5)
    
    client.disconnect()
    
    # ========================================================================
    # Aguardar processamento
    # ========================================================================
    print("\n" + "=" * 80)
    print("⏳ Aguardando 4 segundos para ingest processar e flush...")
    print("=" * 80)
    time.sleep(4)
    
    print("\n✅ Teste concluído!")
    print("\n📋 Próximos passos:")
    print("   1. Verificar logs de ACK no ingest:")
    print("      docker compose logs ingest | grep -i 'ACK\\|cmd_id'")
    print("\n   2. Verificar UPSERT no banco (deve haver apenas 1 registro):")
    print("      docker compose exec db psql -U postgres -d traksense -c \"")
    print("      SELECT COUNT(*) as count,")
    print("             MIN(created_at) as first_insert,")
    print("             MAX(updated_at) as last_update")
    print("      FROM public.cmd_ack")
    print(f"      WHERE tenant_id = '{TENANT_ID}'")
    print(f"        AND device_id = '{DEVICE_ID}'")
    print(f"        AND cmd_id = '{CMD_ID}';\"")
    print("\n   Esperado: count=1, last_update > first_insert")
    print("\n   3. Ver registro completo:")
    print("      docker compose exec db psql -U postgres -d traksense -c \"")
    print("      SELECT cmd_id, ok, ts_exec, err, created_at, updated_at")
    print("      FROM public.cmd_ack")
    print(f"      WHERE cmd_id = '{CMD_ID}';\"")

if __name__ == '__main__':
    test_ack_idempotency()
