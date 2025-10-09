#!/usr/bin/env python3
"""
Script para testar publicação MQTT de payloads JE02.

Envia mensagens de teste para o broker EMQX e valida conectividade.
"""
import paho.mqtt.client as mqtt
import time
import json

# Configuração do broker
BROKER = "localhost"
PORT = 1883
TOPIC = "traksense/demo/plant-01/INV-01/telem"

# Payload JE02 DATA de teste (formato correto do protocolo)
import time as time_module
payload_je02 = {
    "DATA": {
        "TS": int(time_module.time()),  # Timestamp Unix atual
        "INPUT1": 1,   # RUN
        "INPUT2": 0,   # Sem FAULT
        "VAR0": 2453,  # 245.3°C * 10
        "VAR1": 127,   # 12.7% * 10
        "WRSSI": -67,  # -67 dBm
        "RELE": 1,     # Ligado
        "CNTSERR": 2,  # 2 erros
        "UPTIME": 3600 # 1 hora
    }
}

def on_connect(client, userdata, flags, rc):
    """Callback de conexão"""
    if rc == 0:
        print(f"✅ Conectado ao broker {BROKER}:{PORT}")
    else:
        print(f"❌ Falha na conexão: código {rc}")

def on_publish(client, userdata, mid):
    """Callback de publicação"""
    print(f"  ✅ Mensagem {mid} publicada com sucesso")

# Criar cliente (v2.0 API)
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, "test-publisher")
client.on_connect = on_connect
client.on_publish = on_publish

try:
    print(f"Conectando ao broker {BROKER}:{PORT}...")
    client.connect(BROKER, PORT, keepalive=60)
    client.loop_start()
    
    time.sleep(1)  # Aguardar conexão
    
    # Enviar 6 mensagens
    print(f"\nEnviando 6 mensagens para tópico: {TOPIC}")
    for i in range(6):
        # Atualizar timestamp e variar valores para simular medições diferentes
        payload_je02["DATA"]["TS"] = int(time_module.time())
        payload_je02["DATA"]["VAR0"] = 2453 + i * 5  # 245.3°C + 0.5°C por msg
        payload_je02["DATA"]["VAR1"] = 127 + i      # 12.7% + 0.1% por msg
        
        payload_str = json.dumps(payload_je02)
        result = client.publish(TOPIC, payload_str, qos=1)
        print(f"[{i+1}/6] MID={result.mid} - Aguardando confirmação...")
        time.sleep(0.5)
    
    time.sleep(2)  # Aguardar confirmação de todas as mensagens
    
    print("\n✅ Teste concluído!")
    
except Exception as e:
    print(f"❌ Erro: {e}")
    
finally:
    client.loop_stop()
    client.disconnect()
