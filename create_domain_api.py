#!/usr/bin/env python
"""
Script para criar Domain 'api' apontando para o schema PUBLIC.
Isso permite que EMQX envie requests com Host: api:8000
e o django-tenants use PUBLIC_SCHEMA_URLCONF onde está o /ingest.
O IngestView fará o switch manual para o schema do tenant baseado no header x-tenant.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.tenants.models import Tenant, Domain

# Buscar tenant público
public_tenant = Tenant.objects.get(schema_name='public')

# Deletar domain 'api' antigo se existir com tenant diferente
old_domains = Domain.objects.filter(domain='api').exclude(tenant=public_tenant)
if old_domains.exists():
    print(f"⚠️  Removendo {old_domains.count()} domain(s) 'api' antigo(s)...")
    old_domains.delete()

# Criar domain api apontando para public
domain, created = Domain.objects.get_or_create(
    domain='api',
    defaults={
        'tenant': public_tenant,
        'is_primary': False
    }
)

if created:
    print(f"✅ Domain 'api' criado com sucesso!")
else:
    print(f"ℹ️  Domain 'api' já existia")

print(f"📌 Configuração:")
print(f"   Domain: {domain.domain}")
print(f"   Tenant: {public_tenant.name} (schema: {public_tenant.schema_name})")
print(f"   Primary: {domain.is_primary}")

print("\n🎯 Como funciona o fluxo multi-tenant:")
print("   1. EMQX envia request para http://api:8000/ingest")
print("   2. Header x-tenant: uberlandia-medical-center")
print("   3. Django resolve 'api' → schema public → PUBLIC_SCHEMA_URLCONF")
print("   4. PUBLIC_SCHEMA_URLCONF roteia /ingest → IngestView")
print("   5. IngestView lê header x-tenant")
print("   6. IngestView faz switch para schema uberlandia_medical_center")
print("   7. Telemetry salva no schema correto! ✅")

print("\n✅ Para novos tenants:")
print("   - Criar tenant no banco")
print("   - Criar Rule no EMQX com topic 'tenants/<slug>/#'")
print("   - Configurar header x-tenant: <slug> na Action")
print("   - Mesmo Connector pode ser reutilizado!")
