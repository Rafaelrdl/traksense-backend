"""
Script para criar usuário de teste para validação da API de Assets
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')
django.setup()

from django.contrib.auth import get_user_model
from django_tenants.utils import schema_context
from apps.tenants.models import Tenant

User = get_user_model()

def create_test_user():
    """Cria usuário de teste no tenant umc"""
    try:
        # Obter tenant umc
        tenant = Tenant.objects.get(schema_name='umc')
        print(f"✅ Tenant encontrado: {tenant.name} ({tenant.schema_name})")
        
        # Executar dentro do schema do tenant
        with schema_context(tenant.schema_name):
            # Verificar se usuário já existe
            username = 'testapi'
            email = 'testapi@umc.com'
            password = 'Test@123456'
            
            if User.objects.filter(username=username).exists():
                user = User.objects.get(username=username)
                print(f"⚠️  Usuário '{username}' já existe")
                
                # Atualizar senha
                user.set_password(password)
                user.is_active = True
                user.save()
                print(f"✅ Senha atualizada e usuário ativado")
            else:
                # Criar novo usuário
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name='Test',
                    last_name='API',
                    is_active=True
                )
                print(f"✅ Usuário criado: {username}")
            
            print(f"\n📋 Credenciais de Teste:")
            print(f"   Username: {username}")
            print(f"   Email: {email}")
            print(f"   Password: {password}")
            print(f"   Tenant: umc.localhost:8000")
            print(f"   Login URL: http://umc.localhost:8000/api/auth/login/")
            
    except Tenant.DoesNotExist:
        print("❌ Tenant 'umc' não encontrado!")
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    create_test_user()
