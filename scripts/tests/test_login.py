import requests
import json

url = "http://umc.localhost:8000/api/auth/login/"
headers = {
    "Host": "umc.localhost",
    "Content-Type": "application/json",
    "Origin": "http://localhost:5000"
}
data = {
    "username_or_email": "test@umc.com",
    "password": "TestPass123!"
}

print("🔵 Fazendo requisição de login...")
print(f"URL: {url}")
print(f"Headers: {json.dumps(headers, indent=2)}")
print(f"Body: {json.dumps(data, indent=2)}")
print()

try:
    response = requests.post(url, headers=headers, json=data)
    print(f"✅ Status: {response.status_code}")
    print(f"📦 Response:")
    print(json.dumps(response.json(), indent=2))
except requests.exceptions.HTTPError as e:
    print(f"❌ HTTP Error: {e}")
    print(f"Response: {e.response.text}")
except Exception as e:
    print(f"❌ Error: {e}")
