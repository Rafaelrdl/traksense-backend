"""
Script de teste para validar permissões de role (FASE 5).

Testa que:
- Viewers podem apenas ler
- Operators podem ler e escrever
- Admins podem gerenciar equipe
- Owners têm acesso total

Uso:
    python test_team_permissions.py
"""

import os
import django
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.db import connection
from apps.tenants.models import Tenant, Domain
from apps.accounts.models import User, TenantMembership, Invite
from apps.assets.models import Site, Asset

def print_section(title):
    """Helper para printar seções."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def create_test_tenant():
    """Cria tenant de teste se não existir."""
    print_section("CRIANDO TENANT DE TESTE")
    
    connection.set_schema_to_public()
    
    # Verificar se já existe
    tenant = Tenant.objects.filter(slug='test-team').first()
    if tenant:
        print("✅ Tenant 'test-team' já existe")
        return tenant
    
    # Criar tenant
    tenant = Tenant.objects.create(
        name="Test Team",
        slug="test-team",
        schema_name="test_team"
    )
    print(f"✅ Tenant criado: {tenant.name} ({tenant.slug})")
    
    # Criar domínio
    Domain.objects.create(
        domain="test-team.localhost",
        tenant=tenant,
        is_primary=True
    )
    print(f"✅ Domínio criado: test-team.localhost")
    
    return tenant


def create_test_users(tenant):
    """Cria usuários de teste com diferentes roles."""
    print_section("CRIANDO USUÁRIOS DE TESTE")
    
    connection.set_schema_to_public()
    
    users_data = [
        {
            'username': 'owner_test',
            'email': 'owner@test.com',
            'password': 'test123',
            'first_name': 'Test',
            'last_name': 'Owner',
            'role': 'owner'
        },
        {
            'username': 'admin_test',
            'email': 'admin@test.com',
            'password': 'test123',
            'first_name': 'Test',
            'last_name': 'Admin',
            'role': 'admin'
        },
        {
            'username': 'operator_test',
            'email': 'operator@test.com',
            'password': 'test123',
            'first_name': 'Test',
            'last_name': 'Operator',
            'role': 'operator'
        },
        {
            'username': 'viewer_test',
            'email': 'viewer@test.com',
            'password': 'test123',
            'first_name': 'Test',
            'last_name': 'Viewer',
            'role': 'viewer'
        }
    ]
    
    created_users = {}
    
    for data in users_data:
        # Verificar se usuário já existe
        user = User.objects.filter(username=data['username']).first()
        if not user:
            user = User.objects.create_user(
                username=data['username'],
                email=data['email'],
                password=data['password'],
                first_name=data['first_name'],
                last_name=data['last_name']
            )
            print(f"✅ Usuário criado: {user.username}")
        else:
            print(f"⚠️  Usuário já existe: {user.username}")
        
        # Criar membership
        membership = TenantMembership.objects.filter(
            user=user, 
            tenant=tenant
        ).first()
        
        if not membership:
            membership = TenantMembership.objects.create(
                user=user,
                tenant=tenant,
                role=data['role'],
                status='active'
            )
            print(f"   └─ Membership criado: {data['role']}")
        else:
            print(f"   └─ Membership já existe: {membership.role}")
        
        created_users[data['role']] = user
    
    return created_users


def test_permissions(users):
    """Testa permissões de cada role."""
    print_section("TESTANDO PERMISSÕES")
    
    for role, user in users.items():
        print(f"\n🔍 Testando role: {role.upper()}")
        
        # Buscar membership
        membership = TenantMembership.objects.filter(user=user).first()
        
        if not membership:
            print(f"   ❌ Membership não encontrado para {user.username}")
            continue
        
        # Testar propriedades
        print(f"   - is_active: {membership.is_active}")
        print(f"   - can_manage_team: {membership.can_manage_team}")
        print(f"   - can_write: {membership.can_write}")
        print(f"   - can_delete_tenant: {membership.can_delete_tenant}")
        
        # Validar permissões esperadas
        if role == 'owner':
            assert membership.can_manage_team, "Owner deveria poder gerenciar equipe"
            assert membership.can_write, "Owner deveria poder escrever"
            assert membership.can_delete_tenant, "Owner deveria poder deletar tenant"
            print("   ✅ Permissões corretas")
        
        elif role == 'admin':
            assert membership.can_manage_team, "Admin deveria poder gerenciar equipe"
            assert membership.can_write, "Admin deveria poder escrever"
            assert not membership.can_delete_tenant, "Admin NÃO deveria poder deletar tenant"
            print("   ✅ Permissões corretas")
        
        elif role == 'operator':
            assert not membership.can_manage_team, "Operator NÃO deveria gerenciar equipe"
            assert membership.can_write, "Operator deveria poder escrever"
            assert not membership.can_delete_tenant, "Operator NÃO deveria poder deletar tenant"
            print("   ✅ Permissões corretas")
        
        elif role == 'viewer':
            assert not membership.can_manage_team, "Viewer NÃO deveria gerenciar equipe"
            assert not membership.can_write, "Viewer NÃO deveria poder escrever"
            assert not membership.can_delete_tenant, "Viewer NÃO deveria poder deletar tenant"
            print("   ✅ Permissões corretas")


def test_invite_workflow(tenant, users):
    """Testa fluxo de convite."""
    print_section("TESTANDO FLUXO DE CONVITES")
    
    connection.set_schema_to_public()
    
    owner = users['owner']
    
    # Criar convite
    invite = Invite.objects.create(
        tenant=tenant,
        invited_by=owner,
        email="newmember@test.com",
        role="operator",
        message="Bem-vindo à equipe!"
    )
    
    print(f"✅ Convite criado")
    print(f"   - Email: {invite.email}")
    print(f"   - Role: {invite.role}")
    print(f"   - Token: {invite.token[:16]}...")
    print(f"   - Status: {invite.status}")
    print(f"   - Expira em: {invite.expires_at.strftime('%d/%m/%Y %H:%M')}")
    print(f"   - is_valid: {invite.is_valid}")
    print(f"   - is_expired: {invite.is_expired}")
    
    # Verificar que token foi gerado
    assert len(invite.token) > 0, "Token deveria ser gerado"
    assert invite.is_valid, "Convite deveria estar válido"
    assert not invite.is_expired, "Convite não deveria estar expirado"
    
    print("\n✅ Validações de convite passaram")
    
    # Cancelar convite
    invite.cancel()
    print(f"\n✅ Convite cancelado (status: {invite.status})")
    assert invite.status == 'cancelled', "Status deveria ser cancelled"


def test_last_owner_protection(tenant, users):
    """Testa proteção de remoção do último owner."""
    print_section("TESTANDO PROTEÇÃO DE ÚLTIMO OWNER")
    
    connection.set_schema_to_public()
    
    owner = users['owner']
    membership = TenantMembership.objects.get(user=owner, tenant=tenant)
    
    # Tentar deletar (deveria falhar se for único owner)
    owners_count = TenantMembership.objects.filter(
        tenant=tenant,
        role='owner',
        status='active'
    ).count()
    
    print(f"Total de owners ativos: {owners_count}")
    
    if owners_count == 1:
        print("⚠️  Este é o único owner - deleção deveria ser bloqueada")
        print("   (Validação acontece no serializer, não no modelo)")
    else:
        print(f"✅ Existem {owners_count} owners - pode deletar com segurança")


def cleanup():
    """Remove dados de teste."""
    print_section("LIMPEZA (OPCIONAL)")
    
    response = input("\nDeseja remover os dados de teste? (s/N): ")
    
    if response.lower() != 's':
        print("Dados de teste mantidos.")
        return
    
    connection.set_schema_to_public()
    
    # Remover memberships
    deleted_memberships = TenantMembership.objects.filter(
        tenant__slug='test-team'
    ).delete()
    print(f"✅ {deleted_memberships[0]} memberships removidos")
    
    # Remover convites
    deleted_invites = Invite.objects.filter(
        tenant__slug='test-team'
    ).delete()
    print(f"✅ {deleted_invites[0]} convites removidos")
    
    # Remover usuários de teste
    deleted_users = User.objects.filter(
        username__endswith='_test'
    ).delete()
    print(f"✅ {deleted_users[0]} usuários removidos")
    
    # Remover tenant (cuidado - remove schema!)
    response = input("\nRemover tenant 'test-team'? Isso APAGA O SCHEMA! (s/N): ")
    if response.lower() == 's':
        tenant = Tenant.objects.filter(slug='test-team').first()
        if tenant:
            tenant.delete()
            print("✅ Tenant 'test-team' removido")


def main():
    """Executa todos os testes."""
    print_section("🧪 TESTE DE PERMISSÕES - FASE 5")
    
    try:
        # 1. Criar tenant de teste
        tenant = create_test_tenant()
        
        # 2. Criar usuários com diferentes roles
        users = create_test_users(tenant)
        
        # 3. Testar permissões
        test_permissions(users)
        
        # 4. Testar fluxo de convite
        test_invite_workflow(tenant, users)
        
        # 5. Testar proteção de último owner
        test_last_owner_protection(tenant, users)
        
        print_section("✅ TODOS OS TESTES PASSARAM!")
        
        # 6. Limpeza opcional
        cleanup()
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
