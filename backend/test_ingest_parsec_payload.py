#!/usr/bin/env python3
"""
Teste de Ingest - Payload Vendor Parsec (v1)

Publica payload bruto de inversor Parsec via MQTT e verifica normalização.
"""

import paho.mqtt.client as mqtt
import json
import time
import sys
import os

def main():
    print("=" * 80)
    print("TESTE: Payload Vendor Parsec (v1)")
    print("=" * 80)
    
    # UUIDs fixos para testes
    TENANT_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    SITE_ID = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
    DEVICE_ID = "dddddddd-dddd-dddd-dddd-dddddddddddd"  # Device Parsec
    
    # Conectar ao broker MQTT
    print("\n📡 Conectando ao broker MQTT...")
    mqtt_host = os.getenv('MQTT_HOST', 'emqx')
    
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
    try:
        client.connect(mqtt_host, 1883, keepalive=60)
        print(f"✅ Conectado ao MQTT em {mqtt_host}:1883")
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        return 1
    
    # Payload bruto do inversor Parsec
    # DI1 = 1 (RUN), DI2 = 0 (OK, sem falha)
    payload = {
        'di1': 1,        # Status: RUN
        'di2': 0,        # Fault: OK (sem falha)
        'rssi': -68,     # Sinal WiFi
        'fw': '1.2.3',   # Firmware version
        'ts': '2025-10-08T04:15:00Z'
    }
    
    topic = f'traksense/{TENANT_ID}/{SITE_ID}/{DEVICE_ID}/telem'
    
    print(f"\n📤 Publicando payload Parsec em: {topic}")
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
    
    print("=" * 80)
    print("✅ Teste concluído!")
    print("=" * 80)
    print("\nPróximos passos:")
    print("1. Verificar logs do ingest:")
    print("   docker compose logs ingest | grep -i 'parsec\\|normalize\\|FLUSH'")
    print("\n2. Verificar dados no banco:")
    print("   docker compose exec db psql -U postgres -d traksense -c \\")
    print(f"   \"SELECT point_id, v_text, v_bool, v_num, unit FROM public.ts_measure")
    print("    WHERE ts >= NOW() - INTERVAL '5 minutes'")
    print(f"    AND device_id = '{DEVICE_ID}'")
    print("    ORDER BY point_id;\"")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
