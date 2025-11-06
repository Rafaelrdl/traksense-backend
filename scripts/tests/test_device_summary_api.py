"""
Script para testar o novo endpoint de Device Summary.

Testa:
    - GET /api/sites/{id}/devices/summary/
    - GET /api/devices/{id}/summary/
"""
import requests
import json

# Configuração
BASE_URL = "http://umc.localhost:8000/api"
SITE_ID = 1

def test_site_devices_summary():
    """Testa endpoint de devices summary por site."""
    print("=" * 60)
    print("🧪 Testando GET /api/sites/{id}/devices/summary/")
    print("=" * 60)
    
    url = f"{BASE_URL}/sites/{SITE_ID}/devices/summary/"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        data = response.json()
        
        print(f"\n✅ Status Code: {response.status_code}")
        print(f"📊 Total de devices: {len(data)}")
        
        for device in data:
            print(f"\n{'='*60}")
            print(f"🔧 Device: {device['name']}")
            print(f"   ID: {device['id']}")
            print(f"   MQTT Client ID: {device['mqtt_client_id']}")
            print(f"   Type: {device['device_type']}")
            print(f"   Status: {device['device_status']}")
            print(f"   Asset: {device['asset_info']['tag']} - {device['asset_info']['name']}")
            print(f"   Total Variables: {device['total_variables_count']}")
            print(f"   Online Variables: {device['online_variables_count']}")
            
            print(f"\n   📊 Variables ({len(device['variables'])}):")
            for var in device['variables']:
                status_icon = "🟢" if var['is_online'] else "🔴"
                print(f"      {status_icon} {var['name']}: {var['last_value']} {var['unit']}")
        
        print(f"\n{'='*60}")
        print("✅ Teste concluído com sucesso!")
        
        return data
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Erro na requisição: {e}")
        if hasattr(e.response, 'text'):
            print(f"   Resposta: {e.response.text}")
        return None


def test_device_summary(device_id):
    """Testa endpoint de device summary individual."""
    print("\n" + "=" * 60)
    print(f"🧪 Testando GET /api/devices/{device_id}/summary/")
    print("=" * 60)
    
    url = f"{BASE_URL}/devices/{device_id}/summary/"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        data = response.json()
        
        print(f"\n✅ Status Code: {response.status_code}")
        print(f"\n🔧 Device: {data['name']}")
        print(f"   ID: {data['id']}")
        print(f"   MQTT Client ID: {data['mqtt_client_id']}")
        print(f"   Type: {data['device_type']}")
        print(f"   Status: {data['device_status']}")
        print(f"   Asset: {data['asset_info']['tag']} - {data['asset_info']['name']}")
        print(f"   Total Variables: {data['total_variables_count']}")
        print(f"   Online Variables: {data['online_variables_count']}")
        
        print(f"\n   📊 Variables ({len(data['variables'])}):")
        for var in data['variables']:
            status_icon = "🟢" if var['is_online'] else "🔴"
            last_reading = var.get('last_reading_at', 'N/A')
            print(f"      {status_icon} {var['name']}: {var['last_value']} {var['unit']}")
            print(f"         Last reading: {last_reading}")
        
        print(f"\n{'='*60}")
        print("✅ Teste concluído com sucesso!")
        
        return data
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Erro na requisição: {e}")
        if hasattr(e.response, 'text'):
            print(f"   Resposta: {e.response.text}")
        return None


if __name__ == '__main__':
    print("\n🚀 Iniciando testes do Device Summary API\n")
    
    # Teste 1: Listar devices do site com summary
    devices = test_site_devices_summary()
    
    # Teste 2: Buscar summary de device específico
    if devices and len(devices) > 0:
        # Pegar o device Khomp (último device)
        khomp_device = devices[-1]
        test_device_summary(khomp_device['id'])
    
    print("\n" + "=" * 60)
    print("🎉 Todos os testes concluídos!")
    print("=" * 60)
