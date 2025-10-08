"""
Script de teste: MQTT Publish Autorizado
==========================================

Valida que o device consegue publicar nos 5 tópicos permitidos:
  - traksense/{tenant}/{site}/{device}/state
  - traksense/{tenant}/{site}/{device}/telem
  - traksense/{tenant}/{site}/{device}/event
  - traksense/{tenant}/{site}/{device}/alarm
  - traksense/{tenant}/{site}/{device}/ack

Expectativa: Todas as publicações devem ser bem-sucedidas sem desconectar o cliente.
"""

import paho.mqtt.client as mqtt
import time
import os
import sys

# Credenciais do device provisionado (obtidas do comando provision_emqx)
MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_CLIENT_ID = os.getenv("MQTT_CLIENT_ID", "ts-test_alp-a1b2c3d4-1f")
MQTT_USERNAME = os.getenv("MQTT_USERNAME", "t:test_alpha:d:a1b2c3d4-e5f6-7890-1234-567890abcdef")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "bGQRHSnXxA_0oRM5MC-wGoNSFDM")
MQTT_TOPIC_BASE = os.getenv("MQTT_TOPIC_BASE", "traksense/test_alpha/factory-sp/a1b2c3d4-e5f6-7890-1234-567890abcdef")

print(f"🔌 Conectando no EMQX: {MQTT_HOST}:{MQTT_PORT}")
print(f"   ClientID: {MQTT_CLIENT_ID}")
print(f"   Username: {MQTT_USERNAME}")
print(f"   Topic Base: {MQTT_TOPIC_BASE}")

# Contadores
published_count = 0
failed_count = 0

# Callback de conexão
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Conectado com sucesso!")
    else:
        print(f"❌ Falha na conexão: rc={rc}")
        sys.exit(1)

# Callback de publicação
def on_publish(client, userdata, mid):
    global published_count
    published_count += 1
    print(f"✅ Mensagem publicada: mid={mid}")

# Callback de desconexão
def on_disconnect(client, userdata, rc):
    if rc != 0:
        print(f"❌ Desconectado inesperadamente: rc={rc}")
        sys.exit(1)

# Criar cliente
client = mqtt.Client(client_id=MQTT_CLIENT_ID, protocol=mqtt.MQTTv311)
client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
client.on_connect = on_connect
client.on_publish = on_publish
client.on_disconnect = on_disconnect

# Conectar
try:
    client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
    client.loop_start()
except Exception as e:
    print(f"❌ Erro ao conectar: {e}")
    sys.exit(1)

time.sleep(2)  # Aguardar conexão

# Testar publicação nos tópicos permitidos
topics_to_test = [
    f"{MQTT_TOPIC_BASE}/state",
    f"{MQTT_TOPIC_BASE}/telem",
    f"{MQTT_TOPIC_BASE}/event",
    f"{MQTT_TOPIC_BASE}/alarm",
    f"{MQTT_TOPIC_BASE}/ack",
]

for topic in topics_to_test:
    payload = f'{{"test": "authorized", "topic": "{topic}", "ts": "{time.time()}"}}'
    print(f"📤 Publicando em: {topic}")
    result = client.publish(topic, payload, qos=1)
    
    if result.rc != mqtt.MQTT_ERR_SUCCESS:
        print(f"❌ Falha ao publicar em {topic}: rc={result.rc}")
        failed_count += 1
    
    time.sleep(0.5)

time.sleep(2)  # Aguardar callbacks
client.loop_stop()
client.disconnect()

print(f"\n✅ Teste de publicação autorizada concluído!")
print(f"   Publicações bem-sucedidas: {published_count}/5")
print(f"   Falhas: {failed_count}")

if published_count == 5 and failed_count == 0:
    print("\n✅ PASSO 5: PASSOU - Todas as publicações autorizadas foram bem-sucedidas")
    sys.exit(0)
else:
    print(f"\n❌ PASSO 5: FALHOU - Esperado 5 publicações, obteve {published_count}")
    sys.exit(1)
