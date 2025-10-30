#!/usr/bin/env python
"""
Script para criar Domain 'umc.api' apontando para tenant UMC.
Isso permite que EMQX envie requests com Host: umc.api:8000
e o django-tenants roteie automaticamente para o schema correto.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.tenants.models import Tenant, Domain

# Buscar tenant UMC
tenant = Tenant.objects.get(slug='uberlandia-medical-center')

# Criar domain umc.api
domain, created = Domain.objects.get_or_create(
    domain='umc.api',
    defaults={
        'tenant': tenant,
        'is_primary': False
    }
)

if created:
    print(f"✅ Domain 'umc.api' criado com sucesso!")
else:
    print(f"ℹ️  Domain 'umc.api' já existia")

print(f"📌 Configuração:")
print(f"   Domain: {domain.domain}")
print(f"   Tenant: {tenant.name} (schema: {tenant.schema_name})")
print(f"   Primary: {domain.is_primary}")

print("\n🔧 Atualize o EMQX Connector:")
print("   URL Base: http://umc.api:8000")
print("   Path: /ingest")
print("   Headers: Content-Type: application/json (remover x-tenant)")
