# 📚 FASE 5: Índice de Documentação

Guia completo de todos os arquivos relacionados à FASE 5 (Equipe e Permissões).

---

## 🗂️ DOCUMENTAÇÃO

### 📄 Leitura Essencial (ordem recomendada)

1. **[FASE_5_RESUMO_EXECUTIVO.md](./FASE_5_RESUMO_EXECUTIVO.md)** ⭐
   - Resumo executivo completo
   - O que foi entregue
   - Métricas e validação
   - **Comece por aqui!**

2. **[FASE_5_EQUIPE_PERMISSOES.md](./FASE_5_EQUIPE_PERMISSOES.md)**
   - Documentação técnica detalhada
   - Arquitetura do sistema
   - Descrição de models/serializers/views
   - Configuração de email

3. **[GUIA_TESTES_FASE_5.md](./GUIA_TESTES_FASE_5.md)** 🧪
   - Guia completo de testes
   - 13 testes manuais via curl
   - Matriz de testes por role
   - Como debuggar

4. **[FASE_5_PROXIMOS_PASSOS.md](./FASE_5_PROXIMOS_PASSOS.md)**
   - Próximos passos
   - Como aplicar migrações
   - Como testar a API
   - Frontend pendente

5. **[EXECUTADO_PROXIMOS_PASSOS.md](./EXECUTADO_PROXIMOS_PASSOS.md)** ✅
   - O que foi executado
   - Alterações feitas
   - Checklist final
   - Próxima sessão

---

## 💻 CÓDIGO-FONTE

### Models
📁 `apps/accounts/models.py` (modificado)
- `TenantMembership` - Vínculo usuário-tenant com role
- `Invite` - Sistema de convites com tokens

### Serializers
📁 `apps/accounts/serializers_team.py` (novo - 150 linhas)
- `UserBasicSerializer`
- `TenantMembershipSerializer`
- `UpdateMembershipSerializer`
- `InviteSerializer`
- `CreateInviteSerializer`
- `AcceptInviteSerializer`
- `TeamStatsSerializer`

### Permissions
📁 `apps/accounts/permissions.py` (novo - 165 linhas)
- `IsTenantMember`
- `CanManageTeam`
- `CanWrite`
- `IsOwner`
- `IsOwnerOrReadOnly`
- `RoleBasedPermission`

### Views
📁 `apps/accounts/views_team.py` (novo - 235 linhas)
- `TeamMemberViewSet` - Gerenciar membros
- `InviteViewSet` - Gerenciar convites

📁 `apps/assets/views.py` (modificado)
- Permissões adicionadas a 4 ViewSets

### URLs
📁 `apps/accounts/urls.py` (modificado)
- Rotas de team management

### Migrations
📁 `apps/accounts/migrations/0005_invite_tenantmembership.py`
- Criação das tabelas

---

## 📧 TEMPLATES

### Email Templates
📁 `apps/accounts/templates/emails/`
- `team_invite.html` - Email HTML estilizado
- `team_invite.txt` - Email texto simples

---

## 🧪 SCRIPTS DE TESTE

### Testes Automatizados
📄 **[test_team_permissions.py](./test_team_permissions.py)** (270 linhas)
- Cria tenant de teste
- Cria usuários com diferentes roles
- Valida permissões
- Testa fluxo de convites
- Limpeza opcional

**Uso:**
```bash
python test_team_permissions.py
```

### Criar Usuários de Teste
📄 **[create_team_users_umc.py](./create_team_users_umc.py)** (180 linhas)
- Cria 4 usuários no tenant UMC
- Owner, Admin, Operator, Viewer
- Mostra credenciais

**Uso:**
```bash
python create_team_users_umc.py
```

---

## 📊 DIAGRAMAS E TABELAS

### Matriz de Permissões

| Ação | Viewer | Operator | Admin | Owner |
|------|--------|----------|-------|-------|
| Listar assets | ✅ | ✅ | ✅ | ✅ |
| Criar asset | ❌ | ✅ | ✅ | ✅ |
| Editar asset | ❌ | ✅ | ✅ | ✅ |
| Deletar asset | ❌ | ✅ | ✅ | ✅ |
| Gerenciar team | ❌ | ❌ | ✅ | ✅ |
| Billing | ❌ | ❌ | ❌ | ✅ |

### Hierarquia de Roles

```
👑 Owner (Proprietário)
├─ Acesso total
├─ Pode deletar tenant
├─ Gerencia billing
└─ Gerencia equipe

🔑 Admin (Administrador)
├─ Acesso total exceto billing/delete
├─ Gerencia equipe
└─ CRUD completo em assets

🔧 Operator (Operador)
├─ Read/write em assets
├─ Read/write em sensors
└─ Não gerencia equipe

👁️ Viewer (Visualizador)
└─ Apenas leitura
```

---

## 🔗 ENDPOINTS DA API

### Team Management

```
GET    /api/team/members/           # Listar membros
GET    /api/team/members/{id}/      # Detalhes do membro
PATCH  /api/team/members/{id}/      # Atualizar role/status
DELETE /api/team/members/{id}/      # Remover membro
GET    /api/team/members/stats/     # Estatísticas

GET    /api/team/invites/           # Listar convites
POST   /api/team/invites/           # Criar convite
DELETE /api/team/invites/{id}/      # Cancelar convite
POST   /api/team/invites/accept/    # Aceitar convite
POST   /api/team/invites/{id}/resend/ # Reenviar email
```

### Assets (com permissões)

```
GET    /api/sites/                  # Todas as roles
POST   /api/sites/                  # Owner/Admin/Operator
PATCH  /api/sites/{id}/             # Owner/Admin/Operator
DELETE /api/sites/{id}/             # Owner/Admin/Operator

# Mesma lógica para:
/api/assets/
/api/devices/
/api/sensors/
```

---

## 🚀 QUICK START

### 1. Iniciar Docker
```bash
docker-compose up -d
```

### 2. Aplicar Migrações
```bash
python manage.py migrate_schemas
```

### 3. Criar Usuários
```bash
python create_team_users_umc.py
```

### 4. Testar
```bash
python test_team_permissions.py
```

### 5. Testar API
```bash
# Login
curl -X POST http://umc.localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username_or_email":"admin@umc.com","password":"admin123"}'

# Listar membros
curl http://umc.localhost:8000/api/team/members/ \
  -H "Cookie: access_token=..."
```

---

## 📖 GLOSSÁRIO

**RBAC**: Role-Based Access Control - Controle de acesso baseado em roles

**Multi-Tenancy**: Arquitetura onde múltiplos clientes (tenants) compartilham a mesma aplicação

**Schema-per-tenant**: Cada tenant tem seu próprio schema no PostgreSQL

**Soft Delete**: Marcar registro como inativo ao invés de deletar do banco

**HttpOnly Cookie**: Cookie que não pode ser acessado via JavaScript (mais seguro)

**Membership**: Vínculo entre usuário e tenant com role específico

**Invite**: Convite para usuário ingressar em um tenant

**Token**: String aleatória única usada para aceitar convites

---

## ✅ CHECKLIST DE ARQUIVOS

### Código
- [x] `apps/accounts/models.py`
- [x] `apps/accounts/serializers_team.py`
- [x] `apps/accounts/permissions.py`
- [x] `apps/accounts/views_team.py`
- [x] `apps/accounts/urls.py`
- [x] `apps/assets/views.py`
- [x] `apps/accounts/migrations/0005_invite_tenantmembership.py`

### Templates
- [x] `apps/accounts/templates/emails/team_invite.html`
- [x] `apps/accounts/templates/emails/team_invite.txt`

### Scripts
- [x] `test_team_permissions.py`
- [x] `create_team_users_umc.py`

### Documentação
- [x] `FASE_5_RESUMO_EXECUTIVO.md`
- [x] `FASE_5_EQUIPE_PERMISSOES.md`
- [x] `GUIA_TESTES_FASE_5.md`
- [x] `FASE_5_PROXIMOS_PASSOS.md`
- [x] `EXECUTADO_PROXIMOS_PASSOS.md`
- [x] `FASE_5_INDICE.md` (este arquivo)

---

## 🎯 PRÓXIMOS PASSOS

### Backend (✅ COMPLETO)
- Nada pendente

### Validação (⏳ AGUARDANDO DOCKER)
- [ ] Aplicar migrações
- [ ] Executar testes
- [ ] Testar API manualmente

### Frontend (⏳ PENDENTE)
- [ ] Página Team Management
- [ ] Modal de convite
- [ ] Página aceitar convite
- [ ] Testes E2E

---

## 📞 SUPORTE

### Dúvidas?
1. Consulte `FASE_5_RESUMO_EXECUTIVO.md`
2. Veja exemplos em `GUIA_TESTES_FASE_5.md`
3. Execute `python test_team_permissions.py`

### Problemas?
1. Verifique se Docker está rodando
2. Verifique se migrações foram aplicadas
3. Consulte logs: `docker-compose logs -f backend`

---

## 📊 ESTATÍSTICAS

| Métrica | Valor |
|---------|-------|
| Total de arquivos | 15 |
| Linhas de código | ~1.200 |
| Linhas de documentação | ~1.500 |
| Endpoints criados | 10 |
| Roles implementados | 4 |
| Testes automatizados | 1 script |
| Scripts de setup | 1 script |

---

**Última atualização:** 27/10/2025 01:30 UTC-3

**Status:** ✅ Backend 100% implementado e documentado

**Próximo milestone:** Aplicar migrações + Frontend
