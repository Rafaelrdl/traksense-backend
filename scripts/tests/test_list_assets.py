import requests

# Login
r = requests.post('http://umc.localhost:8000/api/auth/login/', json={
    'username_or_email': 'admin',
    'password': 'admin123'
})
token = r.json()['access']

# Listar assets
r2 = requests.get('http://umc.localhost:8000/api/assets/', headers={
    'Authorization': f'Bearer {token}'
})
assets = r2.json()['results']

print('Assets disponíveis:')
for a in assets[:10]:
    print(f"  ID: {a['id']}, Tag: {a['tag']}, Name: {a['name']}")

print(f"\nTotal: {len(assets)} assets")
