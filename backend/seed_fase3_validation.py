#!/usr/bin/env python
"""
Script para seed completo de dados de teste - Fase 3 Validation
Cria tenant, device template, device para testes de provisioning EMQX
"""
import os
import django
import uuid
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.tenancy.models import Client, Domain
from apps.devices.models import DeviceTemplate, PointTemplate, Device, Point

def main():
    print("="*70)
    print("🌱 SEED DADOS DE TESTE - FASE 3 VALIDATION")
    print("="*70)
    
    # =========================================================================
    # 1. Criar Tenant test_alpha
    # =========================================================================
    print("\n📦 Step 1: Criando tenant test_alpha...")
    tenant, created = Client.objects.get_or_create(
        schema_name='test_alpha',
        defaults={
            'name': 'Test Alpha Corp',
            'is_active': True
        }
    )
    if created:
        print(f"   ✅ Tenant criado: {tenant.schema_name}")
    else:
        print(f"   ℹ️  Tenant já existe: {tenant.schema_name}")
    
    # Criar domínio
    domain, created = Domain.objects.get_or_create(
        domain='test-alpha.localhost',
        defaults={'tenant': tenant, 'is_primary': True}
    )
    if created:
        print(f"   ✅ Domain criado: {domain.domain}")
    else:
        print(f"   ℹ️  Domain já existe: {domain.domain}")
    
    # =========================================================================
    # 2. Criar Device Template (chiller_v1)
    # =========================================================================
    print("\n📦 Step 2: Criando device template chiller_v1...")
    
    # Usar connection.set_tenant para trabalhar no schema do tenant
    from django.db import connection
    connection.set_tenant(tenant)
    
    template, created = DeviceTemplate.objects.get_or_create(
        code='chiller_v1',
        version=1,
        defaults={
            'name': 'Chiller Genérico v1',
            'description': 'Template de chiller genérico para testes EMQX provisioning'
        }
    )
    if created:
        print(f"   ✅ Template criado: {template.code}")
    else:
        print(f"   ℹ️  Template já existe: {template.code}")
    
    # =========================================================================
    # 3. Criar Device (sem point templates por enquanto - foco em provisioning EMQX)
    # =========================================================================
    print("\n📦 Step 3: Criando device de teste...")
    
    device_id = 'a1b2c3d4-e5f6-7890-1234-567890abcdef'  # ID fixo para testes
    
    device, created = Device.objects.get_or_create(
        id=device_id,
        defaults={
            'name': 'Chiller Factory SP - Zona 1',
            'template': template
        }
    )
    if created:
        print(f"   ✅ Device criado: {device.id} | {device.name}")
    else:
        print(f"   ℹ️  Device já existe: {device.id} | {device.name}")
    
    #  Não criamos points - o foco é validar provisioning EMQX
    
    # =========================================================================
    # Resumo Final
    # =========================================================================
    print("\n" + "="*70)
    print("✅ SEED CONCLUÍDO COM SUCESSO!")
    print("="*70)
    print(f"\n📊 Resumo:")
    print(f"   Tenant:          {tenant.schema_name}")
    print(f"   Device Template: {template.code} v{template.version}")
    print(f"   Device ID:       {device.id}")
    print(f"   Device Name:     {device.name}")
    
    print(f"\n🔧 Próximo passo: Provisionar device no EMQX")
    print(f"\n   docker compose exec api python manage.py tenant_command provision_emqx \\")
    print(f"       {device.id} factory-sp --schema={tenant.schema_name}")
    print()

if __name__ == '__main__':
    main()
