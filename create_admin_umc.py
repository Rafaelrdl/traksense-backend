"""
Cria usuário admin no tenant UMC
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

print(f"=== CRIANDO ADMIN NO TENANT: {tenant.name} ===\n")

with tenant_context(tenant):
    # Verificar se já existe
    if User.objects.filter(username='admin').exists():
        print("❌ Usuário 'admin' já existe no tenant UMC")
        user = User.objects.get(username='admin')
    else:
        # Criar usuário admin
        user = User.objects.create_user(
            username='admin',
            email='admin@traksense.com',
            password='admin123',
            is_staff=True,
            is_superuser=True
        )
        print("✅ Usuário admin criado no tenant UMC")
    
    print(f"\nDetalhes:")
    print(f"  Username: {user.username}")
    print(f"  Email: {user.email}")
    print(f"  Is active: {user.is_active}")
    print(f"  Is staff: {user.is_staff}")
    print(f"  Is superuser: {user.is_superuser}")
    
    # Testar autenticação
    from django.contrib.auth import authenticate
    auth_user = authenticate(username='admin', password='admin123')
    if auth_user:
        print(f"\n✅ Autenticação funcionando!")
    else:
        print(f"\n❌ Erro na autenticação")
