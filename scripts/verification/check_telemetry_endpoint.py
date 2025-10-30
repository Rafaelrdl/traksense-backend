#!/usr/bin/env python
"""
Script para verificar o endpoint de telemetria e os sensores.
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
from rest_framework_simplejwt.tokens import RefreshToken

def check_telemetry_endpoint():
    """Verifica o endpoint de telemetria."""
    print("=" * 70)
    print("🔍 VERIFICANDO ENDPOINT DE TELEMETRIA")
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
    
    # Request
    device_id = 'GW-1760908415'
    url = f'http://localhost:8000/api/telemetry/devices/{device_id}/summary/'
    
    print(f"\n📡 URL: {url}")
    print(f"🎯 Device ID: {device_id}")
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        print(f"\n📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Resposta recebida:")
            print(f"   Device: {data.get('deviceName', 'N/A')}")
            print(f"   Sensores: {len(data.get('sensors', []))}")
            
            if data.get('sensors'):
                print(f"\n📋 Lista de sensores:")
                for sensor in data['sensors']:
                    print(f"   • {sensor.get('sensorId')} - {sensor.get('sensorType')}")
                    print(f"     Último valor: {sensor.get('lastValue')} {sensor.get('unit')}")
                    print(f"     Última leitura: {sensor.get('lastReadingAt')}")
            else:
                print(f"\n⚠️  Nenhum sensor encontrado no summary")
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
    check_telemetry_endpoint()
    print("\n" + "=" * 70)
    print("✅ Script finalizado!")
    print("=" * 70)
