"""
Script para criar alertas de exemplo no backend
"""
import requests
import json
from datetime import datetime, timedelta

# Configuração
BASE_URL = 'http://umc.localhost:8000'
LOGIN_URL = f'{BASE_URL}/api/auth/login/'
ALERTS_URL = f'{BASE_URL}/api/alerts/alerts/'

# Credenciais
USERNAME = 'admin'
PASSWORD = 'admin123'

def login():
    """Fazer login e obter token"""
    response = requests.post(LOGIN_URL, json={
        'username_or_email': USERNAME,
        'password': PASSWORD
    })
    
    if response.status_code == 200:
        return response.json()['access']
    else:
        print(f'❌ Erro no login: {response.status_code}')
        print(response.text)
        return None

def create_sample_alert(token, rule_id, severity, message):
    """Criar um alerta de exemplo"""
    headers = {'Authorization': f'Bearer {token}'}
    
    # Nota: A API de alertas não permite criação direta
    # Alertas são gerados automaticamente pelas regras
    # Este script é apenas para referência
    
    print(f'ℹ️  Alertas são gerados automaticamente pelas regras')
    print(f'   Para criar alertas, publique dados de telemetria que disparem as regras')

def main():
    print('🔐 Fazendo login...')
    token = login()
    
    if not token:
        return
    
    print('✅ Login realizado com sucesso!\n')
    
    # Listar regras existentes
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(f'{BASE_URL}/api/alerts/rules/', headers=headers)
    
    if response.status_code == 200:
        rules = response.json()['results']
        print(f'📋 Regras cadastradas: {len(rules)}')
        for rule in rules:
            print(f'   - ID {rule["id"]}: {rule["name"]} (Severity: {rule["severity"]})')
        print()
    
    # Listar alertas existentes
    response = requests.get(ALERTS_URL, headers=headers)
    
    if response.status_code == 200:
        alerts = response.json()['results']
        print(f'🚨 Alertas existentes: {len(alerts)}')
        for alert in alerts:
            status = 'Ativo' if alert['is_active'] else 'Resolvido'
            print(f'   - ID {alert["id"]}: {alert["rule_name"]} ({status})')
            print(f'     Mensagem: {alert["message"]}')
            print(f'     Equipamento: {alert["equipment_name"]}')
            print()
    else:
        print(f'❌ Erro ao listar alertas: {response.status_code}')
    
    print('\n💡 Para gerar alertas:')
    print('   1. Certifique-se de que há regras ativas configuradas')
    print('   2. Publique dados de telemetria via MQTT que atendam as condições das regras')
    print('   3. O sistema gerará alertas automaticamente')

if __name__ == '__main__':
    main()
