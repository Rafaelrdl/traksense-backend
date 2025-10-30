#!/usr/bin/env python
"""
Script para verificar device e sensores criados automaticamente.
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django_tenants.utils import schema_context
from apps.tenants.models import Tenant
from apps.assets.models import Site, Asset, Device, Sensor

print("=" * 70)
print("🔍 VERIFICANDO AUTO-CRIAÇÃO DE ASSETS E DEVICES")
print("=" * 70)

tenant = Tenant.objects.get(schema_name='umc')

with schema_context(tenant.schema_name):
    # Verificar site
    site = Site.objects.filter(name='Uberlândia Medical Center').first()
    if site:
        print(f"\n✅ Site encontrado: {site.name} (ID: {site.id})")
    else:
        print("\n❌ Site 'Uberlândia Medical Center' não encontrado!")
        sys.exit(1)
    
    # Verificar asset
    asset = Asset.objects.filter(tag='CHILLER-001').first()
    if asset:
        print(f"✅ Asset encontrado: {asset.tag} - {asset.name}")
        print(f"   Site: {asset.site.name}")
        print(f"   Tipo: {asset.asset_type}")
        print(f"   Status: {asset.status}")
    else:
        print("❌ Asset 'CHILLER-001' não encontrado!")
        sys.exit(1)
    
    # Verificar device
    device = Device.objects.filter(mqtt_client_id='4b686f6d70107115').first()
    if device:
        print(f"\n✅ Device encontrado:")
        print(f"   ID: {device.id}")
        print(f"   Nome: {device.name}")
        print(f"   MQTT Client ID: {device.mqtt_client_id}")
        print(f"   Serial Number: {device.serial_number}")
        print(f"   Asset: {device.asset.tag if device.asset else 'N/A'}")
        print(f"   Tipo: {device.device_type}")
        print(f"   Status: {device.status}")
        print(f"   Online: {device.is_online}")
        print(f"   Last Seen: {device.last_seen}")
    else:
        print("❌ Device '4b686f6d70107115' não encontrado!")
        sys.exit(1)
    
    # Verificar sensores
    sensors = Sensor.objects.filter(device=device)
    print(f"\n✅ {sensors.count()} Sensor(es) encontrado(s):")
    for sensor in sensors:
        print(f"\n   • Tag: {sensor.tag}")
        print(f"     Nome: {sensor.name}")
        print(f"     Tipo: {sensor.metric_type}")
        print(f"     Unidade: {sensor.unit}")
        print(f"     Último Valor: {sensor.last_value}")
        print(f"     Última Leitura: {sensor.last_reading_at}")
        print(f"     Online: {sensor.is_online}")
    
    # Verificar readings
    from apps.ingest.models import Reading
    readings = Reading.objects.filter(device_id='4b686f6d70107115').order_by('-ts')[:5]
    print(f"\n✅ {readings.count()} Última(s) reading(s):")
    for reading in readings:
        print(f"   • {reading.sensor_id}: {reading.value} @ {reading.ts}")

print("\n" + "=" * 70)
print("✅ Verificação concluída!")
print("=" * 70)
