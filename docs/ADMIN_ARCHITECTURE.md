# Django Admin - Arquitetura Multi-Tenant

## 📋 Visão Geral

O Django Admin no TrakSense está **centralizado no schema público** (`public`) e gerencia apenas recursos compartilhados entre todos os tenants.

---

## 🏗️ Arquitetura

### **Schema Público (public)**
- **URL**: `http://localhost:8000/admin/`
- **Propósito**: Administração centralizada de recursos compartilhados
- **Acesso**: Superusers criados no schema público
- **Modelos Disponíveis**:
  - ✅ **Tenants** (`tenants.Tenant`) - Gerenciamento de tenants
  - ✅ **Domains** (`tenants.Domain`) - Mapeamento de domínios → tenants
  - ✅ **Users** (`auth.User`) - Usuários administrativos globais
  - ✅ **Groups** (`auth.Group`) - Grupos de permissões

### **Schemas de Tenants** (ex: `uberlandia_medical_center`)
- **URL**: `http://<tenant-domain>:8000/admin/` → **❌ BLOQUEADO (404)**
- **Propósito**: Dados específicos do tenant (não acessíveis via admin)
- **Modelos**:
  - ❌ **Telemetry** (`ingest.Telemetry`) - Dados de telemetria MQTT (apenas via API)
  - ❌ **Users** (tenant-específicos) - Usuários do aplicativo (não admin)

---

## 🔐 Autenticação

### **Superuser no Schema Público**
```bash
# Criado via management command
docker exec traksense-api python manage.py createsuperuser --noinput \
  --username admin --email admin@traksense.com
```

**Credenciais Atuais**:
- **Username**: `admin`
- **Password**: `Admin@123456`
- **Schema**: `public`
- **Acesso**: `http://localhost:8000/admin/`

### **Usuários de Tenant** (owner@umc.localhost)
- **Criados via**: `seed_dev.py`
- **Schema**: `uberlandia_medical_center` (ou outro tenant)
- **Propósito**: Acesso ao aplicativo web (não ao admin)
- **❌ NÃO PODE** acessar o admin centralizado

---

## 🛡️ Segurança

### **Middleware de Bloqueio** (`BlockTenantAdminMiddleware`)
```python
# apps/common/middleware.py
class BlockTenantAdminMiddleware:
    def __call__(self, request):
        if request.path.startswith("/admin/"):
            if getattr(connection, "schema_name", None) != "public":
                return HttpResponseNotFound()  # 404 para tenants
        return self.get_response(request)
```

**Validação**:
```bash
# ✅ Public schema - Admin disponível
curl -I http://localhost:8000/admin/
# HTTP/1.1 302 Found (redirect para login)

# ❌ Tenant schema - Admin bloqueado
curl -I http://umc.localhost:8000/admin/
# HTTP/1.1 404 Not Found
```

---

## 🎨 Tema Jazzmin

### **Configuração** (`config/settings/base.py`)
```python
SHARED_APPS = [
    'django_tenants',
    'apps.accounts',
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'jazzmin',  # ⚠️ DEVE vir ANTES de django.contrib.admin
    'django.contrib.admin',  # ✅ Apenas em SHARED_APPS
    # ...
]

TENANT_APPS = [
    # ... NOTA: django.contrib.admin NÃO está aqui
    'apps.ingest',  # Telemetry (tenant-específico)
]
```

### **Static Files** (WhiteNoise)
```python
MIDDLEWARE = [
    'django_tenants.middleware.main.TenantMainMiddleware',
    'apps.common.middleware.BlockTenantAdminMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # ← Serve CSS/JS em produção
    # ...
]

STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}
```

**Coletar arquivos estáticos**:
```bash
docker exec traksense-api python manage.py collectstatic --noinput --clear
# 223 static files copied, 631 post-processed
```

---

## 📊 Modelos Registrados no Admin

### ✅ **TenantAdmin** (`apps/tenants/admin.py`)
- **List Display**: Nome, schema, domínios, status
- **Features**:
  - Badge de status (ativo/inativo)
  - Contador de domínios
  - Link para domínios relacionados
  - Filtros por data de criação/atualização

### ✅ **DomainAdmin** (`apps/tenants/admin.py`)
- **List Display**: Domain, tenant, schema, primary
- **Features**:
  - Badge de schema
  - Badge de primary domain
  - Link para tenant relacionado
  - Filtros por tenant/primary

### ❌ **TelemetryAdmin** (DESABILITADO)
```python
# apps/ingest/admin.py
# @admin.register(Telemetry)  # ← COMENTADO
class TelemetryAdmin(admin.ModelAdmin):
    # ...
```

**Motivo**: `Telemetry` está em `TENANT_APPS`, não existe no schema `public`.  
**Erro sem desabilitar**:
```
ProgrammingError: relation "telemetry" does not exist
LINE 1: SELECT COUNT(*) AS "__count" FROM "telemetry"
```

**Solução**: Desabilitar registro no admin centralizado. Telemetria deve ser acessada via:
- API REST (tenant-específica)
- Interface web do aplicativo (tenant-específica)
- Consultas diretas ao banco (via schema do tenant)

---

## 🔧 Troubleshooting

### **Problema: Tema não renderiza (CSS/JS não carregam)**
**Causa**: Gunicorn não serve arquivos estáticos automaticamente.  
**Solução**:
1. Instalar WhiteNoise: `pip install whitenoise==6.6.0`
2. Adicionar middleware: `whitenoise.middleware.WhiteNoiseMiddleware`
3. Configurar storage: `CompressedManifestStaticFilesStorage`
4. Coletar static: `python manage.py collectstatic --noinput --clear`
5. Hard refresh no navegador: `Ctrl + Shift + R`

### **Problema: Erro "relation telemetry does not exist"**
**Causa**: `TelemetryAdmin` registrado no admin do schema público, mas tabela só existe em schemas de tenants.  
**Solução**: Desabilitar `@admin.register(Telemetry)` em `apps/ingest/admin.py`.

### **Problema: Login falha com credenciais corretas**
**Causa**: Usuário criado em schema de tenant, mas admin está em schema público.  
**Solução**: Criar superuser no schema público:
```bash
docker exec -it traksense-api python manage.py createsuperuser \
  --noinput --username admin --email admin@traksense.com
# Depois definir senha via shell Django
```

### **Problema: Admin acessível em tenant domains**
**Causa**: `BlockTenantAdminMiddleware` não configurado.  
**Solução**: Adicionar middleware após `TenantMainMiddleware` em `MIDDLEWARE`.

---

## 📁 Arquivos Relacionados

```
traksense-backend/
├── config/
│   ├── settings/
│   │   └── base.py              # SHARED_APPS, TENANT_APPS, Jazzmin config
│   ├── urls.py                  # URLConf para tenants (sem admin)
│   └── urls_public.py           # URLConf para public (com admin)
├── apps/
│   ├── common/
│   │   └── middleware.py        # BlockTenantAdminMiddleware
│   ├── tenants/
│   │   └── admin.py             # TenantAdmin, DomainAdmin
│   └── ingest/
│       └── admin.py             # TelemetryAdmin (DESABILITADO)
└── requirements.txt             # django-jazzmin, whitenoise
```

---

## 🚀 Como Acessar

1. **Acesse**: http://localhost:8000/admin/
2. **Login**:
   - Username: `admin`
   - Password: `Admin@123456`
3. **Explore**:
   - 📦 **Tenants**: Gerenciar organizações
   - 🌐 **Domains**: Mapear domínios → tenants
   - 👤 **Users**: Usuários administrativos globais

---

## 📝 Notas Importantes

1. **Admin é GLOBAL**: Gerencia recursos compartilhados entre TODOS os tenants
2. **Dados de tenants NÃO estão no admin**: Use API REST ou interface web
3. **Telemetria é tenant-específica**: Não acessível via admin centralizado
4. **WhiteNoise é ESSENCIAL**: Sem ele, tema não renderiza em produção (Gunicorn)
5. **Superusers separados**: Admin global (public) ≠ Usuários de aplicativo (tenant)

---

## ✅ Validações

```bash
# Admin público acessível
curl -I http://localhost:8000/admin/
# HTTP/1.1 302 Found

# Admin bloqueado em tenants
curl -I http://umc.localhost:8000/admin/
# HTTP/1.1 404 Not Found

# Static files sendo servidos
curl -I http://localhost:8000/static/jazzmin/css/main.css
# HTTP/1.1 200 OK

# Admin LTE CSS disponível
curl -I http://localhost:8000/static/vendor/adminlte/css/adminlte.min.css
# HTTP/1.1 200 OK
```

---

**Última atualização**: 17/10/2025  
**Versões**: Django 5.0.1 | django-tenants 3.6.1 | django-jazzmin 3.0.0 | whitenoise 6.6.0
