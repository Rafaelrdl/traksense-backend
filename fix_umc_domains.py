#!/usr/bin/env python
"""
Associar domínios ao tenant UMC correto.
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.tenants.models import Tenant, Domain

def main():
    print("=" * 60)
    print("  ASSOCIANDO DOMÍNIOS AO TENANT UMC")
    print("=" * 60)
    print()
    
    # Get UMC tenant
    try:
        tenant = Tenant.objects.get(schema_name='umc')
        print(f"✅ Tenant encontrado: {tenant.name} (schema: {tenant.schema_name})")
    except Tenant.DoesNotExist:
        print("❌ Tenant 'umc' não encontrado!")
        return
    print()
    
    # Create domains
    domains_to_create = [
        ('umc.localhost', True),   # Primary domain
        ('umc.api', False),         # Secondary domain
    ]
    
    print("🌐 Criando/atualizando domínios...")
    for domain_name, is_primary in domains_to_create:
        domain, created = Domain.objects.get_or_create(
            domain=domain_name,
            defaults={
                'tenant': tenant,
                'is_primary': is_primary,
            }
        )
        
        if created:
            print(f"   ✅ Domínio criado: {domain_name} (primary: {is_primary})")
        else:
            # Update tenant if domain exists
            if domain.tenant != tenant:
                old_tenant = domain.tenant
                domain.tenant = tenant
                domain.is_primary = is_primary
                domain.save()
                print(f"   🔄 Domínio atualizado: {domain_name}")
                print(f"      Antes: {old_tenant.schema_name} → Agora: {tenant.schema_name}")
            else:
                print(f"   ℹ️  Domínio já existe: {domain_name} (primary: {is_primary})")
    print()
    
    # Verify
    print("✅ Verificação final...")
    all_domains = Domain.objects.filter(tenant=tenant)
    print(f"   Tenant: {tenant.name}")
    print(f"   Schema: {tenant.schema_name}")
    print(f"   Domínios ({all_domains.count()}):")
    for d in all_domains:
        print(f"     - {d.domain} (primary: {d.is_primary})")
    print()
    
    print("=" * 60)
    print("  ✅ DOMÍNIOS CONFIGURADOS!")
    print("=" * 60)
    print()
    print("🔐 Agora você pode acessar:")
    print("   - http://umc.localhost:8000/api/")
    print("   - http://umc.api:8000/api/")
    print()

if __name__ == '__main__':
    main()
