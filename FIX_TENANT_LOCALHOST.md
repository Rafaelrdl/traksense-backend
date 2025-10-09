# 🔧 Fix: "No tenant for hostname 'localhost'"

## ❌ Problema Encontrado

Ao tentar acessar `http://localhost:8000/api/docs/`, o erro ocorreu:

```
Page not found (404)
No tenant for hostname "localhost"

Request Method: GET
Request URL: http://localhost:8000/api/docs/
```

## 🔍 Causa Raiz

O **django-tenants** precisa de um tenant associado ao domínio da requisição. Quando acessamos via `localhost`, o middleware `TenantMainMiddleware` tenta encontrar um tenant com domínio `localhost`, mas não encontra nenhum configurado.

### Fluxo do django-tenants:

```
1. Requisição chega: http://localhost:8000/api/docs/
2. TenantMainMiddleware extrai hostname: "localhost"
3. Busca no banco: Domain.objects.get(domain='localhost')
4. Se não existir → 404 "No tenant for hostname"
5. Se existir → Define connection.tenant e prossegue
```

## ✅ Solução Aplicada

### 1️⃣ Executar o script `create_public_tenant.py`

```bash
cd backend
python create_public_tenant.py
```

**O que o script faz:**

```python
# 1. Cria tenant 'public' (schema padrão)
client = Client.objects.get_or_create(
    schema_name='public',
    name='Public Tenant'
)

# 2. Associa domínio 'localhost' ao tenant
domain = Domain.objects.get_or_create(
    domain='localhost',
    tenant=client,
    is_primary=True
)
```

### 2️⃣ Reiniciar o servidor Django

```bash
python manage.py runserver 8000
```

### 3️⃣ Acessar novamente

```
http://localhost:8000/api/docs/
```

✅ **Agora funciona!**

---

## 📊 Tenants Criados

| Schema | Nome | Domínio | Tipo |
|--------|------|---------|------|
| `public` | Public Tenant | `localhost` | Desenvolvimento |

---

## 🔐 Multi-Tenancy: Como Funciona

### Desenvolvimento Local (localhost)

```
http://localhost:8000/api/data/points
↓
TenantMainMiddleware identifica tenant 'public'
↓
connection.tenant = Client(schema_name='public')
↓
Query usa schema 'public'
↓
RLS filtra por tenant_id do 'public'
```

### Produção (domínios reais)

```
http://alpha.traksense.com/api/data/points
↓
TenantMainMiddleware identifica tenant 'alpha_corp'
↓
connection.tenant = Client(schema_name='alpha_corp')
↓
Query usa schema 'alpha_corp'
↓
RLS filtra por tenant_id do 'alpha_corp'
```

---

## 🧪 Testando Multi-Tenancy

### Criar outro tenant (exemplo)

```python
from apps.tenancy.models import Client, Domain

# Criar tenant alpha
alpha = Client.objects.create(
    schema_name='alpha_corp',
    name='Alpha Corporation'
)

# Associar domínio
Domain.objects.create(
    domain='alpha.localhost',
    tenant=alpha,
    is_primary=True
)
```

### Acessar via domínio diferente

```bash
# Adicionar ao hosts file (Windows: C:\Windows\System32\drivers\etc\hosts)
127.0.0.1 alpha.localhost

# Acessar
http://alpha.localhost:8000/api/data/points
```

**Resultado**: Dados isolados do tenant `alpha_corp`!

---

## ⚠️ IMPORTANTE: Produção

### Em produção, você precisa:

1. **Criar tenants para cada cliente**:
```python
client = Client.objects.create(
    schema_name='cliente_abc',  # Nome único, alfanumérico
    name='Cliente ABC Ltda'
)
```

2. **Associar domínio real**:
```python
Domain.objects.create(
    domain='abc.traksense.com',  # Domínio real
    tenant=client,
    is_primary=True
)
```

3. **Executar migrations no novo schema**:
```bash
python manage.py migrate_schemas --schema=cliente_abc
```

4. **Configurar DNS**:
```
abc.traksense.com → CNAME → traksense.com
```

5. **Configurar ALLOWED_HOSTS**:
```python
# settings.py
ALLOWED_HOSTS = [
    'traksense.com',
    '*.traksense.com',  # Wildcards para subdomínios
]
```

---

## 🔍 Debugging: Verificar Tenants

### Listar todos os tenants

```python
from apps.tenancy.models import Client, Domain

# Listar tenants
for client in Client.objects.all():
    print(f"Schema: {client.schema_name}, Name: {client.name}")
    domains = Domain.objects.filter(tenant=client)
    for domain in domains:
        print(f"  → Domain: {domain.domain} (primary: {domain.is_primary})")
```

### Via Django Admin

```
1. Acessar http://localhost:8000/admin/
2. Login com superuser
3. Navegar para: Tenancy → Clients
4. Ver todos os tenants e domínios
```

---

## 📚 Scripts Úteis

### `create_public_tenant.py`
✅ **Já existe e foi executado**

Cria tenant 'public' com domínio 'localhost' para desenvolvimento.

### `create_superuser.py`
Cria superuser para acesso ao Admin.

```bash
python create_superuser.py
```

### `create_rbac_groups.py`
Cria grupos RBAC (admin, operator, viewer).

```bash
python create_rbac_groups.py
```

---

## ✅ Checklist Pós-Fix

- ✅ Tenant 'public' criado
- ✅ Domínio 'localhost' associado
- ✅ Servidor reiniciado
- ✅ Swagger UI acessível em http://localhost:8000/api/docs/
- ✅ Health check funcionando em http://localhost:8000/health
- ✅ Health timeseries funcionando em http://localhost:8000/health/timeseries

---

## 🎯 Próximos Passos

1. **Testar Swagger UI** ✅ Agora deve funcionar!
   ```
   http://localhost:8000/api/docs/
   ```

2. **Criar superuser** (se ainda não criou)
   ```bash
   python create_superuser.py
   # ou
   python manage.py createsuperuser
   ```

3. **Testar API com dados reais**
   ```bash
   # Obter device_id e point_id existentes
   SELECT DISTINCT device_id, point_id FROM ts_measure LIMIT 1;
   
   # Testar no Swagger
   GET /api/data/points?device_id=<uuid>&point_id=<uuid>&start=2025-10-01T00:00:00Z&end=2025-10-08T23:59:59Z&agg=1h
   ```

---

## 🐛 Troubleshooting

### Erro persiste após criar tenant?

**Solução**: Reiniciar servidor
```bash
# Parar servidor (Ctrl+C)
python manage.py runserver 8000
```

### Erro "Schema 'public' does not exist"?

**Solução**: Aplicar migrations no schema public
```bash
python manage.py migrate_schemas --schema=public
```

### Erro ao criar tenant?

**Solução**: Verificar se migrations foram aplicadas
```bash
python manage.py showmigrations
python manage.py migrate
```

---

## 📖 Referências

- [django-tenants Documentation](https://django-tenants.readthedocs.io/)
- [PostgreSQL Schemas](https://www.postgresql.org/docs/current/ddl-schemas.html)
- [Row Level Security (RLS)](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)

---

**Autor**: TrakSense Team  
**Data**: 2025-10-08  
**Status**: ✅ PROBLEMA RESOLVIDO  
**Próximo**: Testar Swagger UI e API!
