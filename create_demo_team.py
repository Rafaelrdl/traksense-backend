"""
Script para criar usuários de demonstração com diferentes permissões
para testar o sistema de Team Management (FASE 5)

Executar com: docker exec -it traksense-api python create_demo_team.py
"""

import django
import os

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.accounts.models import TenantMembership, Invite
from apps.tenants.models import Tenant

User = get_user_model()

def create_demo_team_members():
    """
    Cria membros de equipe de demonstração no tenant UMC
    com diferentes níveis de permissão
    """
    
    print("\n" + "="*60)
    print("CRIANDO USUÁRIOS DE DEMONSTRAÇÃO - FASE 5")
    print("="*60)
    
    # Buscar ou criar tenant UMC
    try:
        tenant = Tenant.objects.get(slug='umc')
        print(f"✅ Tenant encontrado: {tenant.name} (slug: {tenant.slug})")
    except Tenant.DoesNotExist:
        print("❌ Tenant 'umc' não encontrado!")
        print("   Listando tenants disponíveis...")
        for t in Tenant.objects.all():
            print(f"   - {t.name} (slug: {t.slug})")
        return
    
    # Lista de usuários para criar
    demo_users = [
        {
            'email': 'admin@umc.com',
            'username': 'admin',
            'first_name': 'Admin',
            'last_name': 'UMC',
            'password': 'senha123',
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
    
    print(f"\n📊 Verificando usuários existentes...")
    existing_count = User.objects.count()
    print(f"   Usuários atuais: {existing_count}")
    
    created_count = 0
    updated_count = 0
    
    for user_data in demo_users:
        email = user_data['email']
        username = user_data['username']
        role = user_data.pop('role')
        status = user_data.pop('status')
        password = user_data.pop('password')
        
        # Verificar se usuário já existe (por email ou username)
        try:
            user = User.objects.get(email=email)
            created = False
            print(f"\n⚠️  Usuário já existe: {email}")
        except User.DoesNotExist:
            try:
                user = User.objects.get(username=username)
                created = False
                print(f"\n⚠️  Username já existe: {username} (atualizando email para {email})")
                user.email = email
                user.save()
            except User.DoesNotExist:
                # Criar novo usuário
                user = User.objects.create_user(
                    email=email,
                    username=username,
                    first_name=user_data['first_name'],
                    last_name=user_data['last_name'],
                    password=password
                )
                created = True
                print(f"\n✅ Usuário criado: {email}")
                print(f"   Nome: {user.get_full_name()}")
                created_count += 1
        
        # Criar ou atualizar membership
        membership, m_created = TenantMembership.objects.get_or_create(
            user=user,
            tenant=tenant,
            defaults={
                'role': role,
                'status': status,
            }
        )
        
        if not m_created:
            # Atualizar role e status se já existe
            membership.role = role
            membership.status = status
            membership.save()
            print(f"   ↻ Membership atualizado: {role} ({status})")
            updated_count += 1
        else:
            print(f"   ✅ Membership criado: {role} ({status})")
    
    # Mostrar resumo
    print("\n" + "="*60)
    print("RESUMO DA CRIAÇÃO")
    print("="*60)
    print(f"✅ Usuários/Memberships processados: {len(demo_users)}")
    print(f"   Novos: {created_count}")
    print(f"   Atualizados: {updated_count}")
    
    # Listar todos os membros
    print("\n📋 MEMBROS DA EQUIPE UMC:")
    print("-" * 60)
    memberships = TenantMembership.objects.filter(tenant=tenant).select_related('user')
    
    if not memberships.exists():
        print("❌ Nenhum membro encontrado!")
    else:
        for m in memberships:
            print(f"\n👤 {m.user.get_full_name()} ({m.user.email})")
            print(f"   Role: {m.role.upper()}")
            print(f"   Status: {m.status.upper()}")
            print(f"   Entrou em: {m.joined_at.strftime('%d/%m/%Y %H:%M')}")
    
    print("\n" + "="*60)
    print(f"Total de membros: {memberships.count()}")
    print("="*60)
    
    # Verificar convites
    from apps.accounts.models import Invite
    invites = Invite.objects.filter(tenant=tenant, status='pending')
    print(f"\n✉️  Convites pendentes: {invites.count()}")
    
    if invites.exists():
        for invite in invites:
            print(f"   - {invite.email} ({invite.role}) - Criado em {invite.created_at.strftime('%d/%m/%Y')}")

if __name__ == '__main__':
    create_demo_team_members()
    print("\n✅ Script concluído!")


