# 📋 Plano de Validação REAL - Fase 2

## ⚠️ NOTA IMPORTANTE
Este é um plano de validação **FUNCIONAL**. Cada item será marcado como ✅ **SOMENTE APÓS** execução e verificação dos resultados.

---

## 🔄 Sequência de Inicialização (django-tenants)

### Entendimento do Fluxo:

1. **django-tenants** usa schemas PostgreSQL para multi-tenancy
2. **SHARED_APPS** → vão para o schema `public`
3. **TENANT_APPS** → vão para schemas individuais (ex: `test_alpha`, `test_beta`)
4. Comandos especiais:
   - `migrate_schemas --shared` → migra apenas SHARED_APPS (public)
   - `migrate_schemas --tenant` → migra TENANT_APPS em todos os schemas de tenants
   - `migrate_schemas` → migra TUDO

---

## ✅ Passo 1: Verificar Infraestrutura

### 1.1. Containers rodando
```powershell
docker compose -f infra/docker-compose.yml ps
```

**Esperado:** 4-5 containers UP (db, redis, api, emqx, [ingest])

- [x] Containers rodando (api, db, emqx, redis - UP)
- [x] Sem erros nos logs (após aguardar inicialização do banco)

### 1.2. Banco de dados acessível
```powershell
docker compose -f infra/docker-compose.yml exec db psql -U postgres -d traksense -c "\l"
```

**Esperado:** Lista de bancos incluindo `traksense`

- [x] Banco `traksense` existe (verificado via \l)
- [x] Conexão funcionando (PostgreSQL acessível)

### 1.3. TimescaleDB instalado
```powershell
docker compose -f infra/docker-compose.yml exec db psql -U postgres -d traksense -c "SELECT extname, extversion FROM pg_extension WHERE extname = 'timescaledb'"
```

**Esperado:** `timescaledb | <versão>`

- [x] Extensão TimescaleDB instalada (versão 2.22.1 verificada)

---

## ✅ Passo 2: Verificar Configuração Django

### 2.1. Verificar settings.py
```powershell
docker compose -f infra/docker-compose.yml exec api python manage.py shell
```

```python
from django.conf import settings

# 1. SHARED_APPS
print("SHARED_APPS:", settings.SHARED_APPS)
# Deve conter: django_tenants, tenancy, timeseries, health

# 2. TENANT_APPS
print("TENANT_APPS:", settings.TENANT_APPS)
# Deve conter: devices, dashboards, rules, commands

# 3. MIDDLEWARE
print("MIDDLEWARE:", [m for m in settings.MIDDLEWARE if 'Tenant' in m])
# Deve ter: TenantMainMiddleware (primeiro) e TenantGucMiddleware (último)

# 4. TENANT_MODEL
print("TENANT_MODEL:", settings.TENANT_MODEL)
# Deve ser: 'tenancy.Client'

# 5. TENANT_DOMAIN_MODEL
print("TENANT_DOMAIN_MODEL:", settings.TENANT_DOMAIN_MODEL)
# Deve ser: 'tenancy.Domain'

exit()
```

- [x] SHARED_APPS configurado corretamente (['django_tenants', 'apps.tenancy', 'apps.timeseries', 'health', ...])
- [x] TENANT_APPS configurado corretamente (['apps.devices', 'apps.dashboards', 'apps.rules', 'apps.commands'])
- [x] MIDDLEWARE com TenantMainMiddleware primeiro
- [x] MIDDLEWARE com TenantGucMiddleware último
- [x] TENANT_MODEL = 'tenancy.Client' (verificado)
- [x] TENANT_DOMAIN_MODEL = 'tenancy.Domain' (verificado)

---

## ✅ Passo 3: Executar Migrações (SHARED)

### 3.1. Gerar migrações para apps de Fase 2
```powershell
# Gerar migrations para devices
docker compose -f infra/docker-compose.yml exec api python manage.py makemigrations devices

# Gerar migrations para dashboards
docker compose -f infra/docker-compose.yml exec api python manage.py makemigrations dashboards
```

**Esperado:** 
- `0001_initial.py` criado em `backend/apps/devices/migrations/`
- `0001_initial.py` criado em `backend/apps/dashboards/migrations/`

- [x] Migration devices/0001_initial.py criada (4 modelos: Device, DeviceTemplate, PointTemplate, Point + 3 constraints)
- [x] Migration dashboards/0001_initial.py criada (2 modelos: DashboardTemplate, DashboardConfig)
- [x] Migration tenancy/0001_initial.py criada (2 modelos: Client, Domain + índice)

### 3.2. Aplicar migrações SHARED (schema public)
```powershell
docker compose -f infra/docker-compose.yml exec api python manage.py migrate_schemas --shared
```

**Esperado:** 
- Tabelas do SHARED_APPS criadas no schema `public`
- Inclui: `tenancy_client`, `tenancy_domain`, `ts_measure`

- [x] Comando executou sem erros (17 migrations aplicadas)
- [x] Tabelas criadas no schema public (auth, admin, sessions, tenancy, timeseries, dashboards)

### 3.3. Verificar tabelas no schema public
```powershell
docker compose -f infra/docker-compose.yml exec db psql -U postgres -d traksense -c "\dt public.*"
```

**Esperado:** 
- `public.tenancy_client`
- `public.tenancy_domain`
- `public.ts_measure` (hypertable)
- Tabelas do Django Auth
- Tabelas do Django Admin

- [x] Tabelas criadas conforme esperado (incluindo tenancy_client, tenancy_domain, auth_*, admin_*, sessions_*, ts_measure)

---

## ✅ Passo 4: Criar Tenants de Teste

### 4.1. Criar tenant 'public' (obrigatório para django-tenants)
```powershell
docker compose -f infra/docker-compose.yml exec api python backend/create_public_tenant.py
```

**Esperado:** Tenant `public` com schema `public` criado

- [x] Tenant public criado (UUID: 1, via Django shell)
- [x] Domain `localhost` criado e associado ao tenant public

### 4.2. Criar tenant de teste 'alpha'
```powershell
docker compose -f infra/docker-compose.yml exec api python manage.py shell
```

```python
from apps.tenancy.models import Client, Domain

# Criar tenant alpha
alpha = Client.objects.create(
    schema_name='test_alpha',
    name='Test Alpha Corp'
)
Domain.objects.create(
    domain='alpha.localhost',
    tenant=alpha,
    is_primary=True
)

print(f"✅ Tenant Alpha criado: {alpha.pk}")
exit()
```

- [ ] Tenant alpha criado ❌ **BLOQUEADO: Erro de dependência circular entre devices e dashboards**
- [ ] UUID do tenant alpha anotado: ________________

---

## ✅ Passo 5: Executar Migrações (TENANT)

### 5.1. Aplicar migrações nos schemas de tenants
```powershell
docker compose -f infra/docker-compose.yml exec api python manage.py migrate_schemas --tenant
```

**Esperado:** 
- Schema `test_alpha` criado
- Tabelas do TENANT_APPS criadas em `test_alpha`:
  - `devices_devicetemplate`
  - `devices_pointtemplate`
  - `devices_device`
  - `devices_point`
  - `dashboards_dashboardtemplate`
  - `dashboards_dashboardconfig`

- [ ] Comando executou sem erros
- [ ] Schemas de tenants criados

### 5.2. Verificar schemas no banco
```powershell
docker compose -f infra/docker-compose.yml exec db psql -U postgres -d traksense -c "\dn"
```

**Esperado:** Schemas `public`, `test_alpha`

- [ ] Schema public existe
- [ ] Schema test_alpha existe

### 5.3. Verificar tabelas no schema test_alpha
```powershell
docker compose -f infra/docker-compose.yml exec db psql -U postgres -d traksense -c "\dt test_alpha.*"
```

**Esperado:** 6 tabelas (DeviceTemplate, PointTemplate, Device, Point, DashboardTemplate, DashboardConfig)

- [ ] 6 tabelas criadas em test_alpha

---

## ✅ Passo 6: Executar Data Migration (RBAC)

### 6.1. Verificar se migration RBAC existe
```powershell
Get-ChildItem backend\apps\devices\migrations -Filter "*rbac*"
```

**Esperado:** `0002_rbac_groups.py`

- [ ] Migration RBAC existe

### 6.2. Aplicar migration RBAC
```powershell
docker compose -f infra/docker-compose.yml exec api python manage.py migrate_schemas --tenant
```

**Esperado:** Data migration cria 3 grupos no schema do tenant

- [ ] Migration executada
- [ ] Sem erros

### 6.3. Verificar grupos criados
```powershell
docker compose -f infra/docker-compose.yml exec api python manage.py shell
```

```python
from django.contrib.auth.models import Group

grupos = Group.objects.all()
for g in grupos:
    print(f"✅ Grupo: {g.name} | Permissões: {g.permissions.count()}")

exit()
```

**Esperado:** 3 grupos: `internal_ops`, `customer_admin`, `viewer`

- [ ] 3 grupos criados
- [ ] Permissões atribuídas corretamente

---

## ✅ Passo 7: Executar Seeds

### 7.1. Seed de DeviceTemplates
```powershell
docker compose -f infra/docker-compose.yml exec api python manage.py seed_device_templates
```

**Esperado:** 
- Mensagem: "✅ DeviceTemplate 'inverter_v1_parsec' criado"
- Mensagem: "✅ DeviceTemplate 'chiller_v1' criado"

- [ ] Comando executou sem erros
- [ ] 2 templates criados

### 7.2. Verificar templates no banco
```powershell
docker compose -f infra/docker-compose.yml exec api python manage.py shell
```

```python
from apps.devices.models import DeviceTemplate, PointTemplate

templates = DeviceTemplate.objects.all()
print(f"Total de templates: {templates.count()}")

for t in templates:
    pontos = t.point_templates.count()
    print(f"✅ {t.code} (v{t.version}) - {pontos} pontos")

exit()
```

**Esperado:** 2 templates com 3 pontos cada

- [ ] 2 DeviceTemplates criados
- [ ] inverter_v1_parsec com 3 PointTemplates
- [ ] chiller_v1 com 3 PointTemplates

### 7.3. Seed de DashboardTemplates
```powershell
docker compose -f infra/docker-compose.yml exec api python manage.py seed_dashboard_templates
```

**Esperado:** 2 dashboards criados

- [ ] Comando executou sem erros
- [ ] 2 DashboardTemplates criados

---

## ✅ Passo 8: Testar Provisionamento Automático

### 8.1. Criar Device via shell
```powershell
docker compose -f infra/docker-compose.yml exec api python manage.py shell
```

```python
from apps.devices.models import Device, DeviceTemplate, Point
from apps.devices.services import provision_device_from_template
from apps.dashboards.models import DashboardConfig

# Buscar template
template = DeviceTemplate.objects.get(code='inverter_v1_parsec', version=1)

# Criar device
device = Device.objects.create(
    template=template,
    name='Inversor 01 - Teste Validação'
)

print(f"✅ Device criado: {device.pk}")

# Provisionar
provision_device_from_template(device)

# Verificar Points
points = Point.objects.filter(device=device)
print(f"✅ Points criados: {points.count()}")
for p in points:
    print(f"  - {p.point_template.name} (contracted={p.is_contracted})")

# Verificar DashboardConfig
try:
    config = DashboardConfig.objects.get(device=device)
    print(f"✅ DashboardConfig criado")
    print(f"  Painéis: {len(config.json.get('panels', []))}")
except DashboardConfig.DoesNotExist:
    print("❌ DashboardConfig NÃO criado")

exit()
```

**Esperado:**
- 3 Points criados
- DashboardConfig criado com 4 painéis

- [ ] Device criado sem erros
- [ ] 3 Points criados automaticamente
- [ ] DashboardConfig criado automaticamente
- [ ] JSON do dashboard contém 4 painéis

---

## ✅ Passo 9: Testar Validações

### 9.1. Testar validação de unit (BOOL não pode ter unit)
```powershell
docker compose -f infra/docker-compose.yml exec api python manage.py shell
```

```python
from apps.devices.models import PointTemplate, PointType, DeviceTemplate
from django.core.exceptions import ValidationError

template = DeviceTemplate.objects.first()

# Tentar criar BOOL com unit (INVÁLIDO)
pt = PointTemplate(
    device_template=template,
    name='test_invalid',
    label='Test Invalid',
    ptype=PointType.BOOL,
    unit='°C'  # ❌ INVÁLIDO
)

try:
    pt.full_clean()
    print("❌ Validação NÃO funcionou (deveria ter falhado)")
except ValidationError as e:
    print("✅ Validação funcionou:", e.message_dict.get('unit'))

exit()
```

**Esperado:** ValidationError com mensagem sobre `unit`

- [ ] Validação bloqueou unit em tipo BOOL

### 9.2. Testar validação de enum_values (ENUM requer valores)
```python
# ... mesmo shell anterior
pt2 = PointTemplate(
    device_template=template,
    name='test_enum',
    label='Test Enum',
    ptype=PointType.ENUM
    # ❌ Sem enum_values
)

try:
    pt2.full_clean()
    print("❌ Validação NÃO funcionou")
except ValidationError as e:
    print("✅ Validação funcionou:", e.message_dict.get('enum_values'))

exit()
```

- [ ] Validação bloqueou ENUM sem enum_values

---

## ✅ Passo 10: Testar Django Admin

### 10.1. Criar superusuário
```powershell
docker compose -f infra/docker-compose.yml exec api python manage.py createsuperuser
```

**Dados sugeridos:**
- Username: `admin`
- Email: `admin@traksense.local`
- Password: `admin123`

- [ ] Superusuário criado

### 10.2. Adicionar ao grupo internal_ops
```powershell
docker compose -f infra/docker-compose.yml exec api python manage.py shell
```

```python
from django.contrib.auth.models import User, Group

user = User.objects.get(username='admin')
group = Group.objects.get(name='internal_ops')
user.groups.add(group)
print(f"✅ Usuário '{user.username}' adicionado ao grupo '{group.name}'")

exit()
```

- [ ] Usuário adicionado ao grupo internal_ops

### 10.3. Iniciar servidor e acessar admin
```powershell
# Se o container 'api' não estiver rodando o servidor, execute:
docker compose -f infra/docker-compose.yml exec api python manage.py runserver 0.0.0.0:8000
```

Abrir no navegador: http://localhost:8000/admin/

- [ ] Admin carrega sem erros
- [ ] Login funciona
- [ ] Seções visíveis: Devices, Dashboards

### 10.4. Criar Device pelo admin
1. Navegar para: **Devices → Device → Add Device**
2. Preencher:
   - Template: inverter_v1_parsec
   - Name: Inversor Admin Test
   - Status: PENDING
3. Salvar

**Esperado:** 
- Mensagem de sucesso: "✅ Device criado e provisionado automaticamente"
- Inline de Points exibe 3 pontos (read-only)

- [ ] Device criado pelo admin
- [ ] Mensagem de sucesso exibida
- [ ] Points aparecem no inline
- [ ] DashboardConfig criado (verificar em Dashboards)

---

## ✅ Passo 11: Executar Testes Automatizados

### 11.1. Instalar pytest no container
```powershell
# Já deve estar em requirements.txt, mas verificar:
docker compose -f infra/docker-compose.yml exec api pip list | findstr pytest
```

- [ ] pytest instalado

### 11.2. Executar testes de imutabilidade
```powershell
docker compose -f infra/docker-compose.yml exec api pytest backend/tests/test_templates_immutability.py -v
```

**Esperado:** Todos os 3 testes passando

- [ ] test_create_device_template_versions ✅
- [ ] test_block_destructive_changes ✅
- [ ] test_create_new_version_with_superseded_by ✅

### 11.3. Executar testes de provisionamento
```powershell
docker compose -f infra/docker-compose.yml exec api pytest backend/tests/test_device_provisioning.py -v
```

**Esperado:** Todos os 4 testes passando

- [ ] test_provision_device_creates_points ✅
- [ ] test_provision_device_creates_dashboard_config ✅
- [ ] test_provision_with_contracted_points_filter ✅
- [ ] test_dashboard_config_validation ✅

---

## ✅ Critério de Aceite Final

**A Fase 2 está REALMENTE completa quando:**

1. [x] ✅ Containers rodando sem erros (api, db, emqx, redis UP)
2. [x] ✅ Banco de dados acessível com TimescaleDB (v2.22.1)
3. [x] ✅ Settings Django configurados corretamente (SHARED_APPS, TENANT_APPS, MIDDLEWARE verificados)
4. [x] ✅ Migrações SHARED aplicadas (17 migrations executadas no schema public)
5. [ ] ⚠️ Tenant público criado ✓ / alpha BLOQUEADO (erro de dependência circular)
6. [ ] ❌ Migrações TENANT aplicadas (aguardando criação de tenant alpha)
7. [ ] ❌ RBAC groups criados (3 grupos) - migration 0002_rbac_groups.py foi removida
8. [ ] ❌ Seeds executados (2 templates + 2 dashboards) - aguarda setup completo
9. [ ] ❌ Provisionamento automático funciona (shell) - aguarda templates
10. [ ] ❌ Validações bloqueiam dados inválidos - aguarda setup completo
11. [ ] ❌ Django Admin funciona com RBAC - aguarda superusuário + grupos
12. [ ] ❌ Device criado no admin provisiona Points/Dashboard - aguarda admin setup
13. [ ] ❌ Testes automatizados passam (7 testes no total) - aguarda dados de teste

**PROGRESSO:** 4/13 critérios completos (31%)

---

## 📊 Status da Validação

**Data de Início:** 07/10/2025 às 14:46 BRT  
**Validador:** GitHub Copilot + Execução Real  
**Status Atual:** [x] Em Progresso  [x] Bloqueado  [ ] Completo

**Observações:**
- ✅ **Passos 1-3 COMPLETOS:** Infraestrutura, configuração Django, migrations SHARED aplicadas
- ✅ **Passo 4.1 COMPLETO:** Tenant público criado com sucesso (UUID: 1)
- ❌ **Passo 4.2 BLOQUEADO:** Tentativa de criar tenant 'alpha' falhou com erro de dependência circular
- ⚠️ **Problema identificado:** DashboardTemplate (dashboards app) tem FK para DeviceTemplate (devices app), mas ao criar tenant com `auto_create_schema=True`, o django-tenants tenta aplicar migrations em ordem alfabética (dashboards antes de devices), causando erro `relation "devices_devicetemplate" does not exist`
- 📋 **Ações necessárias:** Resolver dependência circular antes de prosseguir com Passos 5-11
- 🔧 **Progresso:** ~40% da validação completa (4 de 11 passos principais) 

---

## 🚫 O que NÃO fazer

❌ Marcar itens sem executar comandos  
❌ Assumir que código existe = funciona  
❌ Pular etapas de inicialização  
❌ Ignorar erros "pequenos"  
❌ Validar sem ter dados de teste  

✅ **Validação = Executar + Verificar Resultado + Documentar**

---

## 🚨 PROBLEMA IDENTIFICADO - Dependência Circular

### ❌ Erro Atual:

Ao tentar criar tenant 'test_alpha', o django-tenants executa `migrate_schemas` automaticamente (devido a `auto_create_schema=True`). O erro ocorre:

```
django.db.utils.ProgrammingError: relation "devices_devicetemplate" does not exist
```

**Causa:** 
- `DashboardTemplate` (app dashboards) tem FK para `DeviceTemplate` (app devices)
- Django aplica migrations em ordem alfabética: `dashboards` vem antes de `devices`
- Ao criar a tabela `dashboards_dashboardtemplate`, a FK referencia `devices_devicetemplate` que ainda não existe

### 🔧 Soluções Propostas:

#### **Opção 1: Remover FK temporariamente (RECOMENDADO - Mais Simples)**

1. **Modificar modelo DashboardTemplate:**
   - Remover campo `device_template = ForeignKey(DeviceTemplate)`
   - Adicionar campo `device_template_code = CharField(max_length=100)`
   - Adicionar campo `device_template_version = IntegerField()`

2. **Vantagens:**
   - Resolve dependência circular imediatamente
   - Não quebra funcionalidade (pode fazer lookup manual)
   - Migrations rodam em qualquer ordem

3. **Desvantagens:**
   - Perde constraint de FK no banco
   - Precisa validar manualmente que template existe

#### **Opção 2: Desativar auto_create_schema (RECOMENDADO - Mais Controle)**

1. **Modificar modelo Client:**
   ```python
   auto_create_schema = False  # Desativar criação automática
   ```

2. **Criar tenants manualmente:**
   ```python
   # Criar tenant sem rodar migrations
   alpha = Client.objects.create(schema_name='test_alpha', name='Test Alpha')
   ```

3. **Aplicar migrations na ordem correta:**
   ```bash
   # Rodar apenas devices primeiro
   python manage.py migrate_schemas --tenant --schema=test_alpha devices
   
   # Depois rodar dashboards
   python manage.py migrate_schemas --tenant --schema=test_alpha dashboards
   ```

4. **Vantagens:**
   - Mantém FK intacta
   - Controle total sobre ordem de migrations
   - Abordagem recomendada para produção

5. **Desvantagens:**
   - Mais passos manuais
   - Precisa documentar ordem correta

#### **Opção 3: Reorganizar migrations (Mais Trabalhoso)**

1. Deletar migrations atuais
2. Criar `devices.0001_initial` SEM DeviceTemplate
3. Criar `dashboards.0001_initial` SEM FK para DeviceTemplate
4. Criar `devices.0002_add_devicetemplate`
5. Criar `dashboards.0002_add_fk_device_template`

**Não recomendado:** Muito trabalho e propenso a erros.

---

### ✅ DECISÃO RECOMENDADA:

**Usar Opção 2 (Desativar auto_create_schema)** porque:
- ✅ Mantém integridade referencial (FK)
- ✅ É a abordagem recomendada para produção
- ✅ Dá controle total sobre processo de migration
- ✅ Evita surpresas em criação automática de schemas

**Próximos Passos:**
1. Modificar `Client.auto_create_schema = False` em `tenancy/models.py`
2. Recriar migrations (se necessário)
3. Criar tenant alpha manualmente
4. Aplicar migrations devices primeiro
5. Aplicar migrations dashboards depois
6. Continuar com Passo 5 do plano de validação
