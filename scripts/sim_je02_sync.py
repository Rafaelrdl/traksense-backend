#!/usr/bin/env python3
"""
Simulador JE02 simples para Windows (síncrono com paho-mqtt)
"""
import json
import time
import random
from datetime import datetime
from paho.mqtt import client as mqtt_client

# Configuração
CONFIG = {
    "mqtt": {
        "host": "localhost",
        "port": 1883,
        "username": "t:demo:d:cfe0a644-4f3b-48f0-b514-6b513607182c",
        "password": "Rw7TXjkFY3GpN8mQ2Hcs"
    },
    "device": {
        "name": "INV-01",
        "topic_base": "traksense/demo/plant-01/inv-01"
    }
}

# Estado do simulador
state = {
    "uptime": 0,
    "input1": 1,  # RUN
    "input2": 0,  # No FAULT
    "rele": 1,
    "cntserr": 0,
    "fault_counter": 0,
    "in_fault": False,
}

def generate_data_payload():
    """Gera payload DATA do protocolo JE02"""
    state["uptime"] += 5
    
    # INPUT1: 80% RUN (1), 20% STOP (0)
    if random.random() > 0.8:
        state["input1"] = 0
    else:
        state["input1"] = 1
    
    # INPUT2: 2-5% chance de FAULT por 30-60s
    if not state["in_fault"]:
        if random.random() < 0.03:  # 3% de chance
            state["in_fault"] = True
            state["input2"] = 1
            state["fault_counter"] = random.randint(6, 12)  # 30-60s em intervalos de 5s
    else:
        state["fault_counter"] -= 1
        if state["fault_counter"] <= 0:
            state["in_fault"] = False
            state["input2"] = 0
    
    # WRSSI: -55 a -75 dBm
    wrssi = random.randint(-75, -55)
    
    # VAR0: temperatura 21-26°C (raw: 210-260)
    var0 = random.randint(210, 260)
    
    # VAR1: umidade 45-65% (raw: 450-650)
    var1 = random.randint(450, 650)
    
    # CNTSERR: incrementa ocasionalmente
    if random.random() < 0.05:
        state["cntserr"] += 1
    
    payload = {
        "schema": "je02/data/1.0",
        "deviceId": "inv-01",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "data": {
            "input1": state["input1"],
            "input2": state["input2"],
            "wrssi": wrssi,
            "var0": var0,
            "var1": var1,
            "rele": state["rele"],
            "cntserr": state["cntserr"],
            "uptime": state["uptime"]
        }
    }
    
    return payload

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"✅ Conectado ao MQTT broker")
    else:
        print(f"❌ Falha na conexão. Código: {rc}")

def main():
    # Criar cliente MQTT
    client_id = f'sim-je02-{int(time.time())}'
    client = mqtt_client.Client(callback_api_version=mqtt_client.CallbackAPIVersion.VERSION1, client_id=client_id)
    client.username_pw_set(CONFIG["mqtt"]["username"], CONFIG["mqtt"]["password"])
    client.on_connect = on_connect
    
    # Conectar
    print(f"🔌 Conectando a {CONFIG['mqtt']['host']}:{CONFIG['mqtt']['port']}...")
    try:
        client.connect(CONFIG["mqtt"]["host"], CONFIG["mqtt"]["port"])
        client.loop_start()
        time.sleep(2)  # Aguardar conexão
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        return
    
    # Enviar mensagens a cada 5 segundos por 30 segundos (6 mensagens)
    topic = f"{CONFIG['device']['topic_base']}/telem"
    print(f"\n📡 Enviando telemetria para: {topic}")
    print(f"   Device: {CONFIG['device']['name']}")
    print(f"   Período: 5s | Duração: 30s (6 mensagens)\n")
    
    for i in range(6):
        payload = generate_data_payload()
        payload_str = json.dumps(payload)
        
        result = client.publish(topic, payload_str, qos=1)
        
        if result.rc == mqtt_client.MQTT_ERR_SUCCESS:
            print(f"✅ [{i+1}/6] Enviado - INPUT1={payload['data']['input1']} INPUT2={payload['data']['input2']} "
                  f"VAR0={payload['data']['var0']/10:.1f}°C VAR1={payload['data']['var1']/10:.1f}% UPTIME={payload['data']['uptime']}s")
        else:
            print(f"❌ [{i+1}/6] Falha ao enviar (rc={result.rc})")
        
        if i < 5:  # Não esperar depois da última mensagem
            time.sleep(5)
    
    print(f"\n✅ Simulação concluída! 6 mensagens enviadas.")
    client.loop_stop()
    client.disconnect()

if __name__ == "__main__":
    main()
