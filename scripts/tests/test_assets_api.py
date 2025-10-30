"""
Testa o endpoint /api/assets/ via HTTP
"""
import requests

url = "http://umc.localhost:8000/api/assets/"
token = "SEU_TOKEN_AQUI"  # Você precisa colocar o token que aparece no localStorage

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

print(f"🔵 Testando GET {url}")
print(f"Headers: {headers}\n")

response = requests.get(url, headers=headers)

print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"✅ Sucesso!")
    print(f"Total de assets: {data.get('count', 0)}")
    print(f"Results: {len(data.get('results', []))}")
    if data.get('results'):
        print(f"\nPrimeiro asset:")
        print(data['results'][0])
else:
    print(f"❌ Erro: {response.text}")
