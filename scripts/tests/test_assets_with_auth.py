"""
Testa login e depois busca assets
"""
import requests

# 1. Fazer login
login_url = "http://umc.localhost:8000/api/auth/login/"
login_data = {
    "username_or_email": "admin@traksense.com",
    "password": "admin123"
}

print("🔐 Fazendo login...")
login_response = requests.post(login_url, json=login_data)

if login_response.status_code != 200:
    print(f"❌ Erro no login: {login_response.status_code}")
    print(login_response.json())
    exit(1)

token = login_response.json()['access']
print(f"✅ Login OK! Token: {token[:50]}...\n")

# 2. Buscar assets
assets_url = "http://umc.localhost:8000/api/assets/"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

print(f"📦 Buscando assets em {assets_url}")
assets_response = requests.get(assets_url, headers=headers)

print(f"Status: {assets_response.status_code}")

if assets_response.status_code == 200:
    data = assets_response.json()
    print(f"\n✅ Sucesso!")
    print(f"Count: {data.get('count', 0)}")
    print(f"Results: {len(data.get('results', []))}")
    
    if data.get('results'):
        print(f"\n📋 Assets encontrados:")
        for asset in data['results']:
            print(f"  - {asset.get('tag')} | {asset.get('name')} | Tipo: {asset.get('asset_type')}")
    else:
        print("\n⚠️ Nenhum asset no resultado")
else:
    print(f"\n❌ Erro: {assets_response.status_code}")
    print(assets_response.text)
