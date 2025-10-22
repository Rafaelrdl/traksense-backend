"""
Script para testar o sistema de status online/offline simulando um sensor antigo.
"""
import os
import sys
import django
from datetime import timedelta

# Setup Django
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.utils import timezone
from django_tenants.utils import schema_context
from apps.assets.models import Sensor, Device
from apps.assets.tasks import check_sensors_online_status, update_device_online_status

TENANT_SCHEMA = 'umc'

print(f"\n{'='*80}")
print(f"SIMULAÇÃO: Sensor Offline")
print(f"{'='*80}\n")

with schema_context(TENANT_SCHEMA):
    # Buscar primeiro sensor
    sensor = Sensor.objects.filter(is_active=True).first()
    
    if not sensor:
        print("❌ Nenhum sensor encontrado!")
        sys.exit(1)
    
    print(f"📍 Sensor selecionado: {sensor.tag}")
    print(f"   Device: {sensor.device.name}")
    print(f"   Status atual: {'ONLINE' if sensor.is_online else 'OFFLINE'}")
    print(f"   Last Reading At: {sensor.last_reading_at}")
    print()
    
    # SIMULAÇÃO: Alterar last_reading_at para 2 horas atrás
    print("🕐 Simulando sensor sem dados há 2 horas...")
    old_time = timezone.now() - timedelta(hours=2)
    sensor.last_reading_at = old_time
    sensor.save(update_fields=['last_reading_at'])
    print(f"   ✅ Last Reading At alterado para: {sensor.last_reading_at}")
    print()
    
    # Executar verificação
    print("🔍 Executando verificação de status...")
    result_sensors = check_sensors_online_status()
    print()
    
    # Atualizar device
    print("🔍 Atualizando status do device...")
    result_devices = update_device_online_status()
    print()
    
    # Verificar resultado
    sensor.refresh_from_db()
    device = sensor.device
    device.refresh_from_db()
    
    print(f"{'='*80}")
    print("RESULTADO APÓS VERIFICAÇÃO")
    print(f"{'='*80}")
    print(f"Sensor: {sensor.tag}")
    print(f"  - is_online: {sensor.is_online} {'✅' if not sensor.is_online else '❌ DEVERIA SER FALSE'}")
    print(f"  - last_reading_at: {sensor.last_reading_at}")
    print()
    print(f"Device: {device.name}")
    print(f"  - status: {device.status} {'✅' if device.status == 'OFFLINE' else '❌'}")
    print()
    
    # Verificar todos os sensores do device
    all_sensors = Sensor.objects.filter(device=device, is_active=True)
    print(f"Todos os sensores do device ({all_sensors.count()}):")
    for s in all_sensors:
        status_icon = '🟢' if s.is_online else '🔴'
        print(f"  {status_icon} {s.tag}: {s.last_reading_at}")
    print()
    
    # Restaurar sensor para online
    print("🔄 Restaurando sensor para ONLINE...")
    sensor.last_reading_at = timezone.now()
    sensor.is_online = True
    sensor.save(update_fields=['last_reading_at', 'is_online'])
    print("   ✅ Sensor restaurado")
    print()
    
    # Atualizar device novamente
    print("🔍 Atualizando device novamente...")
    update_device_online_status()
    device.refresh_from_db()
    print(f"   ✅ Device status: {device.status}")
    print()

print(f"{'='*80}")
print("✅ Simulação concluída!")
print(f"{'='*80}\n")
