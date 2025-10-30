import requests

url = "http://localhost:8000/api/auth/login/"
data = {
    "username_or_email": "admin",
    "password": "admin123"
}

print(f"Testing login at {url}")
response = requests.post(url, json=data)

print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
