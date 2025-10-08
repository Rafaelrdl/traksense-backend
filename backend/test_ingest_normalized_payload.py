#!/usr/bin/env python3
"""
Teste de Ingest - Payload Normalizado (Schema v1)

Publica payload normalizado (schema v1) via MQTT e verifica persistência.
"""

import paho.mqtt.client as mqtt
import json
import time
import sys

def main():
    print("=" * 80)
    print("TESTE: Payload Normalizado (Schema v1)")
    print("=" * 80)
    
    # UUIDs fixos para testes (simulando tenant/site/device reais)
    TENANT_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    SITE_ID = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
    DEVICE_ID = "cccccccc-cccc-cccc-cccc-cccccccccccc"
    
    # Conectar ao broker MQTT (detectar se está em container ou host)
    print("\n📡 Conectando ao broker MQTT...")
    import os
    mqtt_host = os.getenv('MQTT_HOST', 'emqx')  # 'emqx' dentro do Docker, 'localhost' fora
    
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
    try:
        client.connect(mqtt_host, 1883, keepalive=60)
        print(f"✅ Conectado ao MQTT em {mqtt_host}:1883")
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        return 1
    
    # Payload de teste (schema v1 normalizado)
    payload = {
        'schema': 'v1',
        'ts': '2025-10-08T03:10:00Z',
        'points': [
            {'name': 'temp_agua', 't': 'float', 'v': 7.3, 'u': '°C'},
            {'name': 'compressor_1_on', 't': 'bool', 'v': True},
            {'name': 'status', 't': 'enum', 'v': 'RUN', 'u': None}
        ],
        'meta': {'fw': '1.2.3', 'src': 'test_validation'}
    }
    
    topic = f'traksense/{TENANT_ID}/{SITE_ID}/{DEVICE_ID}/telem'
    
    print(f"\n📤 Publicando payload em: {topic}")
    print(f"   Payload: {json.dumps(payload, indent=2)}")
    
    # Publicar mensagem
    result = client.publish(topic, json.dumps(payload), qos=1)
    
    if result.rc == mqtt.MQTT_ERR_SUCCESS:
        print("✅ Mensagem publicada com sucesso")
    else:
        print(f"❌ Erro ao publicar: {result.rc}")
        return 1
    
    client.disconnect()
    
    print("\n⏳ Aguardando 3 segundos para flush...")
    time.sleep(3)
    
    print("\n" + "=" * 80)
    print("✅ Teste concluído!")
    print("=" * 80)
    print("\nPróximos passos:")
    print("1. Verificar logs do ingest:")
    print("   docker compose logs ingest | grep -i 'FLUSH\\|inseridos'")
    print("\n2. Verificar dados no banco:")
    print("   docker compose exec db psql -U postgres -d traksense -c \\")
    print(f"   \"SELECT COUNT(*), array_agg(DISTINCT point_id) as points")
    print("    FROM public.ts_measure")
    print("    WHERE ts >= NOW() - INTERVAL '5 minutes'")
    print(f"    AND device_id = '{DEVICE_ID}';\"")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
