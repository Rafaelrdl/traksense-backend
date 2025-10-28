"""
Debug script to test permission with real HTTP flow.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from rest_framework.test import force_authenticate
from django.db import connection
from django_tenants.utils import tenant_context

from apps.tenants.models import Tenant
from apps.accounts.models import TenantMembership
from apps.accounts.permissions import CanManageTeam

User = get_user_model()

print("=" * 60)
print("DEBUG: TESTANDO PERMISSÃO CanManageTeam")
print("=" * 60)

# Get tenant
tenant = Tenant.objects.get(slug='umc')
print(f"\n✅ Tenant: {tenant.name}")
print(f"   ID: {tenant.id}")
print(f"   Slug: {tenant.slug}")

# Get user
user = User.objects.get(email='admin@umc.com')
print(f"\n✅ Usuário: {user.email}")
print(f"   ID: {user.id}")

# Switch to tenant schema
print("\n" + "=" * 60)
print("TESTANDO NO CONTEXTO DO TENANT")
print("=" * 60)

with tenant_context(tenant):
    connection.set_tenant(tenant)
    
    print(f"\n📊 connection.tenant: {connection.tenant}")
    print(f"   Type: {type(connection.tenant)}")
    print(f"   ID: {connection.tenant.id if hasattr(connection.tenant, 'id') else 'N/A'}")
    print(f"   Schema: {connection.schema_name}")
    
    # Check memberships
    print(f"\n🔍 Buscando memberships para user {user.id} e tenant {tenant.id}:")
    memberships = TenantMembership.objects.filter(
        user=user,
        tenant=tenant,
        status='active'
    )
    print(f"   Query: TenantMembership.objects.filter(user={user.id}, tenant={tenant.id}, status='active')")
    print(f"   Count: {memberships.count()}")
    
    for m in memberships:
        print(f"\n   ✅ Membership encontrado:")
        print(f"      ID: {m.id}")
        print(f"      User ID: {m.user.id}")
        print(f"      Tenant ID: {m.tenant.id}")
        print(f"      Role: {m.role}")
        print(f"      Status: {m.status}")
        print(f"      can_manage_team: {m.can_manage_team}")
    
    # Test permission
    print("\n" + "=" * 60)
    print("TESTANDO PERMISSÃO")
    print("=" * 60)
    
    factory = RequestFactory()
    request = factory.get('/api/team/members/')
    request.tenant = tenant
    force_authenticate(request, user=user)
    
    permission = CanManageTeam()
    
    # Mock view
    class MockView:
        pass
    
    view = MockView()
    
    result = permission.has_permission(request, view)
    print(f"\n🎯 Resultado da permissão: {result}")
    
    if not result:
        print("\n❌ PERMISSÃO NEGADA!")
        print("   Debugando dentro da permissão...")
        
        # Simular o que a permissão faz
        print(f"\n   request.user: {request.user}")
        print(f"   request.user.is_authenticated: {request.user.is_authenticated}")
        print(f"   connection.tenant: {connection.tenant}")
        
        membership = TenantMembership.objects.filter(
            user=request.user,
            tenant=connection.tenant,
            status='active'
        ).first()
        
        print(f"   membership query result: {membership}")
        if membership:
            print(f"   membership.can_manage_team: {membership.can_manage_team}")
    else:
        print("\n✅ PERMISSÃO CONCEDIDA!")
