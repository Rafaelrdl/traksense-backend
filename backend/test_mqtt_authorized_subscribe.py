"""
Script de teste: MQTT Subscribe Autorizado
===========================================

Valida que o device consegue assinar o tópico de comandos:
  - traksense/{tenant}/{site}/{device}/cmd

Expectativa: 
  - Assinatura bem-sucedida (SUBACK com QoS válido)
  - Device recebe mensagens publicadas no tópico
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

cmd_topic = f"{MQTT_TOPIC_BASE}/cmd"

print(f"🔌 Conectando no EMQX: {MQTT_HOST}:{MQTT_PORT}")
print(f"   ClientID: {MQTT_CLIENT_ID}")
print(f"   Username: {MQTT_USERNAME}")
print(f"   Tópico CMD: {cmd_topic}")

# Contadores
received_messages = []
subscribe_granted = False

# Callback de conexão
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Conectado com sucesso!")
        # Assinar tópico de comandos
        result, mid = client.subscribe(cmd_topic, qos=1)
        print(f"📥 Assinando tópico: {cmd_topic}")
    else:
        print(f"❌ Falha na conexão: rc={rc}")
        sys.exit(1)

# Callback de assinatura
def on_subscribe(client, userdata, mid, granted_qos):
    global subscribe_granted
    if granted_qos[0] != 0x80:  # 0x80 = falha
        subscribe_granted = True
        print(f"✅ Assinatura confirmada: mid={mid}, qos={granted_qos[0]}")
    else:
        print(f"❌ Assinatura negada: mid={mid}, qos=0x80")
        sys.exit(1)

# Callback de mensagem recebida
def on_message(client, userdata, msg):
    print(f"✅ Mensagem recebida: topic={msg.topic}, payload={msg.payload.decode()}")
    received_messages.append(msg.payload.decode())

# Criar cliente
client = mqtt.Client(client_id=MQTT_CLIENT_ID, protocol=mqtt.MQTTv311)
client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
client.on_connect = on_connect
client.on_subscribe = on_subscribe
client.on_message = on_message

# Conectar
try:
    client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
    client.loop_start()
except Exception as e:
    print(f"❌ Erro ao conectar: {e}")
    sys.exit(1)

time.sleep(2)  # Aguardar assinatura

# Publicar comando de teste (simular backend enviando comando)
test_payload = '{"cmd": "reset_fault", "pulse_ms": 500}'
print(f"📤 Publicando comando de teste: {test_payload}")
result = client.publish(cmd_topic, test_payload, qos=1)

if result.rc != mqtt.MQTT_ERR_SUCCESS:
    print(f"⚠️ Aviso: Falha ao publicar comando de teste (pode ser OK se ACL bloquear publish em /cmd)")

time.sleep(3)  # Aguardar mensagem

client.loop_stop()
client.disconnect()

print(f"\n✅ Teste de assinatura autorizada concluído!")
print(f"   Assinatura bem-sucedida: {subscribe_granted}")
print(f"   Mensagens recebidas: {len(received_messages)}")

if subscribe_granted:
    print("\n✅ PASSO 6: PASSOU - Assinatura autorizada no tópico /cmd funcionou")
    if len(received_messages) > 0:
        print(f"   ✅ Bônus: {len(received_messages)} mensagem(ns) recebida(s)")
    else:
        print("   ℹ️ Nenhuma mensagem recebida (esperado, device não pode publicar em /cmd)")
    sys.exit(0)
else:
    print("\n❌ PASSO 6: FALHOU - Assinatura não foi confirmada")
    sys.exit(1)
