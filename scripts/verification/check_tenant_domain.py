"""
Verifica se existe tenant para o domínio umc.localhost
"""
import os
import sys
import django

sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.tenants.models import Tenant, Domain

# Listar todos os domínios
print("=== DOMÍNIOS CADASTRADOS ===")
for domain in Domain.objects.all():
    print(f"- {domain.domain} → Tenant: {domain.tenant.schema_name} ({domain.tenant.name})")

# Verificar se existe umc.localhost
print("\n=== VERIFICANDO umc.localhost ===")
try:
    domain = Domain.objects.get(domain='umc.localhost')
    print(f"✅ Encontrado: {domain.domain} → {domain.tenant.schema_name}")
except Domain.DoesNotExist:
    print("❌ Domínio umc.localhost NÃO EXISTE!")
    print("\nVocê precisa criar um tenant com este domínio.")
