#!/usr/bin/env python
"""
Teste com host correto do tenant
"""
import os
import sys
import django
import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.accounts.models import User
from rest_framework_simplejwt.tokens import RefreshToken

user = User.objects.first()
token = RefreshToken.for_user(user)
access_token = str(token.access_token)

headers = {
    'Authorization': f'Bearer {access_token}',
    'Content-Type': 'application/json',
    'Host': 'umc.localhost:8000',  # ← IMPORTANTE: Host do tenant
}

base_url = 'http://localhost:8000'

# Testar endpoint assets
print("Testando /api/sites/7/assets/ com Host: umc.localhost:8000:")
response = requests.get(f'{base_url}/api/sites/7/assets/', headers=headers)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"✅ {len(data)} assets retornados")

# Testar novo endpoint devices
print("\nTestando /api/sites/7/devices/ com Host: umc.localhost:8000:")
response2 = requests.get(f'{base_url}/api/sites/7/devices/', headers=headers)
print(f"Status: {response2.status_code}")
if response2.status_code == 200:
    data = response2.json()
    print(f"✅ {len(data)} devices retornados")
    for device in data:
        print(f"  - {device.get('name')} ({device.get('mqtt_client_id')})")
else:
    print(f"❌ Erro")
