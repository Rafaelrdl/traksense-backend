import requests

url = "http://umc.localhost:8000/api/auth/login/"
data = {
    "username_or_email": "admin@traksense.com",
    "password": "admin123"
}

print(f"🔵 Testando login com admin@traksense.com")
print(f"URL: {url}\n")

response = requests.post(url, json=data)

print(f"Status: {response.status_code}")
if response.status_code == 200:
    result = response.json()
    print(f"✅ LOGIN FUNCIONOU!")
    print(f"Usuário: {result['user']['username']} ({result['user']['email']})")
    print(f"Token gerado: {result['access'][:50]}...")
else:
    print(f"❌ ERRO: {response.json()}")
