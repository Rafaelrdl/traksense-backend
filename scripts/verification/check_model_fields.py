"""
Script para identificar campos reais dos models e gerar serializers corretos
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')
django.setup()

from apps.assets.models import Site, Asset, Device, Sensor

def get_model_fields(model):
    """Retorna lista de campos de um model Django"""
    fields = []
    for field in model._meta.get_fields():
        if field.concrete and not field.many_to_many:
            fields.append(field.name)
    return sorted(fields)

print("\n" + "="*70)
print("CAMPOS REAIS DOS MODELS")
print("="*70)

print("\n1. Site:")
site_fields = get_model_fields(Site)
for field in site_fields:
    print(f"   - {field}")

print("\n2. Asset:")
asset_fields = get_model_fields(Asset)
for field in asset_fields:
    print(f"   - {field}")

print("\n3. Device:")
device_fields = get_model_fields(Device)
for field in device_fields:
    print(f"   - {field}")

print("\n4. Sensor:")
sensor_fields = get_model_fields(Sensor)
for field in sensor_fields:
    print(f"   - {field}")

print("\n" + "="*70 + "\n")
