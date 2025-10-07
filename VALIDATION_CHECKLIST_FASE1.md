# Checklist de Validação — Fase 1 (TENANCY + TIMESCALE + RLS)

Use este checklist para validar que todos os componentes da Fase 1 estão funcionando corretamente.

## ✅ Pré-requisitos

- [X] Infraestrutura da Fase 0 validada e funcionando
- [X] Docker containers rodando (emqx, db, redis, api, ingest)
- [X] PostgreSQL + TimescaleDB acessível
- [X] Python 3.12+ no ambiente de desenvolvimento

## ✅ Setup Inicial

- [X] `django-tenants>=3.6.1` instalado em `backend/requirements.txt`
- [X] `pytest>=8.0` e `pytest-django>=4.7` instalados
- [X] Estrutura de apps criada:
  - [X] `backend/apps/tenancy/` com models Client e Domain
  - [X] `backend/apps/timeseries/` com migrations e views
  - [X] `backend/apps/devices/` (placeholder)
  - [X] `backend/apps/dashboards/` (placeholder)
  - [X] `backend/apps/rules/` (placeholder)
  - [X] `backend/apps/commands/` (placeholder)
- [X] `backend/tests/` com test_rls_isolation.py e test_perf_agg.py

## ✅ Configuração Django

### 1. Verificar settings.py

```powershell
# PowerShell - Verificar configuração
docker compose -f infra/docker-compose.yml exec api python manage.py shell
```

Dentro do shell:
```python
from django.conf import settings

# Verificar SHARED_APPS
print("SHARED_APPS:", settings.SHARED_APPS)
# Esperado: ['django_tenants', 'tenancy', 'timeseries', ...]

# Verificar TENANT_APPS
print("TENANT_APPS:", settings.TENANT_APPS)
# Esperado: ['devices', 'dashboards', 'rules', 'commands']

# Verificar middleware
print("MIDDLEWARE:", [m for m in settings.MIDDLEWARE if 'Tenant' in m])
# Esperado: TenantMainMiddleware primeiro, TenantGucMiddleware último

# Verificar router
print("DATABASE_ROUTERS:", settings.DATABASE_ROUTERS)
# Esperado: ('django_tenants.routers.TenantSyncRouter',)

exit()
```

- [ ] `SHARED_APPS` contém `django_tenants`, `tenancy`, `timeseries`
- [ ] `TENANT_APPS` contém apps de tenants (`devices`, `dashboards`, etc.)
- [ ] `TenantMainMiddleware` é o primeiro middleware
- [ ] `TenantGucMiddleware` é o último middleware
- [ ] `TenantSyncRouter` está configurado
- [ ] `TENANT_MODEL = 'tenancy.Client'`
- [ ] `TENANT_DOMAIN_MODEL = 'tenancy.Domain'`

## ✅ Migrações e Banco de Dados

### 1. Executar migrações do django-tenants

```powershell
# PowerShell
docker compose -f infra/docker-compose.yml exec api python manage.py migrate_schemas --shared
```

**Esperado**: Migrações do schema `public` executadas

- [ ] Comando executou sem erros
- [ ] Tabelas `tenancy_client` e `tenancy_domain` criadas no schema `public`

### 2. Verificar hypertable TimescaleDB

```powershell
docker compose -f infra/docker-compose.yml exec db psql -U postgres -d traksense -c "\d public.ts_measure"
```

**Esperado**: Estrutura da tabela exibida com colunas:
- `tenant_id uuid`
- `device_id uuid`
- `point_id uuid`
- `ts timestamptz`
- `v_num double precision`
- `v_bool boolean`
- `v_text text`
- `unit text`
- `qual smallint`
- `meta jsonb`

- [ ] Tabela `public.ts_measure` existe
- [ ] Colunas estão corretas
- [ ] Tabela é uma hypertable (verificar com `\d+`)

### 3. Verificar índices

```powershell
docker compose -f infra/docker-compose.yml exec db psql -U postgres -d traksense -c "\di public.ts_measure*"
```

**Esperado**: Pelo menos 3 índices:
- `ts_measure_tenant_id_device_id_point_id_ts_idx`
- `ts_measure_tenant_id_ts_idx`
- `ts_measure_device_id_ts_idx`

- [ ] Índices criados corretamente
- [ ] Índices incluem `tenant_id` para RLS

### 4. Verificar Row Level Security (RLS)

```powershell
docker compose -f infra/docker-compose.yml exec db psql -U postgres -d traksense
```

Dentro do psql:
```sql
-- Verificar se RLS está habilitado
SELECT relname, relrowsecurity 
FROM pg_class 
WHERE relname = 'ts_measure';
-- Esperado: ts_measure | t (true)

-- Verificar policy
SELECT schemaname, tablename, policyname, cmd, qual 
FROM pg_policies 
WHERE tablename = 'ts_measure';
-- Esperado: ts_tenant_isolation | ALL | (tenant_id = ...)

\q
```

- [ ] RLS está habilitado na tabela `ts_measure` (relrowsecurity = true)
- [ ] Policy `ts_tenant_isolation` existe
- [ ] Policy usa `current_setting('app.tenant_id')::uuid`

### 5. Verificar Continuous Aggregates

```powershell
docker compose -f infra/docker-compose.yml exec db psql -U postgres -d traksense -c "SELECT matviewname FROM pg_matviews WHERE schemaname = 'public' AND matviewname LIKE 'ts_measure_%'"
```

**Esperado**: 3 materialized views:
- `ts_measure_1m`
- `ts_measure_5m`
- `ts_measure_1h`

- [ ] `ts_measure_1m` existe
- [ ] `ts_measure_5m` existe
- [ ] `ts_measure_1h` existe

### 6. Verificar Refresh Policies

```powershell
docker compose -f infra/docker-compose.yml exec db psql -U postgres -d traksense -c "SELECT count(*) FROM timescaledb_information.jobs WHERE proc_name = 'policy_refresh_continuous_aggregate'"
```

**Esperado**: Contagem >= 3 (uma policy por aggregate)

- [ ] Pelo menos 3 refresh policies configuradas

## ✅ Testes de Multi-Tenancy

### 1. Criar tenants de teste

```powershell
docker compose -f infra/docker-compose.yml exec api python manage.py shell
```

Dentro do shell:
```python
from tenancy.models import Client, Domain

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

# Criar tenant beta
beta = Client.objects.create(
    schema_name='test_beta',
    name='Test Beta Inc'
)
Domain.objects.create(
    domain='beta.localhost',
    tenant=beta,
    is_primary=True
)

print(f"Alpha ID: {alpha.pk}")
print(f"Beta ID: {beta.pk}")

exit()
```

- [ ] Tenant `test_alpha` criado
- [ ] Tenant `test_beta` criado
- [ ] Domínios criados sem erros
- [ ] Schemas `test_alpha` e `test_beta` criados no PostgreSQL

### 2. Executar migrações nos schemas de tenants

```powershell
docker compose -f infra/docker-compose.yml exec api python manage.py migrate_schemas --tenant
```

- [ ] Migrações executadas em todos os schemas de tenants
- [ ] Sem erros reportados

### 3. Verificar schemas no banco

```powershell
docker compose -f infra/docker-compose.yml exec db psql -U postgres -d traksense -c "\dn"
```

**Esperado**: Schemas `public`, `test_alpha`, `test_beta`

- [ ] Schema `public` existe
- [ ] Schema `test_alpha` existe
- [ ] Schema `test_beta` existe

## ✅ Testes de RLS (Row Level Security)

### 1. Popular dados de teste

```powershell
docker compose -f infra/docker-compose.yml exec api python manage.py seed_ts --rows 10000
```

**Esperado**: 
- 2 tenants criados (alpha, beta)
- ~10k rows por tenant inseridos em `public.ts_measure`

- [ ] Comando executou sem erros
- [ ] Mensagem confirma inserção de dados
- [ ] Total de ~20k rows na tabela

### 2. Executar testes automatizados de RLS

```powershell
docker compose -f infra/docker-compose.yml exec api pytest backend/tests/test_rls_isolation.py -v
```

**Esperado**: 3 testes passando:
- `test_rls_blocks_cross_tenant_access` ✓
- `test_rls_policy_exists` ✓
- `test_rls_enabled_on_table` ✓

- [ ] Todos os 3 testes passaram
- [ ] `test_rls_blocks_cross_tenant_access` confirma isolamento
- [ ] Sem erros de conexão ou GUC

### 3. Teste manual de isolamento

```powershell
docker compose -f infra/docker-compose.yml exec db psql -U postgres -d traksense
```

Dentro do psql:
```sql
-- Contar total (sem GUC = sem dados visíveis)
SELECT count(*) FROM public.ts_measure;
-- Esperado: 0 (RLS bloqueia acesso sem GUC)

-- Configurar GUC para tenant alpha (usar UUID real)
SET app.tenant_id = '<UUID_DO_ALPHA>';
SELECT count(*) FROM public.ts_measure;
-- Esperado: ~10000

-- Trocar para tenant beta (usar UUID real)
SET app.tenant_id = '<UUID_DO_BETA>';
SELECT count(*) FROM public.ts_measure;
-- Esperado: ~10000 (diferentes registros)

\q
```

- [ ] Sem GUC: 0 registros visíveis (RLS bloqueia)
- [ ] Com GUC do alpha: apenas dados do alpha
- [ ] Com GUC do beta: apenas dados do beta
- [ ] Trocar GUC isola corretamente os dados

## ✅ Testes de Performance

### 1. Executar testes de performance

```powershell
docker compose -f infra/docker-compose.yml exec api pytest backend/tests/test_perf_agg.py -v -s
```

**Esperado**: 5 testes passando:
- `test_aggregated_query_performance_1m` ✓ (< 1s no ambiente de teste)
- `test_raw_data_query_with_limit` ✓ (< 2s)
- `test_continuous_aggregates_exist` ✓
- `test_refresh_policies_exist` ✓

- [ ] Todos os testes de performance passaram
- [ ] Query agregada executou em < 1s
- [ ] Query raw com limite executou em < 2s
- [ ] Logs mostram tempo de execução

### 2. Teste manual de query agregada

```powershell
docker compose -f infra/docker-compose.yml exec db psql -U postgres -d traksense
```

Dentro do psql:
```sql
-- Configurar GUC
SET app.tenant_id = '<UUID_DO_ALPHA>';

-- Query agregada de 1 minuto (últimas 24h)
\timing on
SELECT tb AS ts, v_avg, v_min, v_max, v_count
FROM public.ts_measure_1m
WHERE tb >= NOW() - INTERVAL '24 hours'
ORDER BY tb DESC
LIMIT 100;
-- Esperado: < 300ms em produção, < 1s em dev

\q
```

- [ ] Query executou com sucesso
- [ ] Tempo de execução aceitável
- [ ] Resultados agregados retornados (avg, min, max, count)

## ✅ API Endpoints

### 1. Testar endpoint /data/points

```powershell
# Obter IDs de teste (execute seed_ts antes)
docker compose -f infra/docker-compose.yml exec api python manage.py shell
```

```python
from django.db import connection
cursor = connection.cursor()
cursor.execute("SELECT device_id, point_id FROM public.ts_measure LIMIT 1")
device_id, point_id = cursor.fetchone()
print(f"Device: {device_id}, Point: {point_id}")
exit()
```

Testar endpoint (use IDs reais):
```powershell
# Query agregada de 1 minuto
curl "http://localhost:8000/api/timeseries/data/points?device_id=<DEVICE_ID>&point_id=<POINT_ID>&from=2025-10-06T00:00:00Z&to=2025-10-07T00:00:00Z&agg=1m"
```

**Esperado**: Resposta JSON:
```json
{
  "device_id": "...",
  "point_id": "...",
  "agg": "1m",
  "rows": [
    {"ts": "2025-10-06T00:00:00Z", "v_avg": 20.5, "v_min": 18.0, "v_max": 23.0, "v_count": 60}
  ]
}
```

- [ ] Endpoint retorna 200 OK
- [ ] Resposta JSON no formato correto
- [ ] Dados agregados incluem avg, min, max, count
- [ ] Query executou em tempo aceitável (header X-Response-Time se disponível)

### 2. Testar endpoint /health/timeseries

```powershell
curl http://localhost:8000/api/timeseries/health/timeseries
```

**Esperado**: `{"status":"ok","rls_enabled":true}`

- [ ] Endpoint retorna 200 OK
- [ ] `status` = `"ok"`
- [ ] `rls_enabled` = `true`

## ✅ Middleware e GUC

### 1. Verificar TenantGucMiddleware

```powershell
docker compose -f infra/docker-compose.yml exec api python manage.py shell
```

```python
from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser
from core.middleware import TenantGucMiddleware
from tenancy.models import Client, Domain
from django.db import connection

# Simular requisição
factory = RequestFactory()
request = factory.get('/', HTTP_HOST='alpha.localhost')
request.user = AnonymousUser()

# Obter tenant
tenant = Client.objects.get(schema_name='test_alpha')
request.tenant = tenant

# Processar middleware
middleware = TenantGucMiddleware(lambda r: None)
middleware.process_request(request)

# Verificar GUC
cursor = connection.cursor()
cursor.execute("SELECT current_setting('app.tenant_id', true)")
guc_value = cursor.fetchone()[0]
print(f"GUC configurado: {guc_value}")
print(f"Tenant ID: {str(tenant.pk)}")
assert guc_value == str(tenant.pk), "GUC não corresponde ao tenant!"

exit()
```

- [ ] Middleware configurou GUC corretamente
- [ ] `app.tenant_id` corresponde ao tenant da requisição
- [ ] Sem erros no processo

## ✅ Testes Integrados

### 1. Executar todos os testes

```powershell
docker compose -f infra/docker-compose.yml exec api pytest backend/tests/ -v
```

**Esperado**: Todos os testes passando (8 testes no total)

- [ ] test_rls_isolation.py: 3/3 passando ✓
- [ ] test_perf_agg.py: 5/5 passando ✓
- [ ] Tempo total < 1 minuto
- [ ] Sem erros ou warnings críticos

### 2. Verificar cobertura (opcional)

```powershell
docker compose -f infra/docker-compose.yml exec api pytest backend/tests/ --cov=apps --cov-report=term
```

- [ ] Cobertura > 70% nos apps críticos (tenancy, timeseries)
- [ ] Relatório gerado sem erros

## ✅ Limpeza e Rebuild

### 1. Limpar dados de teste

```powershell
docker compose -f infra/docker-compose.yml exec db psql -U postgres -d traksense -c "TRUNCATE public.ts_measure CASCADE"
```

- [ ] Tabela truncada sem erros
- [ ] Aggregates também limpos (CASCADE)

### 2. Rebuild completo

```powershell
docker compose -f infra/docker-compose.yml down -v
docker compose -f infra/docker-compose.yml up -d --build
```

- [ ] Containers removidos
- [ ] Volumes removidos
- [ ] Rebuild executado sem erros
- [ ] Todos os serviços sobem novamente

### 3. Re-executar migrações

```powershell
docker compose -f infra/docker-compose.yml exec api python manage.py migrate_schemas
```

- [ ] Migrações executadas sem erros
- [ ] Hypertable e aggregates recriados
- [ ] RLS habilitado novamente

## ✅ Documentação

- [ ] `README.md` atualizado com instruções da Fase 1
- [ ] Seção sobre django-tenants adicionada
- [ ] Comandos `migrate_schemas` documentados
- [ ] Comando `seed_ts` documentado
- [ ] Exemplos de queries com RLS
- [ ] Instruções de teste documentadas

## ✅ Checklist Final

- [ ] ✅ django-tenants configurado e funcionando
- [ ] ✅ Multi-tenancy com schemas separados operacional
- [ ] ✅ Hypertable TimescaleDB criada
- [ ] ✅ Índices de performance criados
- [ ] ✅ Row Level Security (RLS) habilitado e testado
- [ ] ✅ Continuous aggregates (1m, 5m, 1h) criados
- [ ] ✅ Refresh policies configuradas
- [ ] ✅ TenantGucMiddleware configurando GUC corretamente
- [ ] ✅ Endpoint /data/points funcionando com agregações
- [ ] ✅ Testes automatizados de RLS passando (3/3)
- [ ] ✅ Testes de performance passando (5/5)
- [ ] ✅ Isolamento cross-tenant validado
- [ ] ✅ Seeds de dados funcionando
- [ ] ✅ Documentação atualizada

## 🎯 Critérios de Aceite (Fase 1)

✅ **TODOS** os itens abaixo devem estar marcados:

1. [ ] django-tenants 3.6+ instalado e configurado
2. [ ] SHARED_APPS e TENANT_APPS corretamente separados
3. [ ] TenantMainMiddleware primeiro, TenantGucMiddleware último
4. [ ] Hypertable `public.ts_measure` criada com chunking de 1 dia
5. [ ] RLS habilitado com policy `ts_tenant_isolation` usando `app.tenant_id`
6. [ ] 3 índices de performance criados (tenant+device+point+ts, tenant+ts, device+ts)
7. [ ] 3 continuous aggregates criados (ts_measure_1m, ts_measure_5m, ts_measure_1h)
8. [ ] 3 refresh policies configuradas (5min, 15min, 1h)
9. [ ] Endpoint `/api/timeseries/data/points` retorna dados agregados corretamente
10. [ ] Query agregada de 24h executa em < 300ms (produção) ou < 1s (dev)
11. [ ] Teste `test_rls_blocks_cross_tenant_access` passa (isolamento confirmado)
12. [ ] Comando `seed_ts` gera 2 tenants com ~1M rows cada
13. [ ] Todos os 8 testes pytest passam sem erros
14. [ ] GUC `app.tenant_id` é configurado automaticamente pelo middleware
15. [ ] Sem acesso cross-tenant possível (RLS bloqueia sem GUC correto)

---

## 🚀 Próximos Passos (Fase 2)

Após validação completa:

- [ ] Implementar models completos (Device, Point, DeviceTemplate, PointTemplate)
- [ ] Criar API de provisionamento EMQX (Auth/ACL por device)
- [ ] Implementar ingest assíncrono com adapters Pydantic (Parsec, etc.)
- [ ] Sistema de comandos com ACK via MQTT
- [ ] DashboardTemplate e DashboardConfig (JSON)
- [ ] Rules engine com Celery para alertas
- [ ] RBAC (internal_ops, customer_admin, viewer)
- [ ] APIs completas para frontend Spark

---

## 📊 Resumo da Validação

**Data da Validação**: ___ de outubro de 2025  
**Status**: ⏳ **PENDENTE DE VALIDAÇÃO**

### Componentes a Validar

| Componente | Status | Detalhes |
|------------|--------|----------|
| django-tenants | ⏳ | Aguardando configuração |
| Multi-tenancy schemas | ⏳ | Aguardando criação de tenants |
| TimescaleDB hypertable | ⏳ | Aguardando migration |
| Row Level Security | ⏳ | Aguardando testes |
| Continuous Aggregates | ⏳ | Aguardando criação |
| TenantGucMiddleware | ⏳ | Aguardando testes |
| Endpoint /data/points | ⏳ | Aguardando testes |
| Testes RLS | ⏳ | Aguardando execução pytest |
| Testes Performance | ⏳ | Aguardando execução pytest |
| Seed Data | ⏳ | Aguardando comando seed_ts |

### Passos para Completar Validação

1. Instalar dependências: `docker compose exec api pip install -r requirements.txt`
2. Executar migrations: `docker compose exec api python manage.py migrate_schemas`
3. Criar tenants: (usar shell Django ou seed_ts)
4. Popular dados: `docker compose exec api python manage.py seed_ts --rows 1000000`
5. Executar testes: `docker compose exec api pytest backend/tests/ -v`
6. Validar endpoints: testar `/data/points` e `/health/timeseries`
7. Marcar checklist conforme testes passem

---

## 📋 Log de Execução (2025-10-07)

### Progresso Realizado ✅

1. **Estrutura de Apps** (100%):
   - ✅ Criados apps placeholders: devices, dashboards, rules, commands
   - ✅ Corrigidos AppConfig.name para paths corretos (`apps.*`)
   - ✅ Configurados SHARED_APPS e TENANT_APPS no settings.py

2. **django-tenants** (100%):
   - ✅ Instalado django-tenants>=3.6.1
   - ✅ Configurado DATABASE['default']['ENGINE'] = 'django_tenants.postgresql_backend'
   - ✅ Configurado TENANT_MODEL = 'tenancy.Client'
   - ✅ Configurado TENANT_DOMAIN_MODEL = 'tenancy.Domain'
   - ✅ TenantMainMiddleware adicionado como primeiro middleware

3. **Migrations** (90%):
   - ✅ Geradas migrations para app tenancy (Client, Domain)
   - ✅ Aplicadas migrations com `migrate_schemas --shared`
   - ✅ Tabelas tenancy_client e tenancy_domain criadas no schema public
   - ⚠️ Migration timeseries marcada como --fake (limitação atomic=False)

4. **TimescaleDB** (95%):
   - ✅ Hypertable `public.ts_measure` criada manualmente
   - ✅ Índices criados (tenant_devpt_ts, tenant_ts, device_ts)
   - ✅ RLS habilitado com policy `ts_tenant_isolation`
   - ⏳ Continuous Aggregates (1m/5m/1h) PENDENTES (requerem atomic=False)

5. **Container API** (100%):
   - ✅ Docker image construída sem erros
   - ✅ Container iniciando e Django carregando apps corretamente
   - ✅ System check sem issues (0 silenced)

### Problemas Encontrados e Soluções 🔧

| # | Problema | Solução | Status |
|---|----------|---------|--------|
| 1 | django-tenants não instalado | Rebuild container após adicionar em requirements.txt | ✅ RESOLVIDO |
| 2 | Apps placeholders faltando | Criados devices, dashboards, rules, commands | ✅ RESOLVIDO |
| 3 | Paths incorretos em settings.py | Corrigido para 'apps.xxx' e 'tenancy' | ✅ RESOLVIDO |
| 4 | IndentationError em timeseries/models.py | Reformatada docstring (removido código Python) | ✅ RESOLVIDO |
| 5 | TENANT_MODEL referência incorreta | Corrigido de 'apps.tenancy.Client' para 'tenancy.Client' | ✅ RESOLVIDO |
| 6 | urls.py importando 'timeseries.urls' | Corrigido para 'apps.timeseries.urls' | ✅ RESOLVIDO |
| 7 | DATABASE ENGINE padrão PostgreSQL | Adicionado DATABASES['default']['ENGINE'] = 'django_tenants.postgresql_backend' | ✅ RESOLVIDO |
| 8 | CREATE MATERIALIZED VIEW em transação | Marcado migration como --fake, criado hypertable manualmente | ✅ WORKAROUND |
| 9 | Tenancy migrations não existiam | Executado makemigrations tenancy e migrate_schemas --shared | ✅ RESOLVIDO |
| 10 | Sem tenant para localhost | ⏳ PENDENTE - criar tenant 'localhost' via shell | ⏳ EM PROGRESSO |

### Pendências para Concluir Validação ⏳

1. **Tenant localhost** (BLOQUEANTE):
   - Criar tenant com schema_name='public' e domínio='localhost'
   - Permite acessar API via http://localhost:8000

2. **Continuous Aggregates**:
   - Executar SQL manualmente para criar ts_measure_1m/5m/1h
   - Configurar refresh policies

3. **Tenants de Teste**:
   - Criar tenants alpha e beta
   - Executar migrate_schemas --tenant

4. **Seed Data**:
   - Popular ts_measure com ~100k rows de teste
   - Validar RLS isolamento

5. **Testes Automatizados**:
   - Executar pytest backend/tests/test_rls_isolation.py
   - Executar pytest backend/tests/test_perf_agg.py

6. **Validação Endpoints**:
   - GET /health → {"status":"ok"}
   - GET /health/timeseries → validação RLS + hypertable
   - GET /data/points → query com agregação

---

**Status**: Fase 1 - Multi-Tenancy + TimescaleDB + RLS 🔄 **70% COMPLETO**  
**Validador**: GitHub Copilot + User (Rafael)  
**Próxima Fase**: Completar validação endpoints → Fase 2 - Device Models + Ingest
