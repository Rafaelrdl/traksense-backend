#!/usr/bin/env python
"""
Create UMC tenant with localhost domain and test user.
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.contrib.auth import get_user_model
from apps.tenants.models import Tenant, Domain
from django.db import connection

User = get_user_model()

def main():
    # Create or get tenant
    tenant, created = Tenant.objects.get_or_create(
        schema_name='umc',
        defaults={
            'name': 'Uberlândia Medical Center',
            'slug': 'umc',
        }
    )
    
    if created:
        print(f"✅ Tenant criado: {tenant.name} (schema: {tenant.schema_name})")
    else:
        print(f"ℹ️  Tenant já existe: {tenant.name} (schema: {tenant.schema_name})")
    
    # Create or get domain
    domain, created = Domain.objects.get_or_create(
        domain='umc.localhost',
        defaults={
            'tenant': tenant,
            'is_primary': True,
        }
    )
    
    if created:
        print(f"✅ Domain criado: {domain.domain} (primary: {domain.is_primary})")
    else:
        print(f"ℹ️  Domain já existe: {domain.domain} (primary: {domain.is_primary})")
    
    # Switch to tenant schema
    connection.set_tenant(tenant)
    print(f"\n🔄 Conectado ao schema: {tenant.schema_name}")
    
    # Create or get test user
    email = 'test@umc.com'
    username = 'testuser'
    
    user, created = User.objects.get_or_create(
        email=email,
        defaults={
            'username': username,
            'first_name': 'Test',
            'last_name': 'User',
            'is_active': True,
            'is_staff': False,
            'is_superuser': False,
        }
    )
    
    if created:
        user.set_password('TestPass123!')
        user.save()
        print(f"✅ Usuário criado: {user.email}")
        print(f"   Username: {user.username}")
        print(f"   Password: TestPass123!")
    else:
        # Update password to ensure it's correct
        user.set_password('TestPass123!')
        user.save()
        print(f"ℹ️  Usuário já existe: {user.email}")
        print(f"   Username: {user.username}")
        print(f"   Password: TestPass123! (atualizada)")
    
    print("\n📋 Resumo da Configuração:")
    print(f"   Tenant: {tenant.name}")
    print(f"   Schema: {tenant.schema_name}")
    print(f"   Domain: {domain.domain}")
    print(f"   URL: http://{domain.domain}:8000")
    print(f"\n🔐 Credenciais de Teste:")
    print(f"   Email: {email}")
    print(f"   Senha: TestPass123!")
    print(f"\n✅ Configuração completa! Você pode fazer login agora.")

if __name__ == '__main__':
    main()
