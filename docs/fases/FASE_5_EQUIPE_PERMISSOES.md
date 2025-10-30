# FASE 5: Equipe e Permissões - Implementação Completa

## 📋 Resumo

Sistema completo de gestão de equipe multi-tenant com roles, permissões e convites por email.

**Status:** ✅ **IMPLEMENTADO**

---

## 🗂️ Arquivos Criados/Modificados

### Models (`apps/accounts/models.py`)

**TenantMembership:**
```python
class TenantMembership(models.Model):
    """Membership de usuário em um tenant."""
    
    # Roles disponíveis
    ROLE_CHOICES = [
        ('owner', 'Owner'),       # Acesso total + billing
        ('admin', 'Administrator'), # Acesso total exceto billing
        ('operator', 'Operator'),   # Read/write assets
        ('viewer', 'Viewer'),       # Read-only
    ]
    
    user = ForeignKey(User)
    tenant = ForeignKey(Tenant)
    role = CharField(choices=ROLE_CHOICES)
    status = CharField(choices=['active', 'inactive', 'suspended'])
    invited_by = ForeignKey(User, null=True)
    joined_at = DateTimeField(auto_now_add=True)
```

**Invite:**
```python
class Invite(models.Model):
    """Convite para ingressar em um tenant."""
    
    tenant = ForeignKey(Tenant)
    invited_by = ForeignKey(User)
    email = EmailField()
    role = CharField(choices=TenantMembership.ROLE_CHOICES)
    token = CharField(max_length=64, unique=True)
    status = CharField(choices=['pending', 'accepted', 'expired', 'cancelled'])
    message = TextField(blank=True, null=True)
    expires_at = DateTimeField()  # Padrão: 7 dias
    accepted_at = DateTimeField(null=True, blank=True)
```

### Serializers (`apps/accounts/serializers_team.py`)

- `TenantMembershipSerializer` - Listar membros
- `UpdateMembershipSerializer` - Atualizar role/status
- `InviteSerializer` - Listar convites
- `CreateInviteSerializer` - Criar convite (com validações)
- `AcceptInviteSerializer` - Aceitar convite via token
- `TeamStatsSerializer` - Estatísticas da equipe

### Permissions (`apps/accounts/permissions.py`)

- `IsTenantMember` - Usuário é membro ativo do tenant
- `CanManageTeam` - Owner ou Admin (gerenciar equipe)
- `CanWrite` - Owner, Admin ou Operator (escrita)
- `IsOwner` - Apenas Owner (ações críticas)
- `IsOwnerOrReadOnly` - Owner para escrita, outros read-only
- `RoleBasedPermission` - Permissão flexível por roles

### Views (`apps/accounts/views_team.py`)

**TeamMemberViewSet:**
- `GET /api/team/members/` - Listar membros
- `GET /api/team/members/{id}/` - Detalhes do membro
- `PATCH /api/team/members/{id}/` - Atualizar role/status
- `DELETE /api/team/members/{id}/` - Remover membro (soft delete)
- `GET /api/team/members/stats/` - Estatísticas da equipe

**InviteViewSet:**
- `GET /api/team/invites/` - Listar convites
- `POST /api/team/invites/` - Criar convite (envia email)
- `DELETE /api/team/invites/{id}/` - Cancelar convite
- `POST /api/team/invites/accept/` - Aceitar convite via token
- `POST /api/team/invites/{id}/resend/` - Reenviar email

### Templates de Email

**`apps/accounts/templates/emails/team_invite.txt`** - Email texto simples
**`apps/accounts/templates/emails/team_invite.html`** - Email HTML estilizado

---

## 🔐 Sistema de Permissões

### Hierarquia de Roles

```
Owner (Proprietário)
├─ Acesso total
├─ Pode deletar tenant
├─ Gerencia billing
└─ Gerencia equipe

Admin (Administrador)
├─ Acesso total exceto billing/delete tenant
├─ Gerencia equipe
└─ CRUD completo em assets/sensors

Operator (Operador)
├─ Read/write em assets
├─ Read/write em sensors
└─ Não gerencia equipe

Viewer (Visualizador)
└─ Apenas leitura em tudo
```

### Uso nas Views

```python
from apps.accounts.permissions import CanWrite, CanManageTeam

class AssetViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, CanWrite]
    # Owner, Admin, Operator podem criar/editar
    # Viewer só pode visualizar

class TeamMemberViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, CanManageTeam]
    # Apenas Owner e Admin podem gerenciar equipe
```

---

## 📧 Fluxo de Convites

### 1. Criar Convite

```bash
POST /api/team/invites/
{
  "email": "joao@example.com",
  "role": "operator",
  "message": "Bem-vindo à equipe!"
}
```

**Sistema:**
1. Valida email (não pode já ser membro)
2. Gera token seguro (32 bytes)
3. Define expiração (7 dias)
4. Envia email com link de aceitação

### 2. Aceitar Convite

```bash
POST /api/team/invites/accept/
{
  "token": "abc123..."
}
```

**Sistema:**
1. Valida token
2. Verifica expiração
3. Cria TenantMembership
4. Marca convite como aceito

### 3. Cancelar/Reenviar

```bash
# Cancelar
DELETE /api/team/invites/{id}/

# Reenviar email
POST /api/team/invites/{id}/resend/
```

---

## 🧪 Testes

### Criar Tenant e Owner

```python
python manage.py shell

from apps.tenants.models import Tenant, Domain
from apps.accounts.models import User, TenantMembership
from django_tenants.utils import schema_context

# Criar tenant
tenant = Tenant.objects.create(
    name="UMC Hospital",
    slug="umc",
    schema_name="umc"
)

# Criar domínio
Domain.objects.create(
    domain="umc.localhost",
    tenant=tenant,
    is_primary=True
)

# Criar usuário owner
user = User.objects.create_user(
    username="admin",
    email="admin@umc.com",
    password="admin123",
    first_name="Admin",
    last_name="UMC"
)

# Criar membership como owner
TenantMembership.objects.create(
    user=user,
    tenant=tenant,
    role="owner",
    status="active"
)
```

### Testar Endpoints

```bash
# Login
curl -X POST http://umc.localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username_or_email":"admin@umc.com","password":"admin123"}'

# Listar membros
curl http://umc.localhost:8000/api/team/members/ \
  -H "Cookie: access_token=..."

# Convidar membro
curl -X POST http://umc.localhost:8000/api/team/invites/ \
  -H "Cookie: access_token=..." \
  -H "Content-Type: application/json" \
  -d '{"email":"joao@example.com","role":"operator","message":"Bem-vindo!"}'

# Estatísticas da equipe
curl http://umc.localhost:8000/api/team/members/stats/ \
  -H "Cookie: access_token=..."
```

---

## 🔧 Configuração Necessária

### Settings

```python
# config/settings/base.py

# Frontend URL para links de convite
FRONTEND_URL = env('FRONTEND_URL', default='http://localhost:5173')

# Email (desenvolvimento com Mailpit)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'localhost'
EMAIL_PORT = 1025
EMAIL_USE_TLS = False
DEFAULT_FROM_EMAIL = 'noreply@traksense.com'

# Produção (SendGrid, AWS SES, etc.)
# EMAIL_HOST = 'smtp.sendgrid.net'
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True
# EMAIL_HOST_USER = 'apikey'
# EMAIL_HOST_PASSWORD = env('SENDGRID_API_KEY')
```

### Migração

```bash
# Aplicar migrações
python manage.py migrate_schemas

# Ou apenas no public schema
python manage.py migrate_schemas --schema=public
```

---

## 📊 API Endpoints Completos

### Team Members

| Método | Endpoint | Descrição | Permissão |
|--------|----------|-----------|-----------|
| GET | `/api/team/members/` | Listar membros | Owner/Admin |
| GET | `/api/team/members/{id}/` | Detalhes do membro | Owner/Admin |
| PATCH | `/api/team/members/{id}/` | Atualizar role/status | Owner/Admin |
| DELETE | `/api/team/members/{id}/` | Remover membro | Owner/Admin |
| GET | `/api/team/members/stats/` | Estatísticas | Owner/Admin |

### Invites

| Método | Endpoint | Descrição | Permissão |
|--------|----------|-----------|-----------|
| GET | `/api/team/invites/` | Listar convites | Owner/Admin |
| POST | `/api/team/invites/` | Criar convite | Owner/Admin |
| GET | `/api/team/invites/{id}/` | Detalhes do convite | Owner/Admin |
| DELETE | `/api/team/invites/{id}/` | Cancelar convite | Owner/Admin |
| POST | `/api/team/invites/accept/` | Aceitar convite | Autenticado |
| POST | `/api/team/invites/{id}/resend/` | Reenviar email | Owner/Admin |

---

## 🎯 Próximos Passos

### Frontend (React)

1. **Página Team** (`/team`)
   - Lista de membros com role badges
   - Botão "Convidar Membro"
   - Editar role de membros
   - Remover membros

2. **Modal de Convite**
   - Input de email
   - Seletor de role
   - Campo de mensagem opcional
   - Botão enviar

3. **Página Aceitar Convite** (`/accept-invite?token=...`)
   - Exibe detalhes do convite
   - Botão "Aceitar Convite"
   - Redireciona para login se não autenticado

4. **Lista de Convites Pendentes**
   - Filtro por status
   - Botão reenviar
   - Botão cancelar

### Melhorias Futuras

- [ ] Notificações in-app ao aceitar convite
- [ ] Histórico de mudanças de role
- [ ] Limite de membros por plano
- [ ] Aprovação em dois fatores para convites
- [ ] Integração com SSO (SAML, OAuth)

---

## ✅ Checklist de Entrega

- [x] Models TenantMembership e Invite criados
- [x] Serializers completos com validações
- [x] Permissions por role (Owner, Admin, Operator, Viewer)
- [x] ViewSets para members e invites
- [x] Endpoints de CRUD completos
- [x] Sistema de tokens para convites
- [x] Templates de email (HTML + texto)
- [x] Validação de último owner
- [x] Soft delete de memberships
- [x] Estatísticas da equipe
- [x] Documentação completa

---

**Data de Conclusão:** {{ "now"|date:"d/m/Y" }}
**Status:** ✅ FASE 5 COMPLETA - Pronto para integração frontend
