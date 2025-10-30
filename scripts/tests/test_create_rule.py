import requests

# Login
r = requests.post('http://umc.localhost:8000/api/auth/login/', json={
    'username_or_email': 'admin',
    'password': 'admin123'
})
token = r.json()['access']
print(f'✅ Login realizado')

# Criar regra
data = {
    'name': 'Temperatura Alta - Chiller 001',
    'equipment': 6,  # CHILLER-001
    'parameter_key': 'TEMPERATURE',
    'variable_key': '',
    'operator': '>',  # Maior que
    'threshold': 25.0,
    'unit': '°C',
    'duration': 5,
    'severity': 'High',  # Com maiúscula
    'actions': ['EMAIL', 'IN_APP'],
    'enabled': True
}

r2 = requests.post('http://umc.localhost:8000/api/alerts/rules/', 
                   json=data, 
                   headers={'Authorization': f'Bearer {token}'})

print(f'\nStatus: {r2.status_code}')
if r2.status_code == 201:
    print('✅ Regra criada com sucesso!')
    print(f'Regra: {r2.json()}')
else:
    print(f'❌ Erro: {r2.text}')
