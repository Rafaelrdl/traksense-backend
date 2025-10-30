"""
Script simples de teste da API de Assets sem emojis para Windows
"""
import requests
import json
import time

# Configuração
BASE_URL = "http://umc.localhost:8000"
USERNAME = "testapi"
PASSWORD = "Test@123456"
TIMESTAMP = int(time.time())  # Para criar tags únicas

print("\n" + "="*60)
print("TESTE DA API DE ASSETS - TRAKSENSE")
print("="*60)

# 1. Autenticação
print("\n[1/6] Fazendo login...")
try:
    response = requests.post(
        f"{BASE_URL}/api/auth/login/",
        json={"username_or_email": USERNAME, "password": PASSWORD},
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code != 200:
        print(f"ERRO: Status {response.status_code}")
        print(response.text[:500])
        exit(1)
    
    token = response.json().get('access')
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    print("OK - Autenticado com sucesso!")

except Exception as e:
    print(f"ERRO: {str(e)}")
    exit(1)

# 2. Criar Site
print("\n[2/6] Criando Site...")
site_data = {
    "name": "Hospital Sao Lucas",
    "address": "Av. Paulista, 1000 - Sao Paulo, SP",
    "latitude": "-23.5629",
    "longitude": "-46.6544",
    "timezone": "America/Sao_Paulo",
    "company": "Rede Hospitalar SP",
    "sector": "Saude",
    "subsector": "Hospitais"
}

try:
    response = requests.post(f"{BASE_URL}/api/sites/", json=site_data, headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 201:
        site = response.json()
        site_id = site['id']
        print(f"OK - Site criado com ID: {site_id}")
    else:
        print(f"ERRO: {response.text[:500]}")
        exit(1)
except Exception as e:
    print(f"ERRO: {str(e)}")
    exit(1)

# 3. Listar Sites
print("\n[3/6] Listando Sites...")
try:
    response = requests.get(f"{BASE_URL}/api/sites/", headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        count = data.get('count', len(data.get('results', [])))
        print(f"OK - Total de sites: {count}")
    else:
        print(f"ERRO: {response.text[:200]}")
except Exception as e:
    print(f"ERRO: {str(e)}")

# 4. Criar Asset
print("\n[4/6] Criando Asset (Chiller)...")
asset_data = {
    "tag": f"CHILLER-{TIMESTAMP}",
    "site": site_id,
    "asset_type": "CHILLER",
    "manufacturer": "Carrier",
    "model": "30XA-302",
    "status": "OK",
    "specifications": {
        "refrigerant": "R-134a",
        "compressor_type": "Screw",
        "cooling_capacity_kw": 1054
    }
}

try:
    response = requests.post(f"{BASE_URL}/api/assets/", json=asset_data, headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 201:
        asset = response.json()
        asset_id = asset['id']
        print(f"OK - Asset criado com ID: {asset_id}")
    else:
        print(f"ERRO: {response.text[:500]}")
        exit(1)
except Exception as e:
    print(f"ERRO: {str(e)}")
    exit(1)

# 5. Criar Device
print("\n[5/6] Criando Device...")
device_data = {
    "name": f"Gateway-{TIMESTAMP}",
    "serial_number": f"GW-{TIMESTAMP}",
    "asset": asset_id,
    "mqtt_client_id": f"traksense_gw_{TIMESTAMP}",
    "device_type": "GATEWAY",
    "status": "ONLINE"
}

try:
    response = requests.post(f"{BASE_URL}/api/devices/", json=device_data, headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 201:
        device = response.json()
        device_id = device['id']
        print(f"OK - Device criado com ID: {device_id}")
    else:
        print(f"ERRO: {response.text[:500]}")
        exit(1)
except Exception as e:
    print(f"ERRO: {str(e)}")
    exit(1)

# 6. Criar Sensor
print("\n[6/6] Criando Sensor...")
sensor_data = {
    "tag": f"TEMP-{TIMESTAMP}",
    "device": device_id,
    "metric_type": "temp_supply",
    "unit": "°C",
    "thresholds": {"min": 4, "max": 12, "critical_min": 0, "critical_max": 15}
}

try:
    response = requests.post(f"{BASE_URL}/api/sensors/", json=sensor_data, headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 201:
        sensor = response.json()
        sensor_id = sensor['id']
        print(f"OK - Sensor criado com ID: {sensor_id}")
    else:
        print(f"ERRO: {response.text[:500]}")
        exit(1)
except Exception as e:
    print(f"ERRO: {str(e)}")
    exit(1)

# Resumo
print("\n" + "="*60)
print("RESUMO DOS TESTES")
print("="*60)
print(f"Site criado:   ID {site_id} - {site_data['name']}")
print(f"Asset criado:  ID {asset_id} - {asset_data['tag']}")
print(f"Device criado: ID {device_id} - {device_data['name']}")
print(f"Sensor criado: ID {sensor_id} - {sensor_data['tag']}")
print("\nTODOS OS TESTES PASSARAM COM SUCESSO!")
print("="*60 + "\n")
