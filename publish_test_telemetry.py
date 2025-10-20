"""
Script para publicar telemetria de teste no MQTT broker.
Publica dados de temperatura, umidade, temp entrada/saída água.
"""

import paho.mqtt.client as mqtt
import json
import time
from datetime import datetime

# Configuração MQTT
MQTT_HOST = "localhost"
MQTT_PORT = 1883
MQTT_USERNAME = "traksense"
MQTT_PASSWORD = "traksense123"

# Device ID (mesmo usado nos testes anteriores)
DEVICE_ID = "GW-1760908415"

# Topic do EMQX que aciona o webhook
# Formato: tenants/{tenant_slug}/device_id (capturado pela rule do EMQX)
TOPIC = f"tenants/umc/{DEVICE_ID}"

def create_telemetry_payload():
    """
    Cria payload com 4 sensores:
    - Temperatura ambiente
    - Umidade
    - Temperatura entrada água
    - Temperatura saída água
    """
    timestamp = datetime.utcnow().isoformat() + 'Z'
    
    payload = {
        "device_id": DEVICE_ID,
        "timestamp": timestamp,
        "sensors": [
            {
                "sensor_id": "TEMP-AMB-001",
                "type": "temperature",
                "value": 23.5,  # Temperatura ambiente (°C)
                "unit": "°C",
                "labels": {
                    "location": "Sala de Máquinas",
                    "type": "temperature",
                    "description": "Temperatura Ambiente"
                }
            },
            {
                "sensor_id": "HUM-001",
                "type": "humidity",
                "value": 65.2,  # Umidade (%)
                "unit": "%",
                "labels": {
                    "location": "Sala de Máquinas",
                    "type": "humidity",
                    "description": "Umidade Relativa"
                }
            },
            {
                "sensor_id": "TEMP-WATER-IN-001",
                "type": "temperature",
                "value": 12.5,  # Temp entrada água (°C)
                "unit": "°C",
                "labels": {
                    "location": "Entrada Chiller",
                    "type": "temperature",
                    "description": "Temperatura Entrada Água"
                }
            },
            {
                "sensor_id": "TEMP-WATER-OUT-001",
                "type": "temperature",
                "value": 7.2,  # Temp saída água (°C)
                "unit": "°C",
                "labels": {
                    "location": "Saída Chiller",
                    "type": "temperature",
                    "description": "Temperatura Saída Água"
                }
            }
        ]
    }
    
    return payload

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Conectado ao broker MQTT")
    else:
        print(f"❌ Erro de conexão: {rc}")

def on_publish(client, userdata, mid):
    print(f"✅ Mensagem publicada (mid: {mid})")

def publish_telemetry():
    """
    Publica telemetria no broker MQTT.
    """
    print(f"🔌 Conectando ao broker MQTT em {MQTT_HOST}:{MQTT_PORT}...")
    
    # Criar cliente MQTT usando o DEVICE_ID como client_id
    # Isso garante que o EMQX capture o client_id correto
    client = mqtt.Client(client_id=DEVICE_ID)
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    client.on_connect = on_connect
    client.on_publish = on_publish
    
    try:
        # Conectar ao broker
        client.connect(MQTT_HOST, MQTT_PORT, 60)
        client.loop_start()
        
        # Aguardar conexão
        time.sleep(1)
        
        # Criar payload
        payload = create_telemetry_payload()
        payload_json = json.dumps(payload, indent=2)
        
        print(f"\n📦 Payload a ser publicado:")
        print(payload_json)
        
        print(f"\n📡 Publicando no tópico: {TOPIC}")
        
        # Publicar mensagem
        result = client.publish(
            topic=TOPIC,
            payload=payload_json,
            qos=1,
            retain=False
        )
        
        # Aguardar confirmação
        result.wait_for_publish(timeout=5)
        
        if result.is_published():
            print(f"\n✅ Telemetria publicada com sucesso!")
            print(f"📊 Sensores enviados:")
            print(f"   • Temperatura Ambiente: 23.5°C")
            print(f"   • Umidade: 65.2%")
            print(f"   • Temperatura Entrada Água: 12.5°C")
            print(f"   • Temperatura Saída Água: 7.2°C")
            print(f"\n⏰ Timestamp: {payload['timestamp']}")
            print(f"🆔 Device ID: {DEVICE_ID}")
            print(f"\n🔍 Para verificar:")
            print(f"   1. Abra: http://umc.localhost:5000/sensors")
            print(f"   2. Aguarde ~5 segundos (auto-refresh)")
            print(f"   3. Procure pelos sensores: TEMP-AMB-001, HUM-001, TEMP-WATER-IN-001, TEMP-WATER-OUT-001")
        else:
            print(f"\n❌ Erro ao publicar mensagem")
        
        # Aguardar um pouco antes de desconectar
        time.sleep(2)
        
        # Desconectar
        client.loop_stop()
        client.disconnect()
        
        print(f"\n✅ Desconectado do broker")
        
    except Exception as e:
        print(f"\n❌ Erro ao publicar telemetria: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 TrakSense - Publicação de Telemetria de Teste")
    print("=" * 60)
    publish_telemetry()
    print("=" * 60)
