"""
Script para publicar dados de teste no formato Khomp SenML via MQTT.

Este script simula o envio de dados de um gateway LoRaWAN Khomp
para testar o sistema de parsers.
"""
import paho.mqtt.client as mqtt
import json
import time
from datetime import datetime


def create_khomp_senml_payload_temp_humidity():
    """Cria um payload SenML com dados de temperatura e umidade."""
    return [
        {
            "bn": "4b686f6d70107115",  # MAC do dispositivo
            "bt": int(time.time())      # Timestamp atual em segundos
        },
        {
            "n": "model",
            "vs": "nit20l"
        },
        {
            "n": "rssi",
            "u": "dBW",
            "v": -61
        },
        {
            "n": "A",          # Sensor A - Temperatura
            "u": "Cel",
            "v": 23.35
        },
        {
            "n": "A",          # Sensor A - Umidade
            "u": "%RH",
            "v": 64.0
        },
        {
            "n": "283286b20a000036",  # Sensor externo DS18B20
            "u": "Cel",
            "v": 30.75
        },
        {
            "n": "gateway",
            "vs": "000D6FFFFE642E70"
        }
    ]


def create_khomp_senml_payload_binary_counter():
    """Cria um payload SenML com contador binário."""
    return [
        {
            "bn": "4b686f6d70108826",
            "bt": int(time.time())
        },
        {
            "n": "model",
            "vs": "nit20l"
        },
        {
            "n": "C1",
            "vb": True  # Contato fechado
        },
        {
            "n": "C1",
            "u": "count",
            "v": 3  # Contador de transições
        },
        {
            "n": "gateway",
            "vs": "000D6FFFFE642E70"
        }
    ]


def on_connect(client, userdata, flags, rc):
    """Callback quando conecta ao broker."""
    if rc == 0:
        print("✅ Conectado ao broker MQTT")
    else:
        print(f"❌ Falha na conexão: {rc}")


def on_publish(client, userdata, mid):
    """Callback quando uma mensagem é publicada."""
    print(f"✅ Mensagem publicada (ID: {mid})")


def publish_test_data(broker_host="localhost", broker_port=1883, tenant="umc"):
    """
    Publica dados de teste no formato Khomp SenML.
    
    Args:
        broker_host: Host do broker MQTT
        broker_port: Porta do broker MQTT
        tenant: Slug do tenant
    """
    print("=" * 80)
    print("🚀 PUBLICANDO DADOS DE TESTE - KHOMP SENML")
    print("=" * 80)
    print(f"Broker: {broker_host}:{broker_port}")
    print(f"Tenant: {tenant}")
    print()
    
    # Criar cliente MQTT
    client = mqtt.Client(client_id="test-khomp-publisher")
    client.on_connect = on_connect
    client.on_publish = on_publish
    
    try:
        # Conectar ao broker
        print(f"🔌 Conectando ao broker {broker_host}:{broker_port}...")
        client.connect(broker_host, broker_port, 60)
        client.loop_start()
        
        time.sleep(1)  # Aguardar conexão
        
        # Publicar dados de temperatura e umidade
        topic1 = f"tenants/{tenant}/gateways/khomp/device-001"
        payload1 = create_khomp_senml_payload_temp_humidity()
        
        print(f"\n📤 Publicando no tópico: {topic1}")
        print(f"📦 Payload (temperatura e umidade):")
        print(json.dumps(payload1, indent=2))
        
        result1 = client.publish(topic1, json.dumps(payload1), qos=1)
        result1.wait_for_publish()
        
        time.sleep(2)
        
        # Publicar dados de contador binário
        topic2 = f"tenants/{tenant}/gateways/khomp/device-002"
        payload2 = create_khomp_senml_payload_binary_counter()
        
        print(f"\n📤 Publicando no tópico: {topic2}")
        print(f"📦 Payload (contador binário):")
        print(json.dumps(payload2, indent=2))
        
        result2 = client.publish(topic2, json.dumps(payload2), qos=1)
        result2.wait_for_publish()
        
        time.sleep(1)
        
        print("\n" + "=" * 80)
        print("✅ TODOS OS DADOS FORAM PUBLICADOS COM SUCESSO!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        client.loop_stop()
        client.disconnect()
        print("\n🔌 Desconectado do broker")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Publica dados de teste no formato Khomp SenML"
    )
    parser.add_argument(
        "--host",
        default="localhost",
        help="Host do broker MQTT (default: localhost)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=1883,
        help="Porta do broker MQTT (default: 1883)"
    )
    parser.add_argument(
        "--tenant",
        default="umc",
        help="Slug do tenant (default: umc)"
    )
    
    args = parser.parse_args()
    
    publish_test_data(
        broker_host=args.host,
        broker_port=args.port,
        tenant=args.tenant
    )
