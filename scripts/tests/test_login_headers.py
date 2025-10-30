"""
Teste de login com headers completos
"""
import requests
import json

BASE_URL = "http://umc.localhost:8000/api"

headers = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Origin": "http://localhost:5000",
    "Host": "umc.localhost:8000",
}

payload = {
    "username_or_email": "testuser",
    "password": "test123"
}

print("Testando login com headers completos...")
print(f"URL: {BASE_URL}/auth/login/")
print(f"Headers: {json.dumps(headers, indent=2)}")
print(f"Payload: {json.dumps(payload, indent=2)}")
print()

try:
    response = requests.post(
        f"{BASE_URL}/auth/login/",
        json=payload,
        headers=headers,
        timeout=10
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"\nResponse Headers:")
    for key, value in response.headers.items():
        print(f"  {key}: {value}")
    
    print(f"\nResponse Body:")
    try:
        print(json.dumps(response.json(), indent=2))
    except:
        print(response.text)
        
    # Verificar se há erro de CORS
    print(f"\nCORS Headers:")
    print(f"  Access-Control-Allow-Origin: {response.headers.get('Access-Control-Allow-Origin', 'N/A')}")
    print(f"  Access-Control-Allow-Credentials: {response.headers.get('Access-Control-Allow-Credentials', 'N/A')}")
    
except Exception as e:
    print(f"Erro: {e}")
