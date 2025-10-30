#!/usr/bin/env python
"""
Script para testar o endpoint /api/sites/{id}/devices/
"""
import os
import sys
import django
import requests

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.accounts.models import User
from apps.tenants.models import Tenant
from django_tenants.utils import schema_context
from rest_framework_simplejwt.tokens import RefreshToken

def test_sites_devices_endpoint():
    """Testa o endpoint de devices por site."""
    print("=" * 70)
    print("🔍 TESTANDO ENDPOINT /api/sites/{id}/devices/")
    print("=" * 70)
    
    # Get token
    user = User.objects.first()
    if not user:
        print("❌ Nenhum usuário encontrado!")
        return
    
    token = RefreshToken.for_user(user)
    access_token = str(token.access_token)
    
    print(f"\n👤 Usuário: {user.email}")
    print(f"🔑 Token gerado: {access_token[:20]}...")
    
    # Buscar um site do tenant UMC
    tenant = Tenant.objects.get(schema_name='umc')
    
    with schema_context(tenant.schema_name):
        from apps.assets.models import Site, Device, Asset
        
        sites = Site.objects.all()
        
        if not sites.exists():
            print("\n❌ Nenhum site encontrado no tenant UMC!")
            return
        
        site = sites.first()
        print(f"\n📍 Site selecionado: {site.name} (ID: {site.id})")
        
        # Verificar devices no banco
        devices_db = Device.objects.filter(asset__site=site)
        print(f"\n🗄️  Devices no banco para este site: {devices_db.count()}")
        
        for device in devices_db:
            print(f"   • {device.name} ({device.mqtt_client_id}) - {device.device_type}")
            print(f"     Asset: {device.asset.name if device.asset else 'N/A'}")
    
    # Testar endpoint
    url = f'http://localhost:8000/api/sites/{site.id}/devices/'
    
    print(f"\n📡 URL: {url}")
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        print(f"\n📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, list):
                print(f"\n✅ {len(data)} device(s) retornado(s):")
                for device in data:
                    print(f"\n   Device ID: {device.get('id')}")
                    print(f"   Nome: {device.get('name')}")
                    print(f"   MQTT Client ID: {device.get('mqtt_client_id')}")
                    print(f"   Tipo: {device.get('device_type')}")
                    print(f"   Status: {device.get('status')}")
                    print(f"   Online: {device.get('is_online')}")
                    if device.get('asset'):
                        print(f"   Asset: {device['asset'].get('name')}")
            else:
                print(f"\n✅ Resposta recebida:")
                print(data)
        else:
            print(f"\n❌ Erro na resposta:")
            print(response.text[:500])
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Erro na requisição: {e}")
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    test_sites_devices_endpoint()
    print("\n" + "=" * 70)
    print("✅ Script finalizado!")
    print("=" * 70)
