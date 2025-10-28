"""
Verificar e corrigir o role do usuário gerente@umc.com
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
print("VERIFICANDO ROLE DO GERENTE@UMC.COM")
print("=" * 60)

# Get tenant
tenant = Tenant.objects.get(slug='umc')
print(f"\n✅ Tenant: {tenant.name}")

# Switch to tenant schema
with tenant_context(tenant):
    connection.set_tenant(tenant)
    
    # Get user
    user = User.objects.get(email='gerente@umc.com')
    print(f"\n👤 Usuário: {user.email}")
    print(f"   Nome: {user.first_name} {user.last_name}")
    print(f"   Username: {user.username}")
    
    # Get membership
    membership = TenantMembership.objects.get(user=user, tenant=tenant)
    print(f"\n📋 Membership ATUAL:")
    print(f"   Role: {membership.role}")
    print(f"   Status: {membership.status}")
    print(f"   can_manage_team: {membership.can_manage_team}")
    print(f"   can_write: {membership.can_write}")
    
    # Check if needs correction
    if membership.role != 'admin':
        print(f"\n⚠️  Role incorreto! Deveria ser 'admin', mas está '{membership.role}'")
        print(f"\n🔧 Corrigindo role para 'admin'...")
        
        membership.role = 'admin'
        membership.status = 'active'
        membership.save()
        
        print(f"\n✅ Role atualizado com sucesso!")
        
        # Verify
        membership.refresh_from_db()
        print(f"\n📋 Membership ATUALIZADO:")
        print(f"   Role: {membership.role}")
        print(f"   Status: {membership.status}")
        print(f"   can_manage_team: {membership.can_manage_team}")
        print(f"   can_write: {membership.can_write}")
    else:
        print(f"\n✅ Role já está correto: {membership.role}")
    
    # List all memberships
    print(f"\n" + "=" * 60)
    print("TODOS OS MEMBERSHIPS NO TENANT UMC:")
    print("=" * 60)
    
    for m in TenantMembership.objects.filter(tenant=tenant).select_related('user').order_by('role'):
        print(f"\n{m.user.email}")
        print(f"  Role: {m.role}")
        print(f"  Status: {m.status}")
        print(f"  can_manage_team: {m.can_manage_team}")
