"""
Teste detalhado de login
"""
import requests
import json

BASE_URL = "http://umc.localhost:8000/api"

# Teste 1: Com username
print("=" * 60)
print("TESTE 1: Login com USERNAME")
print("=" * 60)
payload1 = {
    "username_or_email": "admin",
    "password": "admin123"
}
print(f"Payload: {json.dumps(payload1, indent=2)}")

response1 = requests.post(
    f"{BASE_URL}/auth/login/",
    json=payload1,
    headers={"Content-Type": "application/json"}
)

print(f"\nStatus Code: {response1.status_code}")
print(f"Response Headers: {dict(response1.headers)}")

if response1.status_code == 200:
    print("\n✅ LOGIN COM USERNAME FUNCIONOU!")
    data = response1.json()
    print(f"User: {data.get('user', {}).get('email')}")
    print(f"Access Token: {data.get('access', '')[:50]}...")
else:
    print(f"\n❌ ERRO COM USERNAME")
    print(f"Response: {response1.text}")

# Teste 2: Com email
print("\n" + "=" * 60)
print("TESTE 2: Login com EMAIL")
print("=" * 60)
payload2 = {
    "username_or_email": "admin@traksense.com",
    "password": "admin123"
}
print(f"Payload: {json.dumps(payload2, indent=2)}")

response2 = requests.post(
    f"{BASE_URL}/auth/login/",
    json=payload2,
    headers={"Content-Type": "application/json"}
)

print(f"\nStatus Code: {response2.status_code}")
print(f"Response Headers: {dict(response2.headers)}")

if response2.status_code == 200:
    print("\n✅ LOGIN COM EMAIL FUNCIONOU!")
    data = response2.json()
    print(f"User: {data.get('user', {}).get('email')}")
    print(f"Access Token: {data.get('access', '')[:50]}...")
else:
    print(f"\n❌ ERRO COM EMAIL")
    print(f"Response: {response2.text}")

# Teste 3: Verificar banco de dados
print("\n" + "=" * 60)
print("TESTE 3: Verificar dados no banco")
print("=" * 60)
print("Execute no backend:")
print('docker-compose exec api python manage.py shell -c "from apps.accounts.models import User; u = User.objects.get(username=\'admin\'); print(f\'Email: {u.email}\'); print(f\'Username: {u.username}\'); print(f\'Has usable password: {u.has_usable_password()}\')"')
