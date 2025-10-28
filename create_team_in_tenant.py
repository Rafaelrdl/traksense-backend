"""
Create demo team members in TENANT SCHEMA (umc).
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.contrib.auth import get_user_model
from django.db import connection
from django_tenants.utils import tenant_context

from apps.tenants.models import Tenant
from apps.accounts.models import TenantMembership

User = get_user_model()

print("=" * 60)
print("CRIANDO MEMBERSHIPS NO SCHEMA DO TENANT UMC")
print("=" * 60)

# Get tenant
tenant = Tenant.objects.get(slug='umc')
print(f"\n✅ Tenant: {tenant.name}")
print(f"   Schema: umc")

# Demo users to create memberships
demo_users = [
    {
        'email': 'admin@umc.com',
        'role': 'owner',
        'status': 'active',
    },
    {
        'email': 'gerente@umc.com',
        'role': 'admin',
        'status': 'active',
    },
    {
        'email': 'operador@umc.com',
        'role': 'operator',
        'status': 'active',
    },
    {
        'email': 'visualizador@umc.com',
        'role': 'viewer',
        'status': 'active',
    },
    {
        'email': 'operador2@umc.com',
        'role': 'operator',
        'status': 'inactive',
    },
]

# Switch to tenant schema to create memberships
with tenant_context(tenant):
    connection.set_tenant(tenant)
    
    print(f"\n📊 Contexto atual:")
    print(f"   connection.schema_name: {connection.schema_name}")
    print(f"   connection.tenant: {connection.tenant}")
    
    print(f"\n👥 Criando/atualizando memberships:")
    
    created_count = 0
    updated_count = 0
    
    for user_data in demo_users:
        # Get user (users are in public schema, but we can still query them)
        try:
            user = User.objects.get(email=user_data['email'])
        except User.DoesNotExist:
            print(f"\n⚠️  Usuário não encontrado: {user_data['email']}")
            continue
        
        # Check if membership exists
        membership, created = TenantMembership.objects.update_or_create(
            user=user,
            tenant=tenant,
            defaults={
                'role': user_data['role'],
                'status': user_data['status'],
            }
        )
        
        if created:
            created_count += 1
            print(f"\n✅ Membership criado: {user.email}")
        else:
            updated_count += 1
            print(f"\n↻  Membership atualizado: {user.email}")
        
        print(f"   Role: {membership.role}")
        print(f"   Status: {membership.status}")
        print(f"   can_manage_team: {membership.can_manage_team}")
    
    print("\n" + "=" * 60)
    print("RESUMO")
    print("=" * 60)
    print(f"✅ Criados: {created_count}")
    print(f"↻  Atualizados: {updated_count}")
    
    # Verify
    total = TenantMembership.objects.filter(tenant=tenant).count()
    print(f"\n📊 Total de memberships no schema umc: {total}")
    
    print("\n👥 Memberships criados:")
    for membership in TenantMembership.objects.filter(tenant=tenant).select_related('user'):
        print(f"   - {membership.user.email}: {membership.role} ({membership.status})")
