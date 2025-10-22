"""
Script para publicar mensagens MQTT de teste com valores variáveis.
Útil para testar o auto-refresh do frontend.
"""
import os
import sys
import django
import json
import time
from datetime import datetime

# Setup Django
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.utils import timezone

# Configurações
TENANT = 'umc'
SITE_NAME = 'Uberlândia Medical Center'
ASSET_TAG = 'CHILLER-001'
DEVICE_ID = '4b686f6d70107115'

# Valores iniciais
TEMP_BASE = 25.0
HUMID_BASE = 60.0
TEMP_SUPPLY_BASE = 30.0
RSSI_BASE = -61.0

print(f"\n{'='*80}")
print(f"TESTE DE AUTO-REFRESH - Publicação MQTT com Valores Variáveis")
print(f"{'='*80}\n")

print(f"📍 Configuração:")
print(f"   Tenant: {TENANT}")
print(f"   Site: {SITE_NAME}")
print(f"   Asset: {ASSET_TAG}")
print(f"   Device: {DEVICE_ID}")
print()

# Simular 5 publicações com valores diferentes
for i in range(1, 6):
    print(f"{'='*80}")
    print(f"Publicação #{i} de 5")
    print(f"{'='*80}")
    
    # Variar valores
    temp_var = (i - 1) * 0.5
    humid_var = (i - 1) * 2
    
    temp = round(TEMP_BASE + temp_var, 2)
    humid = round(HUMID_BASE + humid_var, 1)
    temp_supply = round(TEMP_SUPPLY_BASE + temp_var, 2)
    rssi = RSSI_BASE - i
    
    # Criar payload SenML
    payload = [
        {
            "bn": f"{DEVICE_ID}_",
            "bt": int(time.time()),
            "bu": "celsius",
            "n": "A_temp",
            "v": temp,
            "t": 0
        },
        {
            "bn": f"{DEVICE_ID}_",
            "bt": int(time.time()),
            "bu": "percent_rh",
            "n": "A_humid",
            "v": humid,
            "t": 0
        },
        {
            "bn": "",
            "bt": int(time.time()),
            "n": "283286b20a000036",
            "u": "celsius",
            "v": temp_supply,
            "t": 0
        },
        {
            "bn": f"{DEVICE_ID}_",
            "bt": int(time.time()),
            "bu": "dBW",
            "n": "rssi",
            "v": rssi,
            "t": 0
        }
    ]
    
    print(f"\n📊 Valores desta publicação:")
    print(f"   🌡️  Temperatura Ambiente: {temp}°C")
    print(f"   💧 Umidade: {humid}%")
    print(f"   🌡️  Temperatura Insuflamento: {temp_supply}°C")
    print(f"   📡 RSSI: {rssi} dBW")
    print()
    
    # Montar request para o endpoint de ingest
    topic = f"tenants/{TENANT}/sites/{SITE_NAME}/assets/{ASSET_TAG}/telemetry"
    
    request_data = {
        'topic': topic,
        'payload': json.dumps(payload),
        'timestamp': int(time.time() * 1000),  # milliseconds
        'qos': 0,
        'clientid': DEVICE_ID
    }
    
    # Fazer POST para o endpoint de ingest
    import requests
    
    url = "http://localhost:8000/api/ingest/emqx/"
    headers = {
        'Content-Type': 'application/json'
    }
    
    print(f"📤 Enviando para: {url}")
    print(f"   Topic: {topic}")
    
    try:
        response = requests.post(url, json=request_data, headers=headers)
        
        if response.status_code == 202:
            print(f"✅ Mensagem aceita pelo backend (HTTP {response.status_code})")
            print(f"   Resposta: {response.json()}")
        else:
            print(f"❌ Erro HTTP {response.status_code}")
            print(f"   Resposta: {response.text}")
    except Exception as e:
        print(f"❌ Erro ao enviar mensagem: {str(e)}")
    
    print()
    
    if i < 5:
        wait_time = 10
        print(f"⏳ Aguardando {wait_time} segundos antes da próxima publicação...")
        print(f"   (Frontend deve atualizar em até 30s após cada publicação)")
        print()
        time.sleep(wait_time)

print(f"{'='*80}")
print("✅ TESTE CONCLUÍDO!")
print(f"{'='*80}\n")

print("📊 Resumo:")
print(f"   - 5 mensagens MQTT publicadas")
print(f"   - Valores variaram de:")
print(f"     • Temperatura: {TEMP_BASE}°C → {round(TEMP_BASE + 4 * 0.5, 2)}°C")
print(f"     • Umidade: {HUMID_BASE}% → {round(HUMID_BASE + 4 * 2, 1)}%")
print(f"     • RSSI: {RSSI_BASE} → {RSSI_BASE - 5} dBW")
print()

print("🔍 O que observar no frontend:")
print("   1. Abra: http://umc.localhost:5173")
print("   2. Vá para página 'Sensores'")
print("   3. Aguarde até 30 segundos")
print("   4. Valores devem atualizar automaticamente")
print("   5. Timestamp 'Atualizado às' deve mudar")
print("   6. Console deve mostrar: '✅ Telemetria atualizada automaticamente'")
print()

print("💡 Dica:")
print("   - Se não atualizar em 30s, clique no botão '🔄 Atualizar'")
print("   - Verifique console (F12) para ver logs do polling")
print("   - Network tab deve mostrar GET requests a cada 30s")
print()
