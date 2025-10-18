import paho.mqtt.publish as publish
import json

payload = json.dumps({"value": 28.5, "unit": "celsius", "sensor": "dht22"})

publish.single(
    topic='tenants/umc/esp32-001/temperature',
    payload=payload,
    hostname='localhost',
    port=1883,
    auth={'username': 'umc_device', 'password': 'umc123'},
    client_id='esp32-test-003'
)

print("✅ Mensagem MQTT publicada com sucesso!")
print(f"Topic: tenants/umc/esp32-001/temperature")
print(f"Payload: {payload}")
