"""
Testa login com contexto de tenant configurado
"""
import os
import sys
import django

sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django_tenants.utils import tenant_context
from apps.tenants.models import Tenant
from apps.accounts.models import User

# Pegar o tenant UMC
tenant = Tenant.objects.get(schema_name='umc')

print(f"=== TESTANDO NO TENANT: {tenant.name} ({tenant.schema_name}) ===\n")

# Executar no contexto do tenant
with tenant_context(tenant):
    print("1. Listando usuários no tenant UMC:")
    users = User.objects.all()
    for user in users:
        print(f"   - {user.username} / {user.email} (ativo: {user.is_active})")
    
    print(f"\n2. Total de usuários no tenant: {users.count()}")
    
    # Testar autenticação
    from django.contrib.auth import authenticate
    
    print("\n3. Testando autenticação:")
    user = authenticate(username='admin', password='admin123')
    if user:
        print(f"   ✅ Autenticação OK: {user.username}")
    else:
        print("   ❌ Autenticação FALHOU")
