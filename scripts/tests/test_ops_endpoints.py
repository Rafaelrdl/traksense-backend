#!/usr/bin/env python
"""Script para testar endpoints do Painel Ops."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from django.db import connection

User = get_user_model()

# Criar client HTTP com domínio público
client = Client(SERVER_NAME='localhost')

# Fazer login
admin = User.objects.get(username='admin')
client.force_login(admin)

print(f"Current schema: {connection.schema_name}")

print("\n=== Teste 1: GET /ops/ (Home Page) ===")
response = client.get('/ops/', HTTP_HOST='localhost:8000')
print(f"Status: {response.status_code}")
if hasattr(response, 'templates') and response.templates:
    print(f"Template: {response.templates[0].name}")
if hasattr(response, 'context') and response.context:
    print(f"Context tenants count: {len(response.context.get('tenants', []))}")
else:
    print("Context: N/A (não é TemplateResponse)")

print("\n=== Teste 2: GET /ops/telemetry/ (Query com filtros) ===")
params = {
    'tenant_slug': 'uberlandia-medical-center',
    'sensor_id': 'temp_01',
    'bucket': '1m',
    'limit': 10
}
response = client.get('/ops/telemetry/', params, HTTP_HOST='localhost:8000')
print(f"Status: {response.status_code}")
if response.status_code == 200:
    if hasattr(response, 'templates') and response.templates:
        print(f"Template: {response.templates[0].name}")
    if hasattr(response, 'context') and response.context:
        results = response.context.get('results', [])
        print(f"Results count: {len(results)}")
        if results:
            print(f"First result: {results[0]}")
    else:
        print("Context: N/A")

print("\n=== Teste 3: GET /ops/telemetry/drilldown/ (Drill-down) ===")
params = {
    'tenant_slug': 'uberlandia-medical-center',
    'sensor_id': 'temp_01',
    'limit': 50
}
response = client.get('/ops/telemetry/drilldown/', params, HTTP_HOST='localhost:8000')
print(f"Status: {response.status_code}")
if response.status_code == 200:
    if hasattr(response, 'templates') and response.templates:
        print(f"Template: {response.templates[0].name}")
    if hasattr(response, 'context') and response.context:
        results = response.context.get('results', [])
        stats = response.context.get('stats')
        print(f"Raw readings count: {len(results)}")
        print(f"Stats: {stats}")
    else:
        print("Context: N/A")

print("\n=== Teste 4: POST /ops/telemetry/export/ (CSV Export) ===")
params = {
    'tenant_slug': 'uberlandia-medical-center',
    'sensor_id': 'temp_01',
    'limit': 100
}
response = client.post('/ops/telemetry/export/', params, HTTP_HOST='localhost:8000')
print(f"Status: {response.status_code}")
print(f"Content-Type: {response.get('Content-Type')}")
if response.status_code == 200:
    lines = response.content.decode('utf-8').split('\n')
    print(f"CSV lines: {len(lines)}")
    print(f"Header: {lines[0]}")
    if len(lines) > 1:
        print(f"First row: {lines[1]}")

print("\n✅ Todos os testes de endpoint concluídos!")
