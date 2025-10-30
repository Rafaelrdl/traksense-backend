"""
Script de teste para validar os endpoints da API de Assets.

Este script testa:
1. Criação de Site
2. Criação de Asset
3. Criação de Device
4. Criação de Sensor
5. Listagem com filtros
6. Ações customizadas (stats, heartbeat, etc)

Uso:
    python test_assets_api.py
"""

import requests
import json
from datetime import datetime

# Configuração
BASE_URL = "http://umc.localhost:8000"
TENANT_DOMAIN = "umc.localhost:8000"
HEADERS = {
    "Content-Type": "application/json",
}

# Credenciais de teste (criadas com create_test_user_assets.py)
USERNAME = "testapi"
PASSWORD = "Test@123456"


def get_auth_token():
    """Obtém token de autenticação."""
    response = requests.post(
        f"{BASE_URL}/api/auth/login/",
        json={"username_or_email": USERNAME, "password": PASSWORD},
        headers=HEADERS
    )
    if response.status_code == 200:
        data = response.json()
        # Tenta 'access' primeiro, senão usa 'access_token'
        return data.get("access") or data.get("access_token")
    else:
        print(f"❌ Erro ao autenticar: {response.status_code}")
        print(response.text)
        return None


def test_create_site(token):
    """Testa criação de Site."""
    print("\n" + "="*60)
    print("📍 TESTE 1: Criar Site")
    print("="*60)
    
    headers = {**HEADERS, "Authorization": f"Bearer {token}"}
    
    site_data = {
        "name": "Hospital São Lucas",
        "company": "Rede Saúde Brasil",
        "sector": "Saúde",
        "subsector": "Hospital",
        "address": "Rua das Flores, 123",
        "city": "São Paulo",
        "state": "SP",
        "country": "Brasil",
        "postal_code": "01234-567",
        "latitude": -23.550520,
        "longitude": -46.633308,
        "timezone": "America/Sao_Paulo",
        "metadata": {
            "capacity": 200,
            "floors": 5
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/api/sites/",
        json=site_data,
        headers=headers
    )
    
    if response.status_code == 201:
        site = response.json()
        print(f"✅ Site criado com sucesso!")
        print(f"   ID: {site['id']}")
        print(f"   Nome: {site['name']}")
        print(f"   Full Name: {site['full_name']}")
        print(f"   Asset Count: {site['asset_count']}")
        return site['id']
    else:
        print(f"❌ Erro: {response.status_code}")
        print(response.text)
        return None


def test_create_asset(token, site_id):
    """Testa criação de Asset."""
    print("\n" + "="*60)
    print("🏭 TESTE 2: Criar Asset")
    print("="*60)
    
    headers = {**HEADERS, "Authorization": f"Bearer {token}"}
    
    asset_data = {
        "tag": "CHILL-001",
        "name": "Chiller Central",
        "site": site_id,
        "asset_type": "CHILLER",
        "manufacturer": "Carrier",
        "model": "30XA-1202",
        "serial_number": "SN123456789",
        "installation_date": "2023-01-15",
        "warranty_expiry": "2026-01-15",
        "status": "OPERATIONAL",
        "specifications": {
            "capacity": "1200 TR",
            "refrigerant": "R-134a",
            "voltage": "380V"
        },
        "notes": "Chiller principal do edifício"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/assets/",
        json=asset_data,
        headers=headers
    )
    
    if response.status_code == 201:
        asset = response.json()
        print(f"✅ Asset criado com sucesso!")
        print(f"   ID: {asset['id']}")
        print(f"   Tag: {asset['tag']}")
        print(f"   Nome: {asset['name']}")
        print(f"   Site: {asset['site_name']}")
        print(f"   Tipo: {asset['asset_type']}")
        print(f"   Status: {asset['status']}")
        print(f"   Health Score: {asset['health_score']}")
        return asset['id']
    else:
        print(f"❌ Erro: {response.status_code}")
        print(response.text)
        return None


def test_create_device(token, asset_id):
    """Testa criação de Device."""
    print("\n" + "="*60)
    print("📱 TESTE 3: Criar Device")
    print("="*60)
    
    headers = {**HEADERS, "Authorization": f"Bearer {token}"}
    
    device_data = {
        "name": "Gateway Principal",
        "serial_number": "GW-2024-001",
        "asset": asset_id,
        "device_type": "GATEWAY",
        "mqtt_client_id": "traksense_gw_001",
        "status": "ACTIVE",
        "firmware_version": "1.2.3",
        "metadata": {
            "ip_address": "192.168.1.100",
            "mac_address": "00:1B:44:11:3A:B7"
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/api/devices/",
        json=device_data,
        headers=headers
    )
    
    if response.status_code == 201:
        device = response.json()
        print(f"✅ Device criado com sucesso!")
        print(f"   ID: {device['id']}")
        print(f"   Nome: {device['name']}")
        print(f"   Serial: {device['serial_number']}")
        print(f"   Asset: {device['asset_tag']}")
        print(f"   MQTT Client ID: {device['mqtt_client_id']}")
        print(f"   Status: {device['status']}")
        return device['id']
    else:
        print(f"❌ Erro: {response.status_code}")
        print(response.text)
        return None


def test_create_sensor(token, device_id):
    """Testa criação de Sensor."""
    print("\n" + "="*60)
    print("🌡️  TESTE 4: Criar Sensor")
    print("="*60)
    
    headers = {**HEADERS, "Authorization": f"Bearer {token}"}
    
    sensor_data = {
        "tag": "TEMP-SUPPLY-001",
        "device": device_id,
        "metric_type": "TEMPERATURE",
        "unit": "°C",
        "description": "Temperatura de suprimento",
        "thresholds": {
            "min": 5.0,
            "max": 15.0,
            "warning_min": 7.0,
            "warning_max": 12.0
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/api/sensors/",
        json=sensor_data,
        headers=headers
    )
    
    if response.status_code == 201:
        sensor = response.json()
        print(f"✅ Sensor criado com sucesso!")
        print(f"   ID: {sensor['id']}")
        print(f"   Tag: {sensor['tag']}")
        print(f"   Device: {sensor['device_name']}")
        print(f"   Asset: {sensor['asset_tag']}")
        print(f"   Tipo: {sensor['metric_type']}")
        print(f"   Unidade: {sensor['unit']}")
        return sensor['id']
    else:
        print(f"❌ Erro: {response.status_code}")
        print(response.text)
        return None


def test_list_sites(token):
    """Testa listagem de Sites."""
    print("\n" + "="*60)
    print("📋 TESTE 5: Listar Sites")
    print("="*60)
    
    headers = {**HEADERS, "Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{BASE_URL}/api/sites/",
        headers=headers
    )
    
    if response.status_code == 200:
        sites = response.json()
        print(f"✅ {len(sites)} site(s) encontrado(s):")
        for site in sites:
            print(f"   - {site['name']} ({site['company']}) - {site['asset_count']} assets")
    else:
        print(f"❌ Erro: {response.status_code}")


def test_list_assets_with_filter(token):
    """Testa listagem de Assets com filtro."""
    print("\n" + "="*60)
    print("🔍 TESTE 6: Listar Assets com Filtro")
    print("="*60)
    
    headers = {**HEADERS, "Authorization": f"Bearer {token}"}
    
    # Teste 1: Filtrar por tipo
    response = requests.get(
        f"{BASE_URL}/api/assets/?asset_type=CHILLER",
        headers=headers
    )
    
    if response.status_code == 200:
        assets = response.json()
        print(f"✅ Assets tipo CHILLER: {len(assets)}")
        for asset in assets:
            print(f"   - {asset['tag']}: {asset['name']} ({asset['status']})")
    
    # Teste 2: Filtrar por status
    response = requests.get(
        f"{BASE_URL}/api/assets/?status=OPERATIONAL",
        headers=headers
    )
    
    if response.status_code == 200:
        assets = response.json()
        print(f"✅ Assets OPERATIONAL: {len(assets)}")


def test_site_stats(token, site_id):
    """Testa estatísticas do Site."""
    print("\n" + "="*60)
    print("📊 TESTE 7: Estatísticas do Site")
    print("="*60)
    
    headers = {**HEADERS, "Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{BASE_URL}/api/sites/{site_id}/stats/",
        headers=headers
    )
    
    if response.status_code == 200:
        stats = response.json()
        print(f"✅ Estatísticas:")
        print(f"   Total Assets: {stats['total_assets']}")
        print(f"   Total Devices: {stats['total_devices']}")
        print(f"   Total Sensors: {stats['total_sensors']}")
        print(f"   Online Devices: {stats['online_devices']}")
        print(f"   Online Sensors: {stats['online_sensors']}")
        print(f"   Assets por Status: {stats['assets_by_status']}")
        print(f"   Assets por Tipo: {stats['assets_by_type']}")
    else:
        print(f"❌ Erro: {response.status_code}")


def test_device_heartbeat(token, device_id):
    """Testa heartbeat do Device."""
    print("\n" + "="*60)
    print("💓 TESTE 8: Device Heartbeat")
    print("="*60)
    
    headers = {**HEADERS, "Authorization": f"Bearer {token}"}
    
    response = requests.post(
        f"{BASE_URL}/api/devices/{device_id}/heartbeat/",
        headers=headers
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Heartbeat registrado:")
        print(f"   Last Seen: {result['last_seen']}")
        print(f"   Is Online: {result['is_online']}")
        print(f"   Status: {result['status']}")
    else:
        print(f"❌ Erro: {response.status_code}")


def test_sensor_update_reading(token, sensor_id):
    """Testa atualização de leitura do Sensor."""
    print("\n" + "="*60)
    print("📈 TESTE 9: Atualizar Leitura do Sensor")
    print("="*60)
    
    headers = {**HEADERS, "Authorization": f"Bearer {token}"}
    
    reading_data = {
        "value": 8.5,
        "timestamp": datetime.now().isoformat()
    }
    
    response = requests.post(
        f"{BASE_URL}/api/sensors/{sensor_id}/update_reading/",
        json=reading_data,
        headers=headers
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Leitura atualizada:")
        print(f"   Last Value: {result['last_value']}")
        print(f"   Last Reading: {result['last_reading']}")
        print(f"   Is Online: {result['is_online']}")
    else:
        print(f"❌ Erro: {response.status_code}")


def main():
    """Executa todos os testes."""
    print("\n" + "="*60)
    print("🚀 INICIANDO TESTES DA API DE ASSETS")
    print("="*60)
    
    # Autenticação
    print("\n🔑 Autenticando...")
    token = get_auth_token()
    if not token:
        print("❌ Falha na autenticação. Verifique as credenciais.")
        return
    print("✅ Autenticado com sucesso!")
    
    # Testes de criação
    site_id = test_create_site(token)
    if not site_id:
        return
    
    asset_id = test_create_asset(token, site_id)
    if not asset_id:
        return
    
    device_id = test_create_device(token, asset_id)
    if not device_id:
        return
    
    sensor_id = test_create_sensor(token, device_id)
    if not sensor_id:
        return
    
    # Testes de listagem
    test_list_sites(token)
    test_list_assets_with_filter(token)
    
    # Testes de ações customizadas
    test_site_stats(token, site_id)
    test_device_heartbeat(token, device_id)
    test_sensor_update_reading(token, sensor_id)
    
    # Resumo final
    print("\n" + "="*60)
    print("✅ TODOS OS TESTES CONCLUÍDOS!")
    print("="*60)
    print(f"\nIDs criados:")
    print(f"  Site ID: {site_id}")
    print(f"  Asset ID: {asset_id}")
    print(f"  Device ID: {device_id}")
    print(f"  Sensor ID: {sensor_id}")
    print("\nPróximos passos:")
    print("  1. Verificar no Django Admin: http://localhost:8000/admin")
    print("  2. Explorar Browsable API: http://localhost:8000/api/")
    print("  3. Ver Swagger Docs: http://localhost:8000/api/docs/")


if __name__ == "__main__":
    main()
