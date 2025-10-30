"""
Script para criar readings de telemetria diretamente no banco via Django shell.
"""

CODE = """
from apps.ingest.models import Reading
from django.utils import timezone
from datetime import timedelta

# Criar reading que dispara regra 1 (sensor_13 > 25.0)
reading1 = Reading.objects.create(
    device_id='CHILLER-001',
    sensor_id='sensor_13',
    asset_tag='CHILLER-001',
    parameter_key='sensor_13',
    ts=timezone.now(),
    value=30.0
)
print(f'✅ Reading 1 criado: sensor_13 = 30.0°C')

# Criar reading que dispara regra 2 (sensor_15 > 10.0)
reading2 = Reading.objects.create(
    device_id='CHILLER-001',
    sensor_id='sensor_15',
    asset_tag='CHILLER-001',
    parameter_key='sensor_15',
    ts=timezone.now(),
    value=15.0
)
print(f'✅ Reading 2 criado: sensor_15 = 15.0')

print(f'\\n📊 Total de readings: {Reading.objects.count()}')
"""

import subprocess
import sys

# Executar código no Django shell via docker
print('📡 Criando readings de telemetria...')
result = subprocess.run(
    ['docker', 'exec', 'traksense-api', 'python', 'manage.py', 'shell', '-c', CODE],
    capture_output=True,
    text=True
)

print(result.stdout)
if result.stderr:
    print('Erros:', result.stderr)

if result.returncode == 0:
    print('\\n✅ Readings criados! Agora executando avaliação de regras...')
    
    # Executar task do Celery manualmente
    result2 = subprocess.run(
        ['docker', 'exec', 'traksense-worker', 'celery', '-A', 'config', 'call', 'alerts.evaluate_rules'],
        capture_output=True,
        text=True,
        timeout=30
    )
    
    print(result2.stdout)
    if result2.stderr:
        print('Log:', result2.stderr)
    
    print('\\n🔍 Verificando alertas gerados...')
    
    # Verificar alertas
    verify_code = """
import requests
r = requests.post('http://umc.localhost:8000/api/auth/login/', json={'username_or_email': 'admin', 'password': 'admin123'})
token = r.json()['access']
r2 = requests.get('http://umc.localhost:8000/api/alerts/alerts/', headers={'Authorization': f'Bearer {token}'})
alerts = r2.json()['results']
print(f'Total de alertas: {len(alerts)}')
for alert in alerts:
    print(f'  - {alert["rule_name"]}: {alert["message"]} (Severity: {alert["severity"]})')
"""
    
    result3 = subprocess.run([sys.executable, '-c', verify_code], capture_output=True, text=True)
    print(result3.stdout)
