#!/usr/bin/env python
"""Script para testar dados disponíveis no painel Ops."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django_tenants.utils import schema_context
from apps.tenants.models import Tenant
from apps.ingest.models import Reading

# Listar tenants
tenants = Tenant.objects.exclude(schema_name='public')
print(f"\n=== Tenants Disponíveis ({tenants.count()}) ===")
for tenant in tenants:
    print(f"  - Schema: {tenant.schema_name}")
    print(f"    Nome: {tenant.name}")
    print(f"    Slug: {tenant.slug}")
    
    # Contar readings no tenant
    with schema_context(tenant.schema_name):
        count = Reading.objects.count()
        print(f"    Readings: {count}")
        
        if count > 0:
            # Mostrar sensor_ids únicos
            sensor_ids = Reading.objects.values_list('sensor_id', flat=True).distinct()
            print(f"    Sensors: {list(sensor_ids)[:5]}")  # Primeiros 5
            
            # Amostra
            sample = Reading.objects.first()
            print(f"    Sample: sensor={sample.sensor_id}, value={sample.value}, ts={sample.ts}")
    print()
