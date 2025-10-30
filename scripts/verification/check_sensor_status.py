"""
Verificar status atual dos sensores e quando foi a última leitura
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
from apps.assets.models import Sensor

TENANT_SCHEMA = 'umc'

print(f"\n{'='*80}")
print(f"DIAGNÓSTICO DE STATUS DOS SENSORES")
print(f"{'='*80}\n")

now = timezone.now()
threshold_1h = now - timedelta(hours=1)

print(f"⏰ Hora atual: {now}")
print(f"⏰ Threshold (1h atrás): {threshold_1h}")
print()

with schema_context(TENANT_SCHEMA):
    sensors = Sensor.objects.filter(is_active=True)
    
    print(f"📊 Total de sensores: {sensors.count()}")
    print()
    
    for sensor in sensors:
        last_reading = sensor.last_reading_at
        
        if last_reading:
            diff = now - last_reading
            diff_minutes = diff.total_seconds() / 60
            diff_hours = diff.total_seconds() / 3600
            
            should_be_online = last_reading >= threshold_1h
            is_correct = sensor.is_online == should_be_online
            
            status_icon = '🟢' if sensor.is_online else '🔴'
            correct_icon = '✅' if is_correct else '❌'
            
            print(f"{status_icon} {sensor.tag}")
            print(f"   Last Reading: {last_reading}")
            print(f"   Há {diff_minutes:.1f} minutos ({diff_hours:.2f} horas)")
            print(f"   is_online: {sensor.is_online}")
            print(f"   Deveria ser ONLINE? {should_be_online}")
            print(f"   Status correto? {is_correct} {correct_icon}")
            print()
        else:
            print(f"🔴 {sensor.tag}")
            print(f"   ⚠️  SEM LEITURAS (last_reading_at = None)")
            print(f"   is_online: {sensor.is_online}")
            print(f"   Deveria ser OFFLINE? True ✅")
            print()

print(f"{'='*80}")
print("RESUMO DA REGRA:")
print(f"{'='*80}")
print(f"✅ ONLINE:  last_reading_at >= {threshold_1h}")
print(f"❌ OFFLINE: last_reading_at <  {threshold_1h}")
print(f"   (ou last_reading_at = None)")
print()
