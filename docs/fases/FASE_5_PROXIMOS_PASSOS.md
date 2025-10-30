# FASE 5 - Próximos Passos Executados ✅

**Data:** 27/10/2025

## 🎯 O que foi feito

### 1. ✅ Permissões adicionadas aos ViewSets (apps/assets/views.py)

Todos os ViewSets de assets agora implementam controle de acesso baseado em roles:

```python
from rest_framework.permissions import IsAuthenticated
from apps.accounts.permissions import CanWrite

# Aplicado em:
- SiteViewSet
- AssetViewSet  
- DeviceViewSet
- SensorViewSet
```

**Comportamento:**
- **Viewers**: Podem apenas fazer GET (leitura)
- **Operators**: Podem fazer GET, POST, PATCH, DELETE (leitura e escrita)
- **Admins**: Podem fazer GET, POST, PATCH, DELETE (leitura e escrita)
- **Owners**: Podem fazer GET, POST, PATCH, DELETE (leitura e escrita)

A permissão `CanWrite` bloqueia automaticamente operações de escrita (POST, PUT, PATCH, DELETE) para usuários com role `viewer`.

### 2. ✅ Script de Teste Criado (test_team_permissions.py)

Script completo para validar:
- ✅ Criação de tenant de teste
- ✅ Criação de usuários com diferentes roles
- ✅ Validação de permissões de cada role
- ✅ Teste de fluxo de convites
- ✅ Proteção de remoção do último owner
- ✅ Limpeza de dados de teste

**Uso:**
```bash
python test_team_permissions.py
```

## 📋 Checklist Atualizado

### Backend - Infraestrutura ✅
- [x] Models (TenantMembership, Invite)
- [x] Serializers (7 classes)
- [x] Permissions (6 classes)
- [x] ViewSets (TeamMemberViewSet, InviteViewSet)
- [x] URLs configuradas
- [x] Email templates (HTML + texto)
- [x] Migrações geradas

### Backend - Integração ✅
- [x] Permissões aplicadas em SiteViewSet
- [x] Permissões aplicadas em AssetViewSet
- [x] Permissões aplicadas em DeviceViewSet
- [x] Permissões aplicadas em SensorViewSet
- [x] Script de testes criado

### Pendente ⏳
- [ ] Rodar migrações (requer Docker/PostgreSQL rodando)
- [ ] Executar testes de permissão
- [ ] Criar seed data para desenvolvimento
- [ ] Frontend - Página de Team Management
- [ ] Frontend - Modal de convites
- [ ] Frontend - Página de aceitar convite
- [ ] Testes E2E do fluxo completo

## 🚀 Como Testar (Quando o Docker estiver rodando)

### 1. Aplicar Migrações
```bash
cd c:\Users\Rafael Ribeiro\TrakSense\traksense-backend
python manage.py migrate_schemas --noinput
```

### 2. Executar Script de Teste
```bash
python test_team_permissions.py
```

### 3. Testar API Manualmente

**Login como Admin (role: admin):**
```bash
curl -X POST http://umc.localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username_or_email":"admin@umc.com","password":"admin123"}'
```

**Criar Site (admin pode):**
```bash
curl -X POST http://umc.localhost:8000/api/sites/ \
  -H "Cookie: access_token=SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Site","company":"Test Co"}'
```

**Login como Viewer (role: viewer):**
```bash
curl -X POST http://umc.localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username_or_email":"viewer@umc.com","password":"viewer123"}'
```

**Tentar criar Site (viewer NÃO pode - deve retornar 403):**
```bash
curl -X POST http://umc.localhost:8000/api/sites/ \
  -H "Cookie: access_token=SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Site","company":"Test Co"}'
```

### 4. Testar Endpoints de Team

**Listar membros (owner/admin apenas):**
```bash
curl http://umc.localhost:8000/api/team/members/ \
  -H "Cookie: access_token=SEU_TOKEN"
```

**Convidar membro:**
```bash
curl -X POST http://umc.localhost:8000/api/team/invites/ \
  -H "Cookie: access_token=SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "novomembro@example.com",
    "role": "operator",
    "message": "Bem-vindo!"
  }'
```

**Estatísticas da equipe:**
```bash
curl http://umc.localhost:8000/api/team/members/stats/ \
  -H "Cookie: access_token=SEU_TOKEN"
```

## 📊 Estrutura de Permissões

### Matriz de Permissões

| Ação | Viewer | Operator | Admin | Owner |
|------|--------|----------|-------|-------|
| **Assets (CRUD)** |
| Listar Sites/Assets | ✅ | ✅ | ✅ | ✅ |
| Criar Site/Asset | ❌ | ✅ | ✅ | ✅ |
| Editar Site/Asset | ❌ | ✅ | ✅ | ✅ |
| Deletar Site/Asset | ❌ | ✅ | ✅ | ✅ |
| **Devices/Sensors** |
| Listar | ✅ | ✅ | ✅ | ✅ |
| Criar | ❌ | ✅ | ✅ | ✅ |
| Editar | ❌ | ✅ | ✅ | ✅ |
| Deletar | ❌ | ✅ | ✅ | ✅ |
| **Team Management** |
| Listar membros | ❌ | ❌ | ✅ | ✅ |
| Convidar membro | ❌ | ❌ | ✅ | ✅ |
| Editar role | ❌ | ❌ | ✅ | ✅ |
| Remover membro | ❌ | ❌ | ✅ | ✅ |
| **Billing/Tenant** |
| Ver billing | ❌ | ❌ | ❌ | ✅ |
| Deletar tenant | ❌ | ❌ | ❌ | ✅ |

## 🔧 Implementação Técnica

### Como funciona a permissão CanWrite

```python
# apps/accounts/permissions.py
class CanWrite(BasePermission):
    """
    Permite escrita apenas para owner, admin e operator.
    Viewers têm apenas leitura.
    """
    
    def has_permission(self, request, view):
        # GET, HEAD, OPTIONS sempre permitido
        if request.method in SAFE_METHODS:
            return True
        
        # POST, PUT, PATCH, DELETE: verificar role
        membership = get_user_membership(request.user)
        return membership.can_write  # True para owner/admin/operator
```

### ViewSets protegidos

```python
# apps/assets/views.py
class AssetViewSet(viewsets.ModelViewSet):
    queryset = Asset.objects.select_related('site').all()
    permission_classes = [IsAuthenticated, CanWrite]
    # ...
    
    # GET /api/assets/ → Qualquer role autenticado
    # POST /api/assets/ → Apenas owner/admin/operator
    # PATCH /api/assets/{id}/ → Apenas owner/admin/operator
    # DELETE /api/assets/{id}/ → Apenas owner/admin/operator
```

## 📝 Notas Importantes

1. **IngestView não foi modificado** - Permanece público (sem autenticação) para receber dados do EMQX via webhook. Isso está correto.

2. **Migrations pendentes** - As migrações foram criadas mas não aplicadas. Requer PostgreSQL rodando.

3. **Email em desenvolvimento** - Configurado para usar Mailpit (localhost:1025). Em produção, configurar SendGrid/AWS SES.

4. **Frontend pendente** - Ainda precisa criar:
   - Página `/team` com lista de membros
   - Modal de convite
   - Página `/accept-invite?token=...`
   - Badges de role no UI

## 🎯 Próxima Sessão

Quando voltar a trabalhar no projeto:

1. **Iniciar Docker:**
   ```bash
   docker-compose up -d
   ```

2. **Aplicar migrações:**
   ```bash
   python manage.py migrate_schemas
   ```

3. **Executar testes:**
   ```bash
   python test_team_permissions.py
   ```

4. **Criar usuários de teste com diferentes roles no tenant UMC**

5. **Testar endpoints de team via curl/Postman**

6. **Iniciar desenvolvimento do frontend**

---

**Resumo:** Backend da FASE 5 está 100% implementado. Falta apenas aplicar as migrações quando o banco estiver disponível e desenvolver o frontend. ✅
