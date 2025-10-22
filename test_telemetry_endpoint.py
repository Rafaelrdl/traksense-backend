"""
Script para verificar se o endpoint de telemetria está retornando dados corretamente
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django_tenants.utils import schema_context
from apps.assets.models import Device, Sensor
from apps.ingest.models import Reading

# Tenant schema
TENANT_SCHEMA = 'umc'
DEVICE_MQTT_ID = '4b686f6d70107115'

print(f"\n{'='*80}")
print(f"VERIFICANDO TELEMETRIA PARA DEVICE: {DEVICE_MQTT_ID}")
print(f"{'='*80}\n")

with schema_context(TENANT_SCHEMA):
    # 1. Buscar device
    try:
        device = Device.objects.get(mqtt_client_id=DEVICE_MQTT_ID)
        print(f"✅ Device encontrado:")
        print(f"   - ID: {device.id}")
        print(f"   - Nome: {device.name}")
        print(f"   - MQTT Client ID: {device.mqtt_client_id}")
        print(f"   - Status: {device.status}")
        print(f"   - Last Seen: {device.last_seen}")
        print(f"   - Asset: {device.asset.tag if device.asset else 'N/A'}")
        print()
    except Device.DoesNotExist:
        print(f"❌ Device com mqtt_client_id='{DEVICE_MQTT_ID}' não encontrado!")
        sys.exit(1)
    
    # 2. Buscar sensores do device
    sensors = Sensor.objects.filter(device=device)
    print(f"📊 Sensores encontrados: {sensors.count()}")
    print()
    
    for sensor in sensors:
        print(f"   Sensor: {sensor.tag}")
        print(f"   - Metric Type: {sensor.metric_type}")
        print(f"   - Unit: {sensor.unit}")
        print(f"   - Last Value: {sensor.last_value}")
        print(f"   - Last Reading At: {sensor.last_reading_at}")
        print(f"   - Is Online: {sensor.is_online}")
        print()
    
    # 3. Verificar readings
    readings = Reading.objects.filter(device_id=device.mqtt_client_id).order_by('-ts')[:10]
    print(f"📈 Últimas {readings.count()} readings:")
    print()
    
    for reading in readings:
        print(f"   - Sensor: {reading.sensor_id}")
        print(f"     Value: {reading.value}")
        print(f"     Timestamp: {reading.ts}")
        print()
    
    # 4. Simular resposta do endpoint de telemetria
    print(f"\n{'='*80}")
    print("SIMULANDO RESPOSTA DO ENDPOINT /api/telemetry/devices/{mqtt_client_id}/summary/")
    print(f"{'='*80}\n")
    
    summary = {
        'device': {
            'id': device.id,
            'name': device.name,
            'mqtt_client_id': device.mqtt_client_id,
            'status': device.status,
            'last_seen': str(device.last_seen) if device.last_seen else None,
        },
        'sensors': [],
        'total_sensors': sensors.count(),
        'online_sensors': sensors.filter(is_online=True).count(),
    }
    
    for sensor in sensors:
        summary['sensors'].append({
            'id': sensor.id,
            'tag': sensor.tag,
            'metric_type': sensor.metric_type,
            'unit': sensor.unit,
            'last_value': sensor.last_value,
            'last_reading_at': str(sensor.last_reading_at) if sensor.last_reading_at else None,
            'is_online': sensor.is_online,
        })
    
    import json
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    
    # 5. Verificar se há algum problema
    print(f"\n{'='*80}")
    print("DIAGNÓSTICO")
    print(f"{'='*80}\n")
    
    issues = []
    
    if sensors.count() == 0:
        issues.append("❌ Nenhum sensor encontrado para este device")
    
    if all(s.last_value is None for s in sensors):
        issues.append("⚠️  Todos os sensores têm last_value = None")
    
    if all(s.last_reading_at is None for s in sensors):
        issues.append("⚠️  Todos os sensores têm last_reading_at = None")
    
    if readings.count() == 0:
        issues.append("❌ Nenhuma reading encontrada para este device")
    
    if device.status != 'ONLINE':
        issues.append(f"⚠️  Device status é '{device.status}' (deveria ser 'ONLINE')")
    
    if not device.last_seen:
        issues.append("⚠️  Device last_seen é None")
    
    if issues:
        print("Problemas encontrados:")
        for issue in issues:
            print(f"  {issue}")
    else:
        print("✅ Tudo parece estar OK! O endpoint de telemetria deveria funcionar.")
    
    print()
