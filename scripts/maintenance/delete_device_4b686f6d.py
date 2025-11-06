#!/usr/bin/env python
"""
Deletar Device 4b686f6d70107115 e suas variáveis/sensores
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
django.setup()

from django_tenants.utils import schema_context
from apps.assets.models import Device, Sensor

def delete_device_and_sensors():
    """Delete device and all its sensors"""
    mqtt_client_id = '4b686f6d70107115'
    
    print("\n" + "="*80)
    print(f"🗑️  DELETANDO Device: {mqtt_client_id}")
    print("="*80 + "\n")
    
    with schema_context('umc'):
        try:
            # Find device
            device = Device.objects.get(mqtt_client_id=mqtt_client_id)
            device_id = device.id
            device_name = device.name
            
            print(f"✅ Device encontrado:")
            print(f"   - ID: {device_id}")
            print(f"   - Nome: {device_name}")
            print(f"   - MQTT Client ID: {device.mqtt_client_id}")
            print(f"   - Tipo: {device.device_type}")
            print(f"   - Status: {device.status}")
            
            # Find sensors
            sensors = Sensor.objects.filter(device=device)
            sensor_count = sensors.count()
            
            print(f"\n📊 Sensores associados: {sensor_count}")
            for i, sensor in enumerate(sensors, 1):
                print(f"   {i}. {sensor.tag} (ID: {sensor.id})")
            
            # Confirm deletion
            print(f"\n⚠️  DELETANDO {sensor_count} sensores...")
            deleted_sensors = sensors.delete()
            print(f"   ✅ {deleted_sensors[0]} sensores deletados")
            
            print(f"\n⚠️  DELETANDO device {device_name}...")
            device.delete()
            print(f"   ✅ Device deletado")
            
            print("\n" + "="*80)
            print("✅ DELEÇÃO COMPLETA!")
            print("="*80 + "\n")
            
            # Verificar se ainda existem devices
            remaining_devices = Device.objects.all().count()
            print(f"📊 Devices restantes no sistema: {remaining_devices}\n")
            
        except Device.DoesNotExist:
            print(f"❌ ERROR: Device com mqtt_client_id='{mqtt_client_id}' não encontrado")
        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()


if __name__ == '__main__':
    delete_device_and_sensors()
