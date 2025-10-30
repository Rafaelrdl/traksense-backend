"""
Criar readings de telemetria e disparar avaliação de regras.
"""

# Código para criar readings
CODE = """
from apps.ingest.models import Reading
from django.utils import timezone

# Criar reading que dispara regra 1 (sensor_13 > 25.0)
reading1 = Reading.objects.create(
    device_id='CHILLER-001',
    sensor_id='sensor_13',
    value=30.0,
    ts=timezone.now(),
    labels={'unit': '°C', 'location': 'datacenter'}
)
print(f'✅ Reading 1 criado: sensor_13 = 30.0°C (ID: {reading1.id})')

# Criar reading que dispara regra 2 (sensor_15 > 10.0)
reading2 = Reading.objects.create(
    device_id='CHILLER-001',
    sensor_id='sensor_15',
    value=15.0,
    ts=timezone.now(),
    labels={}
)
print(f'✅ Reading 2 criado: sensor_15 = 15.0 (ID: {reading2.id})')

print(f'\\n📊 Total de readings no banco: {Reading.objects.count()}')
print(f'📊 Readings do CHILLER-001: {Reading.objects.filter(device_id="CHILLER-001").count()}')
"""

import subprocess
import sys
import time

print('📡 Criando readings de telemetria via Django shell...\n')
result = subprocess.run(
    ['docker', 'exec', 'traksense-api', 'python', 'manage.py', 'shell', '-c', CODE],
    capture_output=True,
    text=True
)

print(result.stdout)
if 'Traceback' in result.stderr:
    print('❌ Erro:', result.stderr)
    sys.exit(1)

print('\n⏳ Aguardando 2 segundos...\n')
time.sleep(2)

print('🚀 Executando avaliação manual de regras...\n')
result2 = subprocess.run(
    ['docker', 'exec', 'traksense-worker', 'celery', '-A', 'config', 'call', 'alerts.evaluate_rules'],
    capture_output=True,
    text=True,
    timeout=30
)

print(result2.stdout)
if 'ERROR' in result2.stderr or 'Traceback' in result2.stderr:
    print('Log de erros:', result2.stderr)

print('\n⏳ Aguardando processamento...\n')
time.sleep(3)

print('🔍 Verificando alertas gerados...\n')

verify_code = """
import requests
r = requests.post('http://umc.localhost:8000/api/auth/login/', json={'username_or_email': 'admin', 'password': 'admin123'})
token = r.json()['access']
headers = {'Authorization': f'Bearer {token}'}

r2 = requests.get('http://umc.localhost:8000/api/alerts/alerts/', headers=headers)
alerts = r2.json()['results']

print(f'📊 Total de alertas: {len(alerts)}\\n')

if len(alerts) > 0:
    for alert in alerts:
        print(f'🚨 Alerta ID {alert["id"]}:')
        print(f'   - Regra: {alert["rule_name"]}')
        print(f'   - Equipment: {alert["equipment_name"]} ({alert["asset_tag"]})')
        print(f'   - Mensagem: {alert["message"]}')
        print(f'   - Severity: {alert["severity"]}')
        print(f'   - Status: {"Ativo" if alert["is_active"] else "Inativo"}')
        print(f'   - Triggered: {alert["triggered_at"]}')
        print()
else:
    print('⚠️  Nenhum alerta foi gerado.')
    print('\\nPossíveis causas:')
    print('  - Regras em cooldown')
    print('  - Condições das regras não foram atendidas')
    print('  - Erro na avaliação das regras (verifique logs do Celery)')
"""

result3 = subprocess.run([sys.executable, '-c', verify_code], capture_output=True, text=True)
print(result3.stdout)
