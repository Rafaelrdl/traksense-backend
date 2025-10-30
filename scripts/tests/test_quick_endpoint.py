#!/usr/bin/env python
"""
Teste rápido para verificar se endpoint assets/ funciona
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
}

# Testar endpoint que já existe
print("Testando /api/sites/7/assets/:")
response = requests.get('http://localhost:8000/api/sites/7/assets/', headers=headers)
print(f"Status: {response.status_code}")

# Testar novo endpoint
print("\nTestando /api/sites/7/devices/:")
response2 = requests.get('http://localhost:8000/api/sites/7/devices/', headers=headers)
print(f"Status: {response2.status_code}")
if response2.status_code == 200:
    print("✅ Endpoint funcionando!")
else:
    print(f"❌ Erro: {response2.text[:200]}")
