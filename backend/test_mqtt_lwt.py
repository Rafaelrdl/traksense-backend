"""
Script de teste: MQTT Last Will Testament (LWT)
================================================

Valida que o device pode configurar LWT e que é publicado automaticamente:
  - LWT no tópico: traksense/{tenant}/{site}/{device}/state
  - Retain: true (mensagem persiste no broker)
  - QoS: 1

Expectativa: 
  - LWT configurado com sucesso antes da conexão
  - Ao desconectar abruptamente, EMQX publica LWT automaticamente
  - Mensagem LWT fica retained (pode ser consultada depois)

NOTA: Este script requer um subscriber separado rodando em outro terminal
      para observar a mensagem LWT sendo publicada.
"""

import paho.mqtt.client as mqtt
import time
import os
import sys

# Credenciais do device provisionado
MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_CLIENT_ID = os.getenv("MQTT_CLIENT_ID", "ts-test_alp-a1b2c3d4-1f")
MQTT_USERNAME = os.getenv("MQTT_USERNAME", "t:test_alpha:d:a1b2c3d4-e5f6-7890-1234-567890abcdef")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "bGQRHSnXxA_0oRM5MC-wGoNSFDM")
MQTT_TOPIC_BASE = os.getenv("MQTT_TOPIC_BASE", "traksense/test_alpha/factory-sp/a1b2c3d4-e5f6-7890-1234-567890abcdef")

state_topic = f"{MQTT_TOPIC_BASE}/state"
lwt_payload = '{"online": false, "reason": "lwt_triggered", "ts": "' + str(time.time()) + '"}'

print(f"🔌 Configurando cliente MQTT com LWT")
print(f"   Host: {MQTT_HOST}:{MQTT_PORT}")
print(f"   ClientID: {MQTT_CLIENT_ID}")
print(f"   Username: {MQTT_USERNAME}")
print(f"   LWT Topic: {state_topic}")
print(f"   LWT Payload: {lwt_payload}")

# Callback de conexão
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("\n✅ Conectado com sucesso!")
        print("   LWT configurado: topic={}, retain=true, qos=1".format(state_topic))
    else:
        print(f"\n❌ Falha na conexão: rc={rc}")
        sys.exit(1)

# Criar cliente com LWT
client = mqtt.Client(client_id=MQTT_CLIENT_ID, protocol=mqtt.MQTTv311)
client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
client.on_connect = on_connect

# IMPORTANTE: Configurar LWT ANTES de conectar!
print("\n📋 Configurando LWT antes da conexão...")
client.will_set(state_topic, lwt_payload, qos=1, retain=True)
print("✅ LWT configurado (será publicado ao desconectar abruptamente)")

# Conectar
try:
    client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
    client.loop_start()
except Exception as e:
    print(f"❌ Erro ao conectar: {e}")
    sys.exit(1)

time.sleep(2)

# Publicar estado "online" primeiro (para comparação)
online_payload = '{"online": true, "ts": "' + str(time.time()) + '"}'
print(f"\n📤 Publicando estado online: {online_payload}")
client.publish(state_topic, online_payload, qos=1, retain=True)

time.sleep(2)

# Simular desconexão abrupta (sem DISCONNECT packet)
print("\n⏳ Aguardando 3 segundos antes de desconectar abruptamente...")
time.sleep(3)

print("💀 Simulando desconexão abrupta (sem enviar DISCONNECT)...")
print("   O EMQX deve publicar o LWT automaticamente")

# Não chamar client.disconnect() - isso envia um DISCONNECT packet limpo
# Apenas parar o loop e finalizar (simula crash/perda de conexão)
client.loop_stop()

print("\n✅ PASSO 9: Script finalizado")
print("\nℹ️  Para validar o LWT:")
print("1. Execute um subscriber em outro terminal:")
print(f"   docker compose exec emqx mosquitto_sub -h localhost -p 1883 \\")
print(f"       -u \"{MQTT_USERNAME}\" -P \"{MQTT_PASSWORD}\" \\")
print(f"       -t \"{state_topic}\" -v")
print("\n2. Após alguns segundos, você deve ver a mensagem LWT:")
print(f"   {state_topic} {lwt_payload}")
print("\n3. A mensagem deve persistir (retained) - conecte novamente e verá a mesma mensagem")

print("\n✅ LWT configurado corretamente (validação manual necessária)")
sys.exit(0)
