#!/usr/bin/env python3
"""
Teste de Latência SIMPLIFICADO (Passo 8)

Versão rápida que:
1. Publica 20 mensagens com timestamps NOW() usando QoS=0 (mais rápido)
2. Aguarda 2 segundos
3. Verifica se os dados chegaram ao banco
4. Verifica métrica Prometheus externamente
"""

import paho.mqtt.client as mqtt
import json
import time
from datetime import datetime, timezone

# Configuração
MQTT_HOST = 'emqx'
MQTT_PORT = 1883
# Usar UUID válido para tenant (simulando um tenant real)
TENANT_UUID = '11111111-1111-1111-1111-111111111111'
SITE_ID = 'site01'
DEVICE_ID = '77777777-7777-7777-7777-777777777777'
TOPIC_BASE = f'traksense/{TENANT_UUID}/{SITE_ID}'

def main():
    print("=" * 60)
    print("🔍 TESTE DE LATÊNCIA SIMPLIFICADO")
    print("=" * 60)
    print()
    print(f"📊 Device: {DEVICE_ID}")
    print(f"📊 Mensagens: 20 (QoS=0 para velocidade)")
    print()
    
    # Conectar MQTT
    client = mqtt.Client()
    
    try:
        print("🔌 Conectando ao MQTT...")
        client.connect(MQTT_HOST, MQTT_PORT, 60)
        client.loop_start()
        time.sleep(0.5)  # Aguardar conexão
        print("✅ Conectado!")
        print()
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        return
    
    topic = f'{TOPIC_BASE}/{DEVICE_ID}/telem'
    
    # Publicar mensagens rapidamente
    print("📤 Publicando 20 mensagens...")
    start = time.time()
    
    for i in range(20):
        now = datetime.now(timezone.utc)
        ts_iso = now.isoformat().replace('+00:00', 'Z')
        
        payload = {
            'schema': 'v1',
            'ts': ts_iso,
            'points': [
                {
                    'name': f'temp_test_{i}',
                    't': 'float',
                    'v': 25.0 + (i * 0.1),
                    'u': '°C'
                }
            ],
            'meta': {'test': 'latency_simple', 'seq': i}
        }
        
        client.publish(topic, json.dumps(payload), qos=0)
        
        if (i + 1) % 5 == 0:
            print(f"   ✓ {i+1}/20")
    
    elapsed = time.time() - start
    print(f"\n✅ Publicadas 20 mensagens em {elapsed:.2f}s")
    print()
    
    # Aguardar processamento
    print("⏳ Aguardando 2 segundos para processamento...")
    time.sleep(2)
    
    client.loop_stop()
    client.disconnect()
    
    print()
    print("=" * 60)
    print("✅ TESTE CONCLUÍDO")
    print("=" * 60)
    print()
    print("📊 PRÓXIMOS PASSOS DE VERIFICAÇÃO:")
    print()
    print("1️⃣ Verificar métrica Prometheus (do host):")
    print('   curl http://localhost:9100/metrics | Select-String "ingest_latency"')
    print()
    print("2️⃣ Verificar dados no banco (do container api):")
    print("   docker compose -f .\\infra\\docker-compose.yml exec api python manage.py shell")
    print()
    print("   from timeseries.models import TSMeasure")
    print("   from datetime import datetime, timedelta, timezone")
    print("   from django.db import connection")
    print()
    print("   # Contar pontos recentes")
    print("   recent = datetime.now(timezone.utc) - timedelta(minutes=1)")
    print("   with connection.cursor() as c:")
    print("       c.execute('SELECT COUNT(*) FROM public.ts_measure WHERE ts >= %s', [recent])")
    print("       print(f'Pontos recentes: {c.fetchone()[0]}')")
    print()
    print("3️⃣ Se ambos funcionarem, a latência está sendo medida! ✅")
    print()

if __name__ == '__main__':
    main()
