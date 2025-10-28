"""
Test login API to verify role is being returned correctly.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.test import RequestFactory
from django.db import connection
from django_tenants.utils import tenant_context

from apps.tenants.models import Tenant
from apps.accounts.views import LoginView
from apps.accounts.serializers import UserSerializer
from apps.accounts.models import User

print("=" * 60)
print("TESTANDO LOGIN API - GERENTE@UMC.COM")
print("=" * 60)

# Get tenant
tenant = Tenant.objects.get(slug='umc')
print(f"\n✅ Tenant: {tenant.name}")

# Switch to tenant schema
with tenant_context(tenant):
    connection.set_tenant(tenant)
    
    print(f"\n📊 Schema: {connection.schema_name}")
    
    # Get user
    user = User.objects.get(email='gerente@umc.com')
    print(f"\n👤 Usuário: {user.email}")
    
    # Test serializer directly
    serializer = UserSerializer(user)
    data = serializer.data
    
    print(f"\n📋 DADOS DO SERIALIZER:")
    print(f"   ID: {data.get('id')}")
    print(f"   Email: {data.get('email')}")
    print(f"   Name: {data.get('full_name')}")
    print(f"   Role: {data.get('role')}")
    print(f"   Site: {data.get('site')}")
    print(f"   is_staff: {data.get('is_staff')}")
    
    # Test login endpoint
    print(f"\n" + "=" * 60)
    print("TESTANDO ENDPOINT DE LOGIN")
    print("=" * 60)
    
    factory = RequestFactory()
    request = factory.post(
        '/api/auth/login/',
        data={
            'username_or_email': 'gerente@umc.com',
            'password': 'senha123'
        },
        content_type='application/json'
    )
    
    # Set tenant in request (simulate middleware)
    request.tenant = tenant
    
    # Call view
    view = LoginView.as_view()
    response = view(request)
    
    print(f"\n📤 Response Status: {response.status_code}")
    
    if response.status_code == 200:
        print(f"\n✅ LOGIN SUCCESSFUL!")
        print(f"\n📋 Response Data:")
        if hasattr(response, 'data'):
            user_data = response.data.get('user', {})
            print(f"   Email: {user_data.get('email')}")
            print(f"   Name: {user_data.get('full_name')}")
            print(f"   Role: {user_data.get('role')}")
            print(f"   Site: {user_data.get('site')}")
    else:
        print(f"\n❌ LOGIN FAILED!")
        if hasattr(response, 'data'):
            print(f"   Error: {response.data}")
