"""
Sync users from public schema to umc schema and create memberships.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.contrib.auth import get_user_model
from django.db import connection
from django_tenants.utils import tenant_context, schema_context

from apps.tenants.models import Tenant
from apps.accounts.models import TenantMembership

User = get_user_model()

print("=" * 60)
print("SINCRONIZANDO USUÁRIOS DO PUBLIC PARA UMC")
print("=" * 60)

# Get tenant
tenant = Tenant.objects.get(slug='umc')
print(f"\n✅ Tenant: {tenant.name}")

# Demo users with their data
demo_users = [
    {
        'email': 'admin@umc.com',
        'username': 'admin',
        'password': 'admin123',  # Será usado o hash do public
        'role': 'owner',
        'status': 'active',
    },
    {
        'email': 'gerente@umc.com',
        'username': 'gerente',
        'first_name': 'Carlos',
        'last_name': 'Gerente',
        'password': 'senha123',
        'role': 'admin',
        'status': 'active',
    },
    {
        'email': 'operador@umc.com',
        'username': 'operador',
        'first_name': 'João',
        'last_name': 'Silva',
        'password': 'senha123',
        'role': 'operator',
        'status': 'active',
    },
    {
        'email': 'visualizador@umc.com',
        'username': 'visualizador',
        'first_name': 'Maria',
        'last_name': 'Santos',
        'password': 'senha123',
        'role': 'viewer',
        'status': 'active',
    },
    {
        'email': 'operador2@umc.com',
        'username': 'operador2',
        'first_name': 'Pedro',
        'last_name': 'Oliveira',
        'password': 'senha123',
        'role': 'operator',
        'status': 'inactive',
    },
]

print("\n📊 Fase 1: Coletando dados dos usuários do schema public")
user_data_from_public = {}

with schema_context('public'):
    for user_info in demo_users:
        try:
            user = User.objects.get(email=user_info['email'])
            user_data_from_public[user_info['email']] = {
                'username': user.username,
                'email': user.email,
                'password': user.password,  # Hash já criptografado
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_active': user.is_active,
                'is_staff': user.is_staff,
                'role': user_info['role'],
                'membership_status': user_info['status'],
            }
            print(f"   ✅ {user.email}")
        except User.DoesNotExist:
            print(f"   ⚠️  Não encontrado: {user_info['email']}")

print(f"\n📊 Fase 2: Criando usuários e memberships no schema umc")

with tenant_context(tenant):
    connection.set_tenant(tenant)
    
    print(f"\n   Schema atual: {connection.schema_name}")
    
    created_users = 0
    created_memberships = 0
    
    for email, data in user_data_from_public.items():
        # Create or get user in tenant schema
        # Use username as unique identifier
        try:
            user = User.objects.get(username=data['username'])
            # Update fields
            user.email = email
            user.password = data['password']
            user.first_name = data['first_name']
            user.last_name = data['last_name']
            user.is_active = data['is_active']
            user.is_staff = data['is_staff']
            user.save()
            print(f"\n   ↻  Usuário atualizado: {email}")
        except User.DoesNotExist:
            # Create new user
            user = User.objects.create(
                username=data['username'],
                email=email,
                password=data['password'],
                first_name=data['first_name'],
                last_name=data['last_name'],
                is_active=data['is_active'],
                is_staff=data['is_staff'],
            )
            created_users += 1
            print(f"\n   ✅ Usuário criado: {email}")
        
        # Create membership
        membership, created = TenantMembership.objects.update_or_create(
            user=user,
            tenant=tenant,
            defaults={
                'role': data['role'],
                'status': data['membership_status'],
            }
        )
        
        if created:
            created_memberships += 1
            print(f"      ✅ Membership criado: {data['role']}")
        else:
            print(f"      ↻  Membership atualizado: {data['role']}")
    
    print("\n" + "=" * 60)
    print("RESUMO")
    print("=" * 60)
    print(f"✅ Usuários criados: {created_users}")
    print(f"✅ Memberships criados: {created_memberships}")
    
    # Verify
    total_users = User.objects.count()
    total_memberships = TenantMembership.objects.filter(tenant=tenant).count()
    
    print(f"\n📊 Total de usuários no schema umc: {total_users}")
    print(f"📊 Total de memberships no schema umc: {total_memberships}")
    
    print("\n👥 Usuários e memberships no schema umc:")
    for membership in TenantMembership.objects.filter(tenant=tenant).select_related('user'):
        print(f"   - {membership.user.email}: {membership.role} ({membership.status})")
