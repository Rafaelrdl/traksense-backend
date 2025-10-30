#!/usr/bin/env python3
"""
Script para verificar dados de telemetria salvos no banco
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.db import connection
from apps.tenants.models import Tenant
from apps.ingest.models import Telemetry

def check_telemetry():
    print("=" * 60)
    print("🔍 Verificando Telemetria no Banco de Dados")
    print("=" * 60)
    
    # Get tenant
    connection.set_schema_to_public()
    try:
        tenant = Tenant.objects.get(slug='umc')
        print(f"\n✅ Tenant encontrado: {tenant.name} (slug: {tenant.slug})")
    except Tenant.DoesNotExist:
        print("\n❌ Tenant 'umc' não encontrado!")
        return
    
    # Switch to tenant schema
    connection.set_tenant(tenant)
    
    # Query telemetry for GW-1760908415
    device_id = "GW-1760908415"
    print(f"\n📊 Buscando telemetria para device: {device_id}")
    print("-" * 60)
    
    # Get all telemetry records
    telemetry_records = Telemetry.objects.filter(
        device_id=device_id
    ).order_by('-timestamp')[:20]
    
    print(f"\n📈 Total de registros encontrados: {telemetry_records.count()}")
    
    if telemetry_records.exists():
        print("\n🔎 Últimos 10 registros:")
        print("-" * 60)
        for i, record in enumerate(telemetry_records[:10], 1):
            print(f"\n{i}. Registro ID: {record.id}")
            print(f"   Device: {record.device_id}")
            print(f"   Sensor: {record.sensor_id}")
            print(f"   Tipo: {record.sensor_type}")
            print(f"   Valor: {record.value} {record.unit}")
            print(f"   Timestamp: {record.timestamp}")
            if record.labels:
                print(f"   Labels: {record.labels}")
    else:
        print("\n⚠️  Nenhum registro encontrado!")
    
    # Check for specific sensors
    print("\n" + "=" * 60)
    print("🔍 Verificando sensores específicos:")
    print("-" * 60)
    
    target_sensors = [
        'TEMP-AMB-001',
        'HUM-001', 
        'TEMP-WATER-IN-001',
        'TEMP-WATER-OUT-001'
    ]
    
    for sensor_id in target_sensors:
        count = Telemetry.objects.filter(
            device_id=device_id,
            sensor_id=sensor_id
        ).count()
        
        if count > 0:
            latest = Telemetry.objects.filter(
                device_id=device_id,
                sensor_id=sensor_id
            ).order_by('-timestamp').first()
            print(f"\n✅ {sensor_id}: {count} registros")
            print(f"   Último valor: {latest.value} {latest.unit} em {latest.timestamp}")
        else:
            print(f"\n❌ {sensor_id}: Nenhum registro")
    
    print("\n" + "=" * 60)

if __name__ == '__main__':
    check_telemetry()
