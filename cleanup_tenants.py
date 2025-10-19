#!/usr/bin/env python
"""
Script para limpar tenants duplicados e manter apenas o tenant UMC.
Remove o tenant 'uberlandia_medical_center' e seus domínios.
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.tenants.models import Tenant, Domain
from django.db import connection

def main():
    print("=" * 60)
    print("  LIMPEZA DE TENANTS DUPLICADOS")
    print("=" * 60)
    print()
    
    # 1. Listar todos os tenants
    print("📋 1. Listando todos os tenants existentes...")
    tenants = Tenant.objects.all()
    print(f"   Total de tenants: {tenants.count()}")
    print()
    
    for tenant in tenants:
        print(f"   - Schema: {tenant.schema_name}")
        print(f"     Nome: {tenant.name}")
        print(f"     Slug: {tenant.slug}")
        domains = Domain.objects.filter(tenant=tenant)
        print(f"     Domínios: {', '.join([d.domain for d in domains])}")
        print()
    
    # 2. Listar todos os domínios
    print("🌐 2. Listando todos os domínios...")
    domains = Domain.objects.all()
    for domain in domains:
        print(f"   - {domain.domain} → {domain.tenant.schema_name} (primary: {domain.is_primary})")
    print()
    
    # 3. Identificar tenant problemático
    print("🔍 3. Identificando tenants problemáticos...")
    tenant_to_keep = 'umc'
    tenants_to_remove = []
    
    for tenant in tenants:
        if tenant.schema_name != 'public' and tenant.schema_name != tenant_to_keep:
            tenants_to_remove.append(tenant)
            print(f"   ⚠️  Tenant a ser removido: {tenant.schema_name} ({tenant.name})")
    
    if not tenants_to_remove:
        print("   ✅ Nenhum tenant duplicado encontrado!")
        return
    
    print()
    
    # 4. Verificar domínios dos tenants a serem removidos
    print("🔗 4. Verificando domínios atrelados aos tenants a serem removidos...")
    for tenant in tenants_to_remove:
        domains = Domain.objects.filter(tenant=tenant)
        if domains.exists():
            print(f"   Tenant {tenant.schema_name} tem {domains.count()} domínio(s):")
            for domain in domains:
                print(f"     - {domain.domain} (primary: {domain.is_primary})")
    print()
    
    # 5. Remover domínios
    print("🗑️  5. Removendo domínios dos tenants duplicados...")
    for tenant in tenants_to_remove:
        domains = Domain.objects.filter(tenant=tenant)
        domain_count = domains.count()
        domains.delete()
        print(f"   ✅ Removidos {domain_count} domínio(s) do tenant {tenant.schema_name}")
    print()
    
    # 6. Remover schemas do PostgreSQL
    print("💾 6. Removendo schemas do banco de dados...")
    for tenant in tenants_to_remove:
        schema_name = tenant.schema_name
        print(f"   🗑️  Removendo schema: {schema_name}")
        
        # O django-tenants tem auto_drop_schema=True, então ao deletar
        # o tenant, o schema será removido automaticamente
        try:
            tenant.delete()
            print(f"   ✅ Tenant e schema '{schema_name}' removidos com sucesso!")
        except Exception as e:
            print(f"   ❌ Erro ao remover tenant '{schema_name}': {e}")
    print()
    
    # 7. Verificar resultado final
    print("✅ 7. Verificando resultado final...")
    remaining_tenants = Tenant.objects.all()
    print(f"   Tenants restantes: {remaining_tenants.count()}")
    for tenant in remaining_tenants:
        print(f"   - {tenant.schema_name}: {tenant.name}")
        domains = Domain.objects.filter(tenant=tenant)
        for domain in domains:
            print(f"     └─ {domain.domain}")
    print()
    
    print("=" * 60)
    print("  ✅ LIMPEZA CONCLUÍDA!")
    print("=" * 60)
    print()
    print("📋 Próximos passos:")
    print("   1. Reiniciar o backend: docker restart traksense-api")
    print("   2. Testar login com: test@umc.com / TestPass123!")
    print()

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
