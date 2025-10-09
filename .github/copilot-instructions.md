# Copilot Instructions — TrakSense IoT Platform

## Contexto do Projeto

Plataforma de monitoramento IoT multi-tenant com EMQX, Django/DRF, TimescaleDB e serviço de ingest assíncrono. **Este repositório contém APENAS backend** (API + Ingest). Frontend Spark está em repositório separado.

## Stack & Ferramentas

- **Backend API**: Django 4+ / DRF + django-tenants (multi-tenancy por schema)
- **Database**: PostgreSQL 15 + TimescaleDB (hypertable única com RLS)
- **Broker MQTT**: EMQX 5 (Auth/ACL por device, LWT, TLS em prod)
- **Ingest Service**: Python asyncio (asyncio-mqtt + asyncpg + Pydantic)
- **Cache/Queue**: Redis (Celery para regras/alertas)
- **Infraestrutura**: Docker Compose (desenvolvimento) / Kubernetes (prod)
- **Gerenciamento**: Makefile (Linux/Mac) + manage.ps1 (PowerShell/Windows)

## Arquitetura Multi-Tenant

### Princípios Fundamentais

1. **Metadados por schema de tenant** (`{tenant_schema}.devices_*`)
2. **Telemetria centralizada** em `public.ts_measure` com RLS por `tenant_id`
3. **Nunca duplicar telemetria** em tabelas por tenant (anti-pattern!)
4. **Isolamento via RLS**: `SET app.tenant_id = '<uuid>'` em toda conexão

### Schema Structure

```
public (shared):
  ├── ts_measure (hypertable com RLS por tenant_id)
  ├── ts_measure_{1m,5m,1h} (continuous aggregates)
  ├── tenancy_client (tenants)
  ├── templates_* (DeviceTemplate, PointTemplate, DashboardTemplate)
  └── ingest_errors (DLQ - Dead Letter Queue)

{tenant_schema} (ex: demo):
  ├── devices_device, devices_point
  ├── dashboards_config
  ├── rules_rule
  └── commands_command
```

**CRÍTICO**: Sempre setar `app.tenant_id` antes de queries RLS. Backend usa middleware; ingest seta explicitamente.

## Estrutura de Diretórios

```
traksense-backend/
├── backend/                    # Django API
│   ├── core/                   # Settings, URLs, ASGI/WSGI
│   ├── apps/
│   │   ├── tenancy/            # SHARED_APPS: Client, Domain models
│   │   ├── templates/          # SHARED_APPS: DeviceTemplate, PointTemplate
│   │   ├── timeseries/         # SHARED_APPS: helpers RLS + queries
│   │   ├── devices/            # TENANT_APPS: Device, Point + provisioning
│   │   ├── dashboards/         # TENANT_APPS: DashboardConfig
│   │   ├── rules/              # TENANT_APPS: Rule, Alert
│   │   └── commands/           # TENANT_APPS: Command, CommandAck
│   ├── health/                 # Health check endpoint
│   ├── manage.py
│   └── requirements.txt
├── ingest/                     # Serviço assíncrono isolado
│   ├── adapters/               # Normalizadores por vendor (parsec_v1, etc)
│   ├── main.py                 # Producer-consumer + batching
│   ├── config.py               # Pydantic settings from env
│   ├── models.py               # Pydantic models (TelemetryV1, AckV1)
│   └── requirements.txt
├── infra/
│   ├── docker-compose.yml      # EMQX + TimescaleDB + Redis + API + Ingest
│   ├── .env.api                # Variáveis Django (não commitar secrets)
│   └── .env.ingest             # Variáveis ingest
├── scripts/
│   ├── seed_dev.py             # Seed de dados de desenvolvimento
│   └── provision_emqx.py       # Provisiona Auth/ACL devices no EMQX
├── Makefile                    # Comandos Linux/Mac
├── manage.ps1                  # Comandos PowerShell/Windows
└── README.md
```

## Modelo de Domínio (Core)

### Hierarquia de Templates

```
DeviceTemplate (code, version, superseded_by)
  └─> PointTemplate[] (name, type, unit, polarity, hysteresis)
  └─> DashboardTemplate (JSON panels)
```

**Imutabilidade**: Templates publicados nunca são alterados destrutivamente. Criar nova versão e setar `superseded_by`.

### Hierarquia de Instâncias (por tenant)

```
Device (FK: template, name, topic_base, credentials_id, status)
  └─> Point[] (FK: point_template, is_contracted, limits, label)
  └─> DashboardConfig (JSON filtrado por points contratados)
```

### RBAC

- **internal_ops**: CRUD completo + provisioning EMQX
- **customer_admin**: leitura + comandos (se habilitado)
- **viewer**: somente leitura

**Regra**: Cliente nunca cria Device/Point diretamente (feito por internal_ops).

## Comandos Essenciais (Cross-Platform)

### Linux/Mac (Makefile)

```bash
make up         # Sobe todos os serviços (Docker Compose)
make down       # Derruba e remove volumes
make logs       # Logs em tempo real (tail=200)
make migrate    # Executa migrações Django
make seed       # Seed de dados dev
make frontend   # Ativa perfil frontend (se houver)
```

### Windows (PowerShell)

```powershell
.\manage.ps1 up        # Sobe serviços
.\manage.ps1 down      # Derruba serviços
.\manage.ps1 logs      # Logs
.\manage.ps1 migrate   # Migrações
.\manage.ps1 health    # Testa /health endpoint
.\manage.ps1 shell     # Django shell
```

### Desenvolvimento Local (Sem Docker)

```bash
# Backend API
cd backend
pip install -r requirements.txt
python manage.py migrate --run-syncdb
python manage.py runserver

# Ingest Service
cd ingest
pip install -r requirements.txt
python main.py
```

**Nota**: Requer PostgreSQL + TimescaleDB + EMQX + Redis rodando.

## MQTT: Contratos de Tópicos e Payloads

### Estrutura de Tópicos (OBRIGATÓRIA)

```
traksense/{tenant}/{site}/{device}/state   # retain + LWT (online/offline)
traksense/{tenant}/{site}/{device}/telem   # telemetria periódica
traksense/{tenant}/{site}/{device}/event   # eventos (startup, config change)
traksense/{tenant}/{site}/{device}/alarm   # alarmes críticos
traksense/{tenant}/{site}/{device}/cmd     # comandos (subscribe device)
traksense/{tenant}/{site}/{device}/ack     # confirmações (publish device)
```

**CRÍTICO**: Ingest assina `+/+/+/telem` e `+/+/+/ack`. Nunca mudar estrutura sem migração.

### Payload de Telemetria (Normalizado v1)

```json
{
  "schema": "v1",
  "ts": "2025-10-07T02:34:12Z",
  "points": [
    {"name": "temp_agua", "t": "float", "v": 7.3, "u": "°C"},
    {"name": "compressor_1_on", "t": "bool", "v": true}
  ],
  "meta": {"fw": "1.2.3", "src": "parsec_v1"}
}
```

**Campos**:
- `t`: `"float"` | `"bool"` | `"enum"` | `"text"`
- `v`: valor (type matching)
- `u`: unidade opcional (string)
- `meta`: metadados arbitrários (JSON)

### Adapters de Vendor

Para payloads proprietários (ex: Parsec), criar adapter em `ingest/adapters/`:

```python
# ingest/adapters/parsec_v1.py
def normalize_parsec_v1(payload: bytes, tenant: str, device: str) -> List[Tuple]:
    """Converte payload Parsec para formato normalizado."""
    # Parse JSON vendor
    data = orjson.loads(payload)
    
    # Mapeia para pontos conhecidos (ex: DI1=status, DI2=fault)
    # Retorna tuplas prontas para INSERT em ts_measure
    return [
        (tenant_uuid, device_uuid, point_uuid, ts, v_num, v_bool, v_text, unit, meta)
    ]
```

### Comandos e ACKs

**Comando** (publicado pela API em `.../cmd`):
```json
{
  "schema": "v1",
  "cmd_id": "01HQXYZ...",  // ULID único
  "op": "reset_fault",
  "pulse_ms": 500,
  "by": "user_uuid"
}
```

**ACK** (publicado pelo device em `.../ack`):
```json
{
  "schema": "v1",
  "cmd_id": "01HQXYZ...",
  "ok": true,
  "ts_exec": "2025-10-07T02:34:15Z",
  "err": null
}
```

Ingest persiste ACKs em `commands_commandack` (por tenant schema) via idempotência por `cmd_id`.

## TimescaleDB: Hypertable e RLS

### Schema da Hypertable

```sql
CREATE TABLE public.ts_measure (
  tenant_id  uuid NOT NULL,
  device_id  uuid NOT NULL,
  point_id   uuid NOT NULL,
  ts         timestamptz NOT NULL,
  v_num      double precision,   -- valores numéricos
  v_bool     boolean,             -- valores booleanos
  v_text     text,                -- strings/enums
  unit       text,                -- unidade (opcional)
  qual       smallint DEFAULT 0,  -- qualidade do dado (0=OK)
  meta       jsonb                -- metadados arbitrários
);

SELECT create_hypertable('public.ts_measure', 'ts');

-- Índices críticos
CREATE INDEX idx_ts_measure_tenant_device_point_ts 
  ON public.ts_measure (tenant_id, device_id, point_id, ts DESC);
CREATE INDEX idx_ts_measure_tenant_ts 
  ON public.ts_measure (tenant_id, ts DESC);
```

### Row Level Security (RLS)

```sql
ALTER TABLE public.ts_measure ENABLE ROW LEVEL SECURITY;

CREATE POLICY ts_tenant_isolation ON public.ts_measure
  USING (tenant_id = current_setting('app.tenant_id')::uuid);
```

**CRÍTICO**: 
- **Django**: Middleware seta `app.tenant_id` automaticamente
- **Ingest**: Deve executar `SET app.tenant_id = $1` antes de cada insert batch

### Continuous Aggregates

```sql
-- Agregação por minuto
CREATE MATERIALIZED VIEW public.ts_measure_1m 
  WITH (timescaledb.continuous) AS
SELECT 
  time_bucket('1 min', ts) AS tb,
  tenant_id, device_id, point_id,
  avg(v_num) AS v_avg,
  min(v_num) AS v_min,
  max(v_num) AS v_max,
  count(*) AS cnt
FROM public.ts_measure 
WHERE v_num IS NOT NULL
GROUP BY tb, tenant_id, device_id, point_id;

-- Agregações 5m, 1h seguem o mesmo padrão
```

### Políticas de Retenção e Compressão

```sql
-- Retenção: 365 dias (dados brutos deletados após 1 ano)
SELECT add_retention_policy('public.ts_measure', INTERVAL '365 days');

-- Compressão: dados > 7 dias (economiza 90% de espaço)
SELECT add_compression_policy('public.ts_measure', INTERVAL '7 days');
```

## Ingest Service: Arquitetura Assíncrona

### Producer-Consumer Pattern

```
[EMQX Broker] 
     |
     v (producer task: asyncio-mqtt)
[asyncio.Queue maxsize=10000] <-- backpressure automático
     |
     v (batcher task)
[Buffer] --> flush por tamanho (500) OU tempo (1s)
     |
     v (executemany com RLS)
[TimescaleDB public.ts_measure]
```

### Features Implementadas

- ✅ **Batching inteligente**: flush por tamanho ou timeout
- ✅ **Backpressure**: Queue com maxsize previne OOM
- ✅ **RLS automático**: `SET app.tenant_id` antes de cada batch
- ✅ **DLQ**: Payloads inválidos vão para `public.ingest_errors`
- ✅ **Métricas Prometheus**: `:9100/metrics` (contador, histogramas, gauges)
- ✅ **Cache UUID**: Tenant e Device UUIDs cachados em memória
- ✅ **Idempotência ACK**: `cmd_id` único previne duplicação

### Exemplo de Adapter

```python
# ingest/adapters/parsec_v1.py
from typing import List, Tuple
import orjson
from models import TelemetryV1

async def normalize_parsec_v1(
    payload: bytes, 
    tenant_uuid: str, 
    device_uuid: str,
    pool: asyncpg.Pool
) -> List[Tuple]:
    """
    Converte payload Parsec para tuplas prontas para INSERT.
    
    Retorna:
        [(tenant_id, device_id, point_id, ts, v_num, v_bool, v_text, unit, meta), ...]
    """
    data = orjson.loads(payload)
    
    # Mapeia DI1/DI2 para pontos conhecidos
    # Faz lookup de point_id do banco (cached)
    # Retorna tuplas
    rows = []
    # ... implementação
    return rows
```

### Debugging Ingest

```bash
# Logs em tempo real
docker compose -f infra/docker-compose.yml logs -f ingest

# Métricas Prometheus
curl http://localhost:9100/metrics | grep ingest_

# Verificar DLQ (payloads inválidos)
docker compose exec api python manage.py shell
>>> from apps.timeseries.models import IngestError
>>> IngestError.objects.all()
```

## API DRF: Endpoints Principais

### Endpoints REST

```
POST   /api/devices/              # Cria Device + Points + DashboardConfig (internal_ops)
GET    /api/devices/{id}/          # Detalhes de device (RBAC)
PATCH  /api/devices/{id}/          # Atualiza status/config

GET    /api/dashboards/{device_id} # DashboardConfig JSON (frontend Spark consome)

GET    /api/data/points            # Séries temporais
       ?device={uuid}&point={uuid}&from={iso}&to={iso}&agg={1m|5m|1h}
       # Usa continuous aggregates (ts_measure_1m, etc)

POST   /api/cmd/{device_id}        # Publica comando MQTT + aguarda ACK
       Body: {"op": "reset_fault", "pulse_ms": 500}
       Resposta: {"cmd_id": "...", "status": "pending"}

GET    /health                     # Health check (public, sem auth)
       Resposta: {"status": "ok"}
```

### RBAC Implementation

**Grupos Django**:
- `internal_ops`: Full access + provisioning
- `customer_admin`: Read + comandos (se habilitado)
- `viewer`: Read-only

**DRF Permissions**:
```python
# apps/devices/permissions.py
class IsInternalOps(BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name='internal_ops').exists()
```

### OpenAPI Schema

Django expõe schema em `/schema/` para gerar clients:
```bash
curl http://localhost:8000/schema/ > openapi.json
```

Frontend usa `openapi-typescript-codegen` para gerar hooks React Query.

## EMQX: Provisionamento e ACL

### Provisionamento ao Criar Device

```python
# apps/devices/provisioning/emqx.py
def provision_device_in_emqx(device: Device) -> dict:
    """
    1. Gera username/password únicos
    2. Cria authentication via HTTP API EMQX
    3. Configura ACL rules:
       - PUBLISH: .../state, .../telem, .../event, .../alarm, .../ack
       - SUBSCRIBE: .../cmd
    4. Configura LWT (Last Will Testament) em .../state com retain
    """
    # HTTP API: POST http://emqx:18083/api/v5/authentication/...
    # Retorna credentials_id para armazenar em Device.credentials_id
```

### ACL Rules (PostgreSQL ou HTTP API)

```sql
-- Se usar PostgreSQL Auth/ACL Plugin
INSERT INTO emqx_acl (username, permission, action, topic)
VALUES 
  ('device_123', 'allow', 'publish', 'traksense/demo/site-a/device_123/telem'),
  ('device_123', 'allow', 'subscribe', 'traksense/demo/site-a/device_123/cmd');
```

### Dashboard EMQX

- **URL**: http://localhost:18083
- **Default**: admin / public (TROCAR EM PRODUÇÃO!)
- **Features**: Clients online, Subscriptions, Topics, Rules Engine

### TLS em Produção

```yaml
# docker-compose.yml (prod)
ports:
  - "8883:8883"  # MQTT com TLS
volumes:
  - ./certs:/opt/emqx/etc/certs:ro
```

## Dashboards: Templates e Configuração

### DashboardTemplate (Global, SHARED_APPS)

```json
{
  "schema": "v1",
  "device_template_code": "inverter_v1_parsec",
  "panels": [
    {
      "type": "status",
      "title": "Estado do Inversor",
      "point_template": "device_state",
      "mappings": {
        "RUN": "Em operação",
        "STOP": "Parado",
        "FAULT": "Falha"
      }
    },
    {
      "type": "timeseries",
      "title": "Temperatura da Água",
      "point_template": "temp_agua",
      "agg": "1m",
      "yUnit": "°C"
    },
    {
      "type": "button",
      "title": "Reset de Falha",
      "op": "reset_fault",
      "params": {"pulse_ms": 500}
    }
  ],
  "layout": "cards-2col"
}
```

### DashboardConfig (Por Device, TENANT_APPS)

Gerado ao criar Device via `provision_device_from_template()`:

```python
# apps/devices/services.py
def provision_device_from_template(device: Device, template: DeviceTemplate):
    """
    1. Cria Points baseados em PointTemplates (filtra is_contracted)
    2. Cria DashboardConfig baseado em DashboardTemplate
    3. Substitui point_template → point_id real
    4. Provisiona device no EMQX
    """
    # DashboardConfig.config_json contém painel renderizável
```

**Frontend Spark** busca `/api/dashboards/{device_id}` e renderiza com ECharts/Mantine.

## Convenções de Código e Qualidade

### Python (Backend/Ingest)

- **Formatação**: Black (line-length 100)
- **Lint**: Ruff (fast linter, substitui flake8/isort)
- **Type Checking**: mypy (strict em ingest, moderate em backend)
- **Docstrings**: Google style (obrigatório em funções públicas)

```python
# Exemplo de docstring
def get_tenant_uuid(pool: asyncpg.Pool, schema_name: str) -> str:
    """
    Resolve tenant UUID a partir do schema_name.
    
    Args:
        pool: Pool de conexões asyncpg
        schema_name: Nome do schema do tenant (ex: 'demo')
    
    Returns:
        UUID do tenant como string, ou None se não encontrado
    """
```

### Django

- **Models**: sempre incluir `__str__`, `Meta.verbose_name`, docstrings
- **Migrations**: nomear descritivamente (`0003_add_rls_policy.py`)
- **Signals**: EVITAR para lógica complexa; usar services explícitos
- **Tests**: `pytest-django` com fixtures em `conftest.py`

### Nomenclatura

- **snake_case**: funções, variáveis, nomes de pontos MQTT, colunas SQL
- **PascalCase**: classes Django/DRF
- **UPPER_SNAKE**: constantes
- **UUIDs**: sempre `uuid.uuid4()` (ou ULID para comandos)

### Commits

Formato: `<type>(<scope>): <description>`

```
feat(ingest): implementa batching com asyncpg.executemany
fix(api): corrige query RLS em /api/data/points
docs(readme): atualiza instruções Windows
refactor(devices): extrai provisionamento EMQX para service
test(ingest): adiciona test para adapter parsec_v1
```

### Testes

```bash
# Backend (Django)
pytest backend/ -v --cov=backend --cov-report=html

# Ingest
pytest ingest/ -v --cov=ingest

# Testes de integração (requer Docker)
pytest backend/apps/devices/tests/test_provision_integration.py
```

**Coverage mínimo**: 80% (configurado em `pytest.ini`)

## Tarefas Comuns para AI Agents

### Adicionar Novo DeviceTemplate

1. Criar registro em `apps.templates.models.DeviceTemplate`
2. Criar `PointTemplate[]` associados
3. Criar `DashboardTemplate` JSON
4. Migração + seed script

### Adicionar Endpoint DRF

```python
# apps/devices/views.py
class DeviceViewSet(viewsets.ModelViewSet):
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer
    permission_classes = [IsAuthenticated, IsInternalOps]
    
    @action(detail=True, methods=['post'])
    def provision(self, request, pk=None):
        """Provisiona device no EMQX."""
        device = self.get_object()
        result = provision_device_in_emqx(device)
        return Response(result)
```

### Criar Adapter de Vendor

1. Arquivo em `ingest/adapters/{vendor}_v{version}.py`
2. Função `normalize_{vendor}_v{version}(payload, tenant_uuid, device_uuid, pool)`
3. Validação Pydantic dos campos obrigatórios
4. Lookup de `point_id` (cached)
5. Retornar tuplas para `executemany`

### Adicionar Continuous Aggregate

```sql
-- Migration: 0004_add_timeseries_5m_aggregate.py
CREATE MATERIALIZED VIEW public.ts_measure_5m 
  WITH (timescaledb.continuous) AS
SELECT 
  time_bucket('5 min', ts) AS tb,
  tenant_id, device_id, point_id,
  avg(v_num) AS v_avg,
  min(v_num) AS v_min,
  max(v_num) AS v_max
FROM public.ts_measure 
WHERE v_num IS NOT NULL
GROUP BY tb, tenant_id, device_id, point_id;
```

## Fora de Escopo (NÃO FAZER)

- ❌ **UI React/HTML/CSS**: Frontend está em repo separado
- ❌ **Telemetria por schema de tenant**: Usar `public.ts_measure` com RLS
- ❌ **Grafana**: Dashboards são JSON consumidos pelo frontend Spark
- ❌ **Mudar estrutura de tópicos MQTT**: Contrato fixo
- ❌ **Alterar templates publicados destrutivamente**: Criar nova versão

## Glossário

- **DeviceTemplate**: Tipo de equipamento (ex: inverter_v1_parsec)
- **PointTemplate**: Ponto de telemetria padrão (ex: temp_agua)
- **DashboardTemplate**: Layout de painéis JSON (global)
- **DashboardConfig**: Instância de dashboard por device (filtrado)
- **RLS**: Row Level Security (filtragem por tenant_id)
- **LWT**: Last Will and Testament (MQTT offline detection)
- **ACK**: Acknowledgment (confirmação de comando)
- **DLQ**: Dead Letter Queue (payloads inválidos)
- **Continuous Aggregate**: Materialized view TimescaleDB (pré-agregação)

## Debugging e Troubleshooting

### Logs

```bash
# API
docker compose -f infra/docker-compose.yml logs -f api

# Ingest
docker compose -f infra/docker-compose.yml logs -f ingest

# EMQX
docker compose -f infra/docker-compose.yml logs -f emqx
```

### Django Shell

```powershell
.\manage.ps1 shell
# Ou:
docker compose -f infra/docker-compose.yml exec api python manage.py shell
```

```python
# Verificar RLS
from apps.tenancy.models import Client
tenant = Client.objects.first()
from django.db import connection
connection.cursor().execute(f"SET app.tenant_id = '{tenant.uuid}'")

# Query telemetria
from apps.timeseries.models import Measure
Measure.objects.filter(device_id='...')[:10]
```

### Health Checks

```bash
# API
curl http://localhost:8000/health

# EMQX
curl http://localhost:18083/api/v5/status

# Métricas Ingest (Prometheus)
curl http://localhost:9100/metrics | grep ingest_
```

## Documentação Adicional

- **README.md**: Setup rápido e visão geral
- **SETUP_WINDOWS.md**: Instruções específicas PowerShell
- **docs/adr/**: Architecture Decision Records
- **VALIDATION_*.md**: Checklists de validação por fase
- **API_IMPLEMENTATION_COMPLETE.md**: Status de implementação

**SEMPRE comentar código em português** para facilitar manutenção pela equipe brasileira.