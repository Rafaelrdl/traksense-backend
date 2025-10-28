"""
Test team API with full HTTP request simulation including authentication.
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
from apps.accounts.views_team import TeamMemberViewSet

User = get_user_model()

print("=" * 60)
print("TESTE COMPLETO DA API DE TEAM COM AUTENTICAÇÃO")
print("=" * 60)

# Get tenant
tenant = Tenant.objects.get(slug='umc')
print(f"\n✅ Tenant: {tenant.name}")

# Get user (users are in public schema)
user = User.objects.get(email='admin@umc.com')
print(f"✅ Usuário: {user.email}")

# Get membership (also in public schema)
membership = TenantMembership.objects.get(user=user, tenant=tenant)
print(f"✅ Membership: {membership.role} ({membership.status})")
print(f"   can_manage_team: {membership.can_manage_team}")

# Create request
factory = RequestFactory()

print("\n" + "=" * 60)
print("TESTE 1: GET /api/team/members/ (sem autenticação)")
print("=" * 60)

# Test without authentication
with tenant_context(tenant):
    request = factory.get('/api/team/members/')
    request.tenant = tenant
    connection.set_tenant(tenant)
    
    view = TeamMemberViewSet.as_view({'get': 'list'})
    
    try:
        response = view(request)
        print(f"Status: {response.status_code}")
        if hasattr(response, 'data'):
            print(f"Data: {response.data}")
    except Exception as e:
        print(f"❌ Erro: {e}")

print("\n" + "=" * 60)
print("TESTE 2: GET /api/team/members/ (COM autenticação)")
print("=" * 60)

# Test with authentication
with tenant_context(tenant):
    connection.set_tenant(tenant)
    print(f"connection.tenant: {connection.tenant}")
    print(f"connection.schema_name: {connection.schema_name}")
    
    request = factory.get('/api/team/members/')
    request.tenant = tenant
    
    # Force authentication
    force_authenticate(request, user=user)
    
    view = TeamMemberViewSet.as_view({'get': 'list'})
    
    try:
        response = view(request)
        response.render()  # Force render to get final data
        print(f"Status: {response.status_code}")
        if hasattr(response, 'data'):
            if response.status_code == 200:
                print(f"Members count: {response.data.get('count')}")
                print(f"First 2 members:")
                for member in response.data.get('results', [])[:2]:
                    print(f"  - {member['user']['full_name']} ({member['role']})")
            else:
                print(f"Error: {response.data}")
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 60)
print("TESTE 3: Verificando middleware de tenant")
print("=" * 60)

print(f"connection.tenant: {connection.tenant}")
print(f"connection.schema_name: {connection.schema_name}")
