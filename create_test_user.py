"""
Script para criar usuário de teste no tenant UMC.
"""

from django_tenants.utils import schema_context
from apps.accounts.models import User

# Criar usuário no tenant UMC
with schema_context('umc'):
    # Remove usuário se já existe
    User.objects.filter(username='admin').delete()
    
    # Cria novo usuário
    user = User.objects.create_user(
        username='admin',
        email='admin@umc.local',
        password='admin123',
        first_name='Admin',
        last_name='TrakSense',
        is_staff=True,
        is_superuser=True
    )
    
    print(f"✅ Usuário criado com sucesso!")
    print(f"   Username: {user.username}")
    print(f"   Email: {user.email}")
    print(f"   Is Staff: {user.is_staff}")
    print(f"   Is Superuser: {user.is_superuser}")
