"""
Script para criar usuários de teste com diferentes roles no tenant UMC.

Cria 4 usuários:
- admin@umc.com (owner)
- manager@umc.com (admin)  
- tech@umc.com (operator)
- view@umc.com (viewer)

Uso:
    python create_team_users_umc.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.db import connection
from apps.tenants.models import Tenant
from apps.accounts.models import User, TenantMembership


def main():
    print("=" * 60)
    print("  CRIANDO USUÁRIOS DE TESTE NO TENANT UMC")
    print("=" * 60)
    
    # Buscar tenant UMC
    connection.set_schema_to_public()
    
    try:
        tenant = Tenant.objects.get(slug='umc')
        print(f"\n✅ Tenant encontrado: {tenant.name}")
    except Tenant.DoesNotExist:
        print("\n❌ Tenant 'umc' não encontrado!")
        print("Execute primeiro: python create_tenant_umc_localhost.py")
        return
    
    # Definir usuários
    users_data = [
        {
            'username': 'admin',
            'email': 'admin@umc.com',
            'password': 'admin123',
            'first_name': 'Admin',
            'last_name': 'UMC',
            'role': 'owner',
            'description': 'Proprietário - Acesso total'
        },
        {
            'username': 'manager',
            'email': 'manager@umc.com',
            'password': 'manager123',
            'first_name': 'Manager',
            'last_name': 'UMC',
            'role': 'admin',
            'description': 'Administrador - Acesso total exceto billing'
        },
        {
            'username': 'tech',
            'email': 'tech@umc.com',
            'password': 'tech123',
            'first_name': 'Tech',
            'last_name': 'UMC',
            'role': 'operator',
            'description': 'Operador - Read/write em assets'
        },
        {
            'username': 'viewer',
            'email': 'viewer@umc.com',
            'password': 'viewer123',
            'first_name': 'Viewer',
            'last_name': 'UMC',
            'role': 'viewer',
            'description': 'Visualizador - Apenas leitura'
        }
    ]
    
    print(f"\n📝 Criando {len(users_data)} usuários...\n")
    
    for data in users_data:
        # Verificar se usuário já existe
        user = User.objects.filter(email=data['email']).first()
        
        if user:
            print(f"⚠️  {data['email']} - Usuário já existe")
            created = False
        else:
            # Criar usuário
            user = User.objects.create_user(
                username=data['username'],
                email=data['email'],
                password=data['password'],
                first_name=data['first_name'],
                last_name=data['last_name']
            )
            print(f"✅ {data['email']} - Usuário criado")
            created = True
        
        # Verificar membership
        membership = TenantMembership.objects.filter(
            user=user,
            tenant=tenant
        ).first()
        
        if membership:
            if created:
                print(f"   └─ Membership já existe: {membership.role}")
            else:
                # Atualizar role se mudou
                if membership.role != data['role']:
                    old_role = membership.role
                    membership.role = data['role']
                    membership.save()
                    print(f"   └─ Role atualizado: {old_role} → {data['role']}")
                else:
                    print(f"   └─ Role: {membership.role}")
        else:
            # Criar membership
            membership = TenantMembership.objects.create(
                user=user,
                tenant=tenant,
                role=data['role'],
                status='active'
            )
            print(f"   └─ Membership criado: {data['role']}")
        
        print(f"   └─ {data['description']}")
    
    # Listar todos os membros
    print("\n" + "=" * 60)
    print("  MEMBROS DO TENANT UMC")
    print("=" * 60)
    
    memberships = TenantMembership.objects.filter(tenant=tenant).select_related('user')
    
    print(f"\nTotal: {memberships.count()} membros\n")
    
    for m in memberships:
        status_icon = "🟢" if m.status == 'active' else "🔴"
        role_icon = {
            'owner': '👑',
            'admin': '🔑',
            'operator': '🔧',
            'viewer': '👁️'
        }.get(m.role, '❓')
        
        print(f"{status_icon} {role_icon} {m.user.email:25s} | {m.role:10s} | {m.user.get_full_name()}")
    
    # Mostrar credenciais
    print("\n" + "=" * 60)
    print("  CREDENCIAIS PARA LOGIN")
    print("=" * 60)
    print("\nUse estas credenciais para testar as permissões:\n")
    
    for data in users_data:
        print(f"👤 {data['role'].upper():10s} | {data['email']:20s} | {data['password']}")
    
    print("\n" + "=" * 60)
    print("  ENDPOINTS PARA TESTAR")
    print("=" * 60)
    
    print("""
Login:
  POST http://umc.localhost:8000/api/auth/login/
  Body: {"username_or_email": "admin@umc.com", "password": "admin123"}

Team Members (owner/admin apenas):
  GET http://umc.localhost:8000/api/team/members/
  GET http://umc.localhost:8000/api/team/members/stats/

Criar Asset (operator/admin/owner):
  POST http://umc.localhost:8000/api/assets/
  Body: {"name": "Test Asset", "site": 1, "asset_type": "HVAC"}

Listar Assets (qualquer role):
  GET http://umc.localhost:8000/api/assets/
    
NOTA: Viewers podem apenas fazer GET, mas NÃO podem POST/PATCH/DELETE
""")
    
    print("=" * 60)
    print("✅ SCRIPT CONCLUÍDO")
    print("=" * 60)


if __name__ == '__main__':
    main()
