#!/usr/bin/env python3
"""
Teste direto do endpoint /ingest com header X-Tenant correto
"""
import requests
import json
from datetime import datetime, timezone

# Payload EMQX format (correto conforme IngestView espera)
payload = {
    "client_id": "GW-1760908415",
    "topic": "tenants/umc/GW-1760908415",
    "payload": {
        "device_id": "GW-1760908415",
        "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        "sensors": [
            {
                "sensor_id": "TEMP-AMB-001",
                "type": "temperature",
                "value": 23.5,
                "unit": "C",
                "labels": {
                    "type": "temperature",
                    "description": "Temperatura Ambiente",
                    "location": "Sala de Maquinas"
                }
            },
            {
                "sensor_id": "HUM-001",
                "type": "humidity",
                "value": 65.2,
                "unit": "percent",
                "labels": {
                    "type": "humidity",
                    "description": "Umidade Relativa",
                    "location": "Sala de Maquinas"
                }
            },
            {
                "sensor_id": "TEMP-WATER-IN-001",
                "type": "temperature",
                "value": 12.5,
                "unit": "C",
                "labels": {
                    "type": "temperature",
                    "description": "Temperatura Entrada Agua",
                    "location": "Entrada Chiller"
                }
            },
            {
                "sensor_id": "TEMP-WATER-OUT-001",
                "type": "temperature",
                "value": 7.2,
                "unit": "C",
                "labels": {
                    "type": "temperature",
                    "description": "Temperatura Saida Agua",
                    "location": "Saida Chiller"
                }
            }
        ]
    },
    "ts": int(datetime.now(timezone.utc).timestamp() * 1000)
}

print("=" * 60)
print("🧪 Teste Direto do Endpoint /ingest")
print("=" * 60)
print(f"\n📦 Payload:")
print(json.dumps(payload, indent=2, ensure_ascii=False))

headers = {
    "Content-Type": "application/json",
    "X-Tenant": "umc"
}

print(f"\n📋 Headers:")
for key, value in headers.items():
    print(f"   {key}: {value}")

print(f"\n🚀 Enviando POST para http://localhost:8000/ingest...")

try:
    response = requests.post(
        "http://localhost:8000/ingest",
        json=payload,
        headers=headers,
        timeout=10
    )
    
    print(f"\n✅ Status Code: {response.status_code}")
    print(f"📝 Response: {response.text}")
    
    if response.status_code == 200:
        print("\n🎉 SUCESSO! Telemetria processada.")
        print("\n🔍 Verifique:")
        print("   1. http://umc.localhost:5000/sensors")
        print("   2. Aguarde ~5 segundos (auto-refresh)")
        print("   3. Procure: TEMP-AMB-001, HUM-001, TEMP-WATER-IN-001, TEMP-WATER-OUT-001")
    else:
        print(f"\n❌ ERRO: {response.status_code}")
        
except Exception as e:
    print(f"\n❌ Erro na requisição: {e}")

print("\n" + "=" * 60)
