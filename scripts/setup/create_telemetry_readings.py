"""
Script para criar leituras de telemetria que disparem alertas.
"""
import requests
from datetime import datetime

# Login
print('🔐 Fazendo login...')
r = requests.post('http://umc.localhost:8000/api/auth/login/', json={
    'username_or_email': 'admin',
    'password': 'admin123'
})
token = r.json()['access']
headers = {'Authorization': f'Bearer {token}'}
print('✅ Login realizado\n')

# Buscar regras ativas
print('📋 Buscando regras ativas...')
r = requests.get('http://umc.localhost:8000/api/alerts/rules/', headers=headers)
rules = r.json()['results']

print(f'Encontradas {len(rules)} regras:\n')
for rule in rules:
    print(f'   Regra ID {rule["id"]}: {rule["name"]}')
    print(f'   - Equipment: {rule["equipment_name"]} (ID: {rule["equipment"]})')
    print(f'   - Condição: {rule["condition_display"]}')
    print(f'   - Parâmetro: {rule["parameter_key"]}')
    print()

# A regra 1 espera: sensor_13 > 25.0 °C (TEMPERATURE)
# A regra 2 espera: sensor_15 > 10.0 (algum outro sensor)

# Vou criar leituras que acionem a regra 1
print('📡 Criando leitura de temperatura alta para CHILLER-001...')

# Criar reading via POST
reading_data = {
    'asset_tag': 'CHILLER-001',
    'parameter_key': 'sensor_13',  # Sensor de temperatura
    'value': 30.0,  # Acima de 25.0
    'unit': '°C',
    'timestamp': datetime.utcnow().isoformat() + 'Z'
}

r = requests.post('http://umc.localhost:8000/api/telemetry/readings/',
                  json=reading_data,
                  headers=headers)

if r.status_code in [200, 201]:
    print('✅ Leitura criada com sucesso!')
    print(f'   Dados: {reading_data}')
else:
    print(f'❌ Erro ao criar leitura: {r.status_code}')
    print(f'   Response: {r.text}')

# Tentar também para o sensor 15
print('\n📡 Criando leitura para sensor_15...')
reading_data2 = {
    'asset_tag': 'CHILLER-001',
    'parameter_key': 'sensor_15',
    'value': 15.0,  # Acima de 10.0
    'unit': '',
    'timestamp': datetime.utcnow().isoformat() + 'Z'
}

r2 = requests.post('http://umc.localhost:8000/api/telemetry/readings/',
                   json=reading_data2,
                   headers=headers)

if r2.status_code in [200, 201]:
    print('✅ Leitura criada com sucesso!')
    print(f'   Dados: {reading_data2}')
else:
    print(f'❌ Erro ao criar leitura: {r2.status_code}')
    print(f'   Response: {r2.text}')

print('\n✅ Leituras criadas! Aguarde a próxima execução do Celery Beat (até 5 minutos)')
print('   Ou execute manualmente: docker exec traksense-worker celery -A config call alerts.evaluate_rules')
