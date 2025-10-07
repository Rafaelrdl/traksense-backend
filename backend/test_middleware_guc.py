"""
Script temporário para testar TenantGucMiddleware
"""
from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser
from core.middleware import TenantGucMiddleware
from apps.tenancy.models import Client
from django.db import connection

# Simular requisição
factory = RequestFactory()
request = factory.get('/', HTTP_HOST='alpha.localhost')
request.user = AnonymousUser()

# Obter tenant alpha
tenant = Client.objects.get(schema_name='test_alpha')
request.tenant = tenant

# Processar middleware
middleware = TenantGucMiddleware(lambda r: None)
middleware.process_request(request)

# Verificar GUC
cursor = connection.cursor()
cursor.execute("SELECT current_setting('app.tenant_id', true)")
guc_value = cursor.fetchone()[0]

print(f"✅ GUC configurado: {guc_value}")
print(f"✅ Tenant PK: {tenant.pk}")
print(f"✅ Match: {guc_value == str(tenant.pk)}")

if guc_value == str(tenant.pk):
    print("\n✅ TenantGucMiddleware funcionando corretamente!")
else:
    print(f"\n❌ ERRO: GUC ({guc_value}) não corresponde ao Tenant PK ({tenant.pk})")
