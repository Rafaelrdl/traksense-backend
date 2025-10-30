"""
Testar endpoint /api/telemetry/device/{device_id}/summary/
"""
import requests
import json

BASE_URL = "http://umc.localhost:8000"
DEVICE_ID = "4b686f6d70107115"

# Credenciais
USERNAME = "admin@umc.com.br"
PASSWORD = "admin123"

print(f"\n{'='*80}")
print(f"TESTANDO ENDPOINT DE TELEMETRIA")
print(f"{'='*80}\n")

# 1. Fazer login
print("1. Fazendo login...")
login_url = f"{BASE_URL}/api/auth/login/"
login_data = {
    "username_or_email": USERNAME,
    "password": PASSWORD
}

login_response = requests.post(login_url, json=login_data)
if login_response.status_code != 200:
    print(f"❌ Login falhou: {login_response.status_code}")
    print(login_response.text)
    exit(1)

tokens = login_response.json()
access_token = tokens['access']
print(f"✅ Login OK - Token obtido")
print()

# 2. Buscar devices do site
print("2. Buscando devices do site...")
sites_url = f"{BASE_URL}/api/sites/"
headers = {"Authorization": f"Bearer {access_token}"}

sites_response = requests.get(sites_url, headers=headers)
if sites_response.status_code != 200:
    print(f"❌ Erro ao buscar sites: {sites_response.status_code}")
    exit(1)

sites = sites_response.json()
print(f"✅ Sites encontrados: {len(sites)}")

# Pegar o primeiro site
site = sites[0]
site_id = site['id']
print(f"   Site: {site['name']} (ID: {site_id})")
print()

# 3. Buscar devices do site
print("3. Buscando devices do site...")
devices_url = f"{BASE_URL}/api/sites/{site_id}/devices/"

devices_response = requests.get(devices_url, headers=headers)
if devices_response.status_code != 200:
    print(f"❌ Erro ao buscar devices: {devices_response.status_code}")
    print(devices_response.text)
    exit(1)

devices = devices_response.json()
print(f"✅ Devices encontrados: {len(devices)}")

if devices:
    device = devices[0]
    print(f"   Device: {device['name']}")
    print(f"   MQTT Client ID: {device.get('mqtt_client_id', 'N/A')}")
    print()
else:
    print("❌ Nenhum device encontrado")
    exit(1)

# 4. Buscar telemetria do device
print("4. Buscando telemetria do device...")
telemetry_url = f"{BASE_URL}/api/telemetry/device/{device['mqtt_client_id']}/summary/"

telemetry_response = requests.get(telemetry_url, headers=headers)
print(f"   URL: {telemetry_url}")
print(f"   Status: {telemetry_response.status_code}")
print()

if telemetry_response.status_code == 200:
    print("✅ Telemetria OK!")
    print()
    telemetry = telemetry_response.json()
    print("Resposta:")
    print(json.dumps(telemetry, indent=2, ensure_ascii=False))
else:
    print(f"❌ Erro ao buscar telemetria:")
    print(telemetry_response.text)
