"""
Testa o endpoint GET /api/assets/ com autenticação
"""
import os
import sys
import django

sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from rest_framework.test import APIRequestFactory
from apps.assets.views import AssetViewSet
from apps.accounts.models import User
from django_tenants.utils import tenant_context
from apps.tenants.models import Tenant

# Pegar tenant e usuário
tenant = Tenant.objects.get(schema_name='umc')

with tenant_context(tenant):
    user = User.objects.get(username='admin')

# Criar requisição
factory = APIRequestFactory()
request = factory.get('/api/assets/')

# Simular autenticação
request.user = user

# Chamar a view
view = AssetViewSet.as_view({'get': 'list'})

# Executar no contexto do tenant
from django_tenants.utils import schema_context
with schema_context(tenant.schema_name):
    response = view(request)

print(f"Status Code: {response.status_code}")
print(f"\nData:")
print(response.data)
