import requests
import json
from datetime import datetime

# Login
print('🔐 Fazendo login...')
r = requests.post('http://umc.localhost:8000/api/auth/login/', json={
    'username_or_email': 'admin',
    'password': 'admin123'
})
token = r.json()['access']
print('✅ Login realizado\n')

# Buscar regras ativas
print('📋 Buscando regras ativas...')
r = requests.get('http://umc.localhost:8000/api/alerts/rules/', 
                 headers={'Authorization': f'Bearer {token}'})
rules = r.json()['results']
print(f'Encontradas {len(rules)} regras:\n')

for rule in rules:
    print(f'   - ID {rule["id"]}: {rule["name"]}')
    print(f'     Condição: {rule["condition_display"]}')
    print(f'     Equipment: {rule["equipment_name"]} (ID: {rule["equipment"]})')
    print(f'     Severity: {rule["severity"]}')
    print()

# Publicar telemetria que viola a regra (TEMPERATURE > 25.0)
print('📡 Publicando telemetria com temperatura ALTA (30°C)...')
telemetry_data = {
    'asset_id': 6,  # CHILLER-001
    'timestamp': datetime.utcnow().isoformat() + 'Z',
    'data': {
        'TEMPERATURE': 30.0,  # Acima do threshold de 25.0
        'PRESSURE': 100.0,
        'HUMIDITY': 60.0
    }
}

r = requests.post('http://umc.localhost:8000/api/ingest/telemetry/', 
                  json=telemetry_data,
                  headers={'Authorization': f'Bearer {token}'})

if r.status_code in [200, 201]:
    print('✅ Telemetria publicada com sucesso!')
else:
    print(f'❌ Erro ao publicar telemetria: {r.status_code}')
    print(f'   Response: {r.text}')

# Aguardar processamento
print('\n⏳ Aguardando processamento...')
import time
time.sleep(3)

# Verificar alertas gerados
print('\n🚨 Verificando alertas gerados...')
r = requests.get('http://umc.localhost:8000/api/alerts/alerts/', 
                 headers={'Authorization': f'Bearer {token}'})

if r.status_code == 200:
    alerts = r.json()['results']
    print(f'Total de alertas: {len(alerts)}\n')
    
    if len(alerts) > 0:
        for alert in alerts:
            print(f'   - ID {alert["id"]}: {alert["rule_name"]}')
            print(f'     Asset: {alert["asset_tag"]}')
            print(f'     Mensagem: {alert["message"]}')
            print(f'     Severity: {alert["severity"]}')
            print(f'     Status: {"Ativo" if alert["is_active"] else "Inativo"}')
            print(f'     Triggered: {alert["triggered_at"]}')
            print()
        print('✅ Sistema de alertas funcionando!')
    else:
        print('⚠️ Nenhum alerta foi gerado. Possíveis causas:')
        print('   - O sistema de checagem de regras pode não estar rodando')
        print('   - Pode haver delay no processamento')
        print('   - A telemetria pode não ter sido persistida corretamente')
else:
    print(f'❌ Erro ao buscar alertas: {r.status_code}')
