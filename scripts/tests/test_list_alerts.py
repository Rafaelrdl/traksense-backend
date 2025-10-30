import requests
import json

# Login
r = requests.post('http://umc.localhost:8000/api/auth/login/', json={
    'username_or_email': 'admin',
    'password': 'admin123'
})
token = r.json()['access']

# Listar alertas
r2 = requests.get('http://umc.localhost:8000/api/alerts/alerts/', headers={
    'Authorization': f'Bearer {token}'
})

data = r2.json()
print(f'Status: {r2.status_code}')
print(f'Total alerts: {data.get("count", 0)}')
print(f'\nFirst 3 alerts:')
print(json.dumps(data.get('results', [])[:3], indent=2))
