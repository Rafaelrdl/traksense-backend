"""
Script de teste: MQTT Subscribe NÃO Autorizado (Wildcards)
===========================================================

Valida que o device NÃO consegue assinar wildcards fora do seu prefixo.

Testa assinaturas em:
  - traksense/# (wildcard multi-level - acesso total)
  - traksense/+/+/+/telem (wildcard single-level)
  - traksense/other-tenant/other-site/other-device/cmd (tópico de outro device)

Expectativa: 
  - Todas as assinaturas devem retornar SUBACK com QoS = 0x80 (falha)
  - Logs do EMQX devem registrar tentativas negadas
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

# Tópicos com wildcards (não autorizados)
unauthorized_topics = [
    ("traksense/#", "wildcard multi-level (acesso total)"),
    ("traksense/+/+/+/telem", "wildcard single-level"),
    ("traksense/other-tenant/other-site/other-device/cmd", "tópico de outro device"),
]

print(f"🔌 Conectando no EMQX: {MQTT_HOST}:{MQTT_PORT}")
print(f"   ClientID: {MQTT_CLIENT_ID}")
print(f"   Username: {MQTT_USERNAME}")

results = []
current_index = 0

# Callback de conexão
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Conectado com sucesso!\n")
    else:
        print(f"❌ Falha na conexão: rc={rc}")
        sys.exit(1)

# Callback de assinatura
def on_subscribe(client, userdata, mid, granted_qos):
    global current_index
    if current_index < len(unauthorized_topics):
        topic, description = unauthorized_topics[current_index - 1]
        qos = granted_qos[0]
        
        if qos == 0x80:  # 0x80 = falha
            print(f"✅ ACL funcionou! Assinatura negada: {description}")
            print(f"   Topic: {topic}, QoS: 0x80")
            results.append(True)
        else:
            print(f"❌ ACL NÃO funcionou! Assinatura permitida: {description}")
            print(f"   Topic: {topic}, QoS: {qos}")
            results.append(False)

# Criar cliente
client = mqtt.Client(client_id=MQTT_CLIENT_ID, protocol=mqtt.MQTTv311)
client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
client.on_connect = on_connect
client.on_subscribe = on_subscribe

# Conectar
try:
    client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
    client.loop_start()
except Exception as e:
    print(f"❌ Erro ao conectar: {e}")
    sys.exit(1)

time.sleep(2)

# Tentar assinar tópicos NÃO autorizados
for topic, description in unauthorized_topics:
    current_index += 1
    print(f"📥 Tentando assinar: {description}")
    print(f"   Topic: {topic}")
    client.subscribe(topic, qos=1)
    time.sleep(1.5)

time.sleep(2)

client.loop_stop()
client.disconnect()

print(f"\n✅ Teste de assinaturas não autorizadas concluído!")
print(f"   Total de testes: {len(unauthorized_topics)}")
print(f"   Negações bem-sucedidas: {sum(results)}/{len(unauthorized_topics)}")

if all(results):
    print("\n✅ PASSO 8: PASSOU - ACL funcionou! Todas as assinaturas com wildcards foram negadas")
    sys.exit(0)
else:
    print("\n❌ PASSO 8: FALHOU - ACL NÃO funcionou completamente")
    print("   ⚠️ Algumas assinaturas foram permitidas quando deveriam ser negadas")
    sys.exit(1)
