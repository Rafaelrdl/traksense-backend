# 🧪 Guia de Testes - FASE 5: Equipe e Permissões

## 📋 Pré-requisitos

1. **Docker rodando** (PostgreSQL, Redis, EMQX, Mailpit)
2. **Migrações aplicadas** (`python manage.py migrate_schemas`)
3. **Tenant UMC criado** (já existe)
4. **Usuários de teste criados**

---

## 🚀 Setup Inicial

### 1. Iniciar Docker

```bash
cd c:\Users\Rafael Ribeiro\TrakSense\traksense-backend
docker-compose up -d
```

Aguardar ~10 segundos para serviços inicializarem.

### 2. Aplicar Migrações

```bash
python manage.py migrate_schemas --noinput
```

Deve criar as tabelas `tenant_memberships` e `invites` em todos os schemas.

### 3. Criar Usuários de Teste

```bash
python create_team_users_umc.py
```

Cria 4 usuários com diferentes roles:
- `admin@umc.com` (owner) - senha: `admin123`
- `manager@umc.com` (admin) - senha: `manager123`
- `tech@umc.com` (operator) - senha: `tech123`
- `viewer@umc.com` (viewer) - senha: `viewer123`

### 4. Validar Permissões

```bash
python test_team_permissions.py
```

Script automatizado que:
- Cria tenant de teste
- Cria usuários com cada role
- Valida permissões de cada role
- Testa fluxo de convites
- Testa proteção de último owner

---

## 🧪 Testes Manuais via API

### Teste 1: Login e Autenticação

**Owner (acesso total):**
```bash
curl -X POST http://umc.localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username_or_email":"admin@umc.com","password":"admin123"}' \
  -c cookies.txt
```

**Admin:**
```bash
curl -X POST http://umc.localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username_or_email":"manager@umc.com","password":"manager123"}' \
  -c cookies.txt
```

**Operator:**
```bash
curl -X POST http://umc.localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username_or_email":"tech@umc.com","password":"tech123"}' \
  -c cookies.txt
```

**Viewer (apenas leitura):**
```bash
curl -X POST http://umc.localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username_or_email":"viewer@umc.com","password":"viewer123"}' \
  -c cookies.txt
```

---

### Teste 2: Team Management (Owner/Admin apenas)

**Listar membros:**
```bash
curl http://umc.localhost:8000/api/team/members/ \
  -b cookies.txt
```

**Esperado:**
- ✅ Owner: 200 OK com lista de membros
- ✅ Admin: 200 OK com lista de membros
- ❌ Operator: 403 Forbidden
- ❌ Viewer: 403 Forbidden

**Estatísticas da equipe:**
```bash
curl http://umc.localhost:8000/api/team/members/stats/ \
  -b cookies.txt
```

**Esperado:**
```json
{
  "total_members": 4,
  "members_by_role": {
    "owner": 1,
    "admin": 1,
    "operator": 1,
    "viewer": 1
  },
  "members_by_status": {
    "active": 4
  }
}
```

---

### Teste 3: Criar Convite (Owner/Admin)

**Convidar novo membro:**
```bash
curl -X POST http://umc.localhost:8000/api/team/invites/ \
  -b cookies.txt \
  -H "Content-Type: application/json" \
  -d '{
    "email": "novomembro@umc.com",
    "role": "operator",
    "message": "Bem-vindo à equipe UMC!"
  }'
```

**Esperado:**
- ✅ Owner/Admin: 201 Created com token de convite
- ❌ Operator/Viewer: 403 Forbidden

**Resposta esperada:**
```json
{
  "id": 1,
  "email": "novomembro@umc.com",
  "role": "operator",
  "status": "pending",
  "token": "abc123...",
  "expires_at": "2025-11-03T...",
  "invited_by": {
    "id": 1,
    "email": "admin@umc.com",
    "full_name": "Admin UMC"
  }
}
```

**Verificar email no Mailpit:**
1. Abrir http://localhost:8025
2. Ver email de convite
3. Copiar link de aceitação

---

### Teste 4: Listar Convites

```bash
curl http://umc.localhost:8000/api/team/invites/ \
  -b cookies.txt
```

**Esperado:**
- ✅ Owner/Admin: 200 OK com lista de convites
- ❌ Operator/Viewer: 403 Forbidden

---

### Teste 5: Aceitar Convite

```bash
curl -X POST http://umc.localhost:8000/api/team/invites/accept/ \
  -H "Content-Type: application/json" \
  -d '{"token":"TOKEN_DO_EMAIL"}'
```

**Esperado:**
- ✅ 200 OK com mensagem de sucesso
- Membership criado automaticamente
- Convite marcado como "accepted"

---

### Teste 6: Reenviar Convite

```bash
curl -X POST http://umc.localhost:8000/api/team/invites/1/resend/ \
  -b cookies.txt
```

**Esperado:**
- ✅ Owner/Admin: 200 OK, novo email enviado
- ❌ Operator/Viewer: 403 Forbidden

---

### Teste 7: Cancelar Convite

```bash
curl -X DELETE http://umc.localhost:8000/api/team/invites/1/ \
  -b cookies.txt
```

**Esperado:**
- ✅ Owner/Admin: 204 No Content
- Convite marcado como "cancelled"

---

### Teste 8: Atualizar Role de Membro

```bash
curl -X PATCH http://umc.localhost:8000/api/team/members/2/ \
  -b cookies.txt \
  -H "Content-Type: application/json" \
  -d '{"role":"admin"}'
```

**Esperado:**
- ✅ Owner/Admin: 200 OK
- ❌ Operator/Viewer: 403 Forbidden

---

### Teste 9: Remover Membro

```bash
curl -X DELETE http://umc.localhost:8000/api/team/members/3/ \
  -b cookies.txt
```

**Esperado:**
- ✅ Owner/Admin: 204 No Content (soft delete - status=inactive)
- ❌ Se for último owner: 400 Bad Request com erro
- ❌ Operator/Viewer: 403 Forbidden

---

### Teste 10: Criar Asset (Owner/Admin/Operator)

**Criar site primeiro:**
```bash
curl -X POST http://umc.localhost:8000/api/sites/ \
  -b cookies.txt \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Prédio A",
    "company": "UMC Hospital",
    "address": "Rua Test, 123",
    "city": "São Paulo",
    "state": "SP",
    "country": "Brasil",
    "timezone": "America/Sao_Paulo"
  }'
```

**Criar asset:**
```bash
curl -X POST http://umc.localhost:8000/api/assets/ \
  -b cookies.txt \
  -H "Content-Type: application/json" \
  -d '{
    "tag": "HVAC-001",
    "name": "Ar Condicionado Central",
    "site": 1,
    "asset_type": "HVAC",
    "status": "OPERATIONAL"
  }'
```

**Esperado:**
- ✅ Owner: 201 Created
- ✅ Admin: 201 Created
- ✅ Operator: 201 Created
- ❌ Viewer: 403 Forbidden

---

### Teste 11: Listar Assets (Qualquer role)

```bash
curl http://umc.localhost:8000/api/assets/ \
  -b cookies.txt
```

**Esperado:**
- ✅ Todas as roles: 200 OK com lista de assets

---

### Teste 12: Editar Asset (Owner/Admin/Operator)

```bash
curl -X PATCH http://umc.localhost:8000/api/assets/1/ \
  -b cookies.txt \
  -H "Content-Type: application/json" \
  -d '{"status":"MAINTENANCE"}'
```

**Esperado:**
- ✅ Owner/Admin/Operator: 200 OK
- ❌ Viewer: 403 Forbidden

---

### Teste 13: Deletar Asset (Owner/Admin/Operator)

```bash
curl -X DELETE http://umc.localhost:8000/api/assets/1/ \
  -b cookies.txt
```

**Esperado:**
- ✅ Owner/Admin/Operator: 204 No Content
- ❌ Viewer: 403 Forbidden

---

## 📊 Matriz de Testes

| Endpoint | Owner | Admin | Operator | Viewer |
|----------|-------|-------|----------|--------|
| **Team Management** |
| GET /team/members/ | ✅ | ✅ | ❌ | ❌ |
| POST /team/invites/ | ✅ | ✅ | ❌ | ❌ |
| PATCH /team/members/{id}/ | ✅ | ✅ | ❌ | ❌ |
| DELETE /team/members/{id}/ | ✅ | ✅ | ❌ | ❌ |
| **Assets** |
| GET /assets/ | ✅ | ✅ | ✅ | ✅ |
| POST /assets/ | ✅ | ✅ | ✅ | ❌ |
| PATCH /assets/{id}/ | ✅ | ✅ | ✅ | ❌ |
| DELETE /assets/{id}/ | ✅ | ✅ | ✅ | ❌ |
| **Sites** |
| GET /sites/ | ✅ | ✅ | ✅ | ✅ |
| POST /sites/ | ✅ | ✅ | ✅ | ❌ |
| PATCH /sites/{id}/ | ✅ | ✅ | ✅ | ❌ |
| DELETE /sites/{id}/ | ✅ | ✅ | ✅ | ❌ |
| **Devices** |
| GET /devices/ | ✅ | ✅ | ✅ | ✅ |
| POST /devices/ | ✅ | ✅ | ✅ | ❌ |
| PATCH /devices/{id}/ | ✅ | ✅ | ✅ | ❌ |
| DELETE /devices/{id}/ | ✅ | ✅ | ✅ | ❌ |
| **Sensors** |
| GET /sensors/ | ✅ | ✅ | ✅ | ✅ |
| POST /sensors/ | ✅ | ✅ | ✅ | ❌ |
| PATCH /sensors/{id}/ | ✅ | ✅ | ✅ | ❌ |
| DELETE /sensors/{id}/ | ✅ | ✅ | ✅ | ❌ |

---

## 🐛 Debugging

### Ver logs do backend:
```bash
docker-compose logs -f backend
```

### Ver emails enviados:
http://localhost:8025

### Verificar PostgreSQL:
```bash
docker exec -it traksense-postgres psql -U app -d app
\c app
SET search_path TO umc, public;
SELECT * FROM tenant_memberships;
SELECT * FROM invites;
```

### Verificar Redis:
```bash
docker exec -it traksense-redis redis-cli
KEYS *
```

---

## ✅ Checklist de Testes

- [ ] Migrações aplicadas sem erros
- [ ] 4 usuários criados no tenant UMC
- [ ] Script test_team_permissions.py passou
- [ ] Login funciona para todas as roles
- [ ] Owner pode listar membros
- [ ] Admin pode listar membros
- [ ] Operator NÃO pode listar membros (403)
- [ ] Viewer NÃO pode listar membros (403)
- [ ] Owner pode criar convite
- [ ] Admin pode criar convite
- [ ] Email de convite enviado (verificar Mailpit)
- [ ] Convite pode ser aceito via token
- [ ] Owner pode criar asset
- [ ] Admin pode criar asset
- [ ] Operator pode criar asset
- [ ] Viewer NÃO pode criar asset (403)
- [ ] Todas as roles podem listar assets
- [ ] Viewer NÃO pode editar asset (403)
- [ ] Viewer NÃO pode deletar asset (403)
- [ ] Não pode remover último owner (400)

---

## 📝 Notas

- **Cookies:** Use `-c cookies.txt` para salvar cookies e `-b cookies.txt` para usar
- **Headers:** O token JWT fica em HttpOnly cookie (mais seguro)
- **Tenant:** Detectado automaticamente via subdomínio (`umc.localhost`)
- **CORS:** Configurado para aceitar `http://localhost:5173` (frontend)

---

**Última atualização:** 27/10/2025
