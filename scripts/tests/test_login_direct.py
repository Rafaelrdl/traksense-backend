"""
Teste direto de login no backend
"""
import requests
import json

# URL do backend
BASE_URL = "http://umc.localhost:8000/api"

# Dados de login
login_data = {
    "username_or_email": "admin@umc.local",
    "password": "admin123"
}

print("🔍 Testando endpoint de login...")
print(f"📍 URL: {BASE_URL}/auth/login/")
print(f"📦 Payload: {json.dumps(login_data, indent=2)}")
print()

try:
    response = requests.post(
        f"{BASE_URL}/auth/login/",
        json=login_data,
        headers={"Content-Type": "application/json"},
        timeout=10
    )
    
    print(f"📊 Status Code: {response.status_code}")
    print(f"📄 Response Headers: {dict(response.headers)}")
    print()
    
    if response.status_code == 200:
        print("✅ Login bem-sucedido!")
        data = response.json()
        print(f"👤 Usuário: {data.get('user', {}).get('email')}")
        print(f"🔑 Access Token: {data.get('access', '')[:50]}...")
        print(f"🔄 Refresh Token: {data.get('refresh', '')[:50]}...")
    else:
        print(f"❌ Erro no login!")
        print(f"📄 Response Body:")
        try:
            print(json.dumps(response.json(), indent=2))
        except:
            print(response.text)
            
except requests.exceptions.ConnectionError as e:
    print("❌ Erro de conexão!")
    print(f"   Backend não está rodando em {BASE_URL}")
    print(f"   Detalhes: {e}")
except requests.exceptions.Timeout:
    print("❌ Timeout!")
    print(f"   Backend demorou mais de 10 segundos para responder")
except Exception as e:
    print(f"❌ Erro inesperado: {e}")
