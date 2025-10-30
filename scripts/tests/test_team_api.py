"""
Script para testar a API de team management diretamente.
"""

import django
import os

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from apps.accounts.models import TenantMembership
from apps.tenants.models import Tenant
from apps.accounts.views_team import TeamMemberViewSet
from rest_framework.test import force_authenticate

User = get_user_model()

def test_team_api():
    print("\n" + "="*60)
    print("TESTANDO API DE TEAM MANAGEMENT")
    print("="*60)
    
    # Buscar tenant e usuário
    tenant = Tenant.objects.get(slug='umc')
    user = User.objects.get(email='admin@umc.com')
    
    print(f"\n✅ Tenant: {tenant.name}")
    print(f"✅ Usuário: {user.email}")
    
    # Verificar membership
    membership = TenantMembership.objects.get(user=user, tenant=tenant)
    print(f"✅ Membership: {membership.role} ({membership.status})")
    
    # Criar request factory
    factory = RequestFactory()
    
    # Testar listagem de membros
    print("\n📋 TESTANDO GET /api/team/members/")
    print("-" * 60)
    
    request = factory.get('/api/team/members/')
    force_authenticate(request, user=user)
    
    # Simular tenant no connection
    from django.db import connection
    connection.tenant = tenant
    
    view = TeamMemberViewSet.as_view({'get': 'list'})
    response = view(request)
    
    print(f"Status: {response.status_code}")
    print(f"Data: {response.data}")
    
    print("\n✅ Teste concluído!")

if __name__ == '__main__':
    test_team_api()
