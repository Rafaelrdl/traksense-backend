Copilot Custom Instructions — TrakSense (IoT Monitoring)

Contexto
Este repositório implementa a plataforma de monitoramento IoT (multi-tenant) sem CMMS nesta fase.
Frontend (Spark): existe um projeto React (Spark) separado e desconectado desta codebase na Fase 1. Não gerar nem alterar componentes de UI aqui além de contratos/DTOs. Este repositório cobre Backend (Django/DRF + django-tenants), Ingest (Python assíncrono), EMQX provisioning e TimescaleDB.

TL;DR (regras de ouro p/ o Copilot)

Multi-tenant: metadados por tenant; telemetria em uma única hypertable (schema public) com RLS por tenant_id.

Ingest é um serviço Python assíncrono separado (MQTT → valida/normaliza → Timescale com batch insert).

Broker: EMQX com AuthN/ACL por device, LWT e TLS (prod).

Dashboards: não renderizamos aqui. O frontend Spark (em outro repo) consome DashboardConfig (JSON) e endpoints de dados.

Não implementar telas/React nesta codebase. Gerar APIs, modelos, migrações, RLS, adapters de ingest, testes e scripts de provisionamento.

Preferir tipagem forte, Pydantic para schemas, asyncpg para ingest, DRF para APIs.

Nunca duplicar telemetria em tabelas por tenant; nunca quebrar o contrato de tópicos/payloads MQTT descritos abaixo.

1) Escopo por fase

Fase 1 (este repo):
Backend (Django/DRF + django-tenants), Timescale (hypertable única), Ingest assíncrono (asyncio-mqtt), EMQX provisioning, APIs de dados, commands (ACK), templates de dashboards (somente JSON), RBAC e RLS.

Frontend Spark (outro repo):
Renderizador de dashboards (ECharts/Mantine) e UI. Não desenvolver aqui.

2) Stacks e decisões arquiteturais (ADR-000)

Broker: EMQX (Docker), Auth/ACL por device.

Backend API: Django 4+/DRF + django-tenants (multi-tenant por domínio/subdomínio).

DB: PostgreSQL + TimescaleDB.

Metadados (Tenant/Site/Device/Point/Rules/Dashboards) → schemas de tenants.

Telemetria (time-series) → public.ts_measure (+ continuous aggregates, retenção e compressão) com RLS por tenant_id.

Ingest: serviço Python assíncrono isolado

MQTT client: asyncio-mqtt (ou gmqtt)

Validação: Pydantic (adapters por vendor/payload)

Persistência: asyncpg com batch insert/COPY quando aplicável

Mensageria opcional: Redis para Celery (regras/alertas notificação).

Auth/SSO: placeholder (poderá ser Keycloak); por ora Django auth.

Motivo: simplificar operações (uma hypertable), manter isolamento lógico por RLS, escalar ingest e API de forma independente e preservar o visual no Spark.

3) Estrutura de pastas (sugerida)
/backend
  /apps
    /tenancy
    /devices
    /dashboards
    /rules
    /commands
    /timeseries   # helpers/queries p/ Timescale + RLS
  manage.py
/ingest
  /adapters
    parsec_v1.py
  main.py
/infra
  docker-compose.yml
  /emqx
    emqx.conf
    authz.sql    # se usar Postgres Auth/ACL
/shared
  /schemas       # JSON Schema/Pydantic models exportados
  /types         # Tipos TS gerados p/ o frontend (DTOs)
/scripts
  provision_emqx.py
  seed_dev.py
copilot-instructions.md


Arquivos críticos que o Copilot não deve alterar sem pedido explícito:

Configuração de RLS/retention/compression da hypertable.

Contratos MQTT (tópicos), formatos de payload e nomes de colunas de ts_measure.

Estrutura base de tenants/tenant middleware.

4) Modelo de domínio (resumo)

Tenant / Site

DeviceTemplate (ex.: inverter_v1_parsec, chiller_v1)

PointTemplate (tipo, unidade, enum, polarity, histerese default)

Device (FK template, topic_base, credentials_id)

Point (FK device; is_contracted, limits, label)

DashboardTemplate (JSON de painéis) → DashboardConfig (instância filtrada por pontos contratados)

Rule (limites/histerese/janela)

CommandDefinition (ex.: reset_fault) e Command / CommandAck

RBAC: internal_ops, customer_admin, viewer

Nota: criação de Device/Point é restrita a internal_ops (painel interno). Cliente pode apenas visualizar/ajustar limites (se permitido).

5) MQTT — contratos de tópicos e payloads

Tópicos (prefixo obrigatório):

traksense/{tenant}/{site}/{device}/state   (retain, LWT)
traksense/{tenant}/{site}/{device}/telem
traksense/{tenant}/{site}/{device}/event
traksense/{tenant}/{site}/{device}/alarm
traksense/{tenant}/{site}/{device}/cmd
traksense/{tenant}/{site}/{device}/ack


Telemetria (envelope normalizado):

{
  "schema": "v1",
  "ts": "2025-10-07T02:34:12Z",
  "points": [
    {"name":"temp_agua", "t":"float", "v":7.3, "u":"°C"},
    {"name":"compressor_1_on", "t":"bool", "v":true}
  ],
  "meta": {"fw":"1.2.3","src":"parsec_v1"}
}


Command (ex.: reset de falha):

{"schema":"v1","cmd_id":"ulid","op":"reset_fault","pulse_ms":500,"by":"user_ulid"}


ACK:

{"schema":"v1","cmd_id":"ulid","ok":true,"ts_exec":"...","err":null}


Parsec (inversores) — mapeamento

DI1: status → 1=RUN, 0=STOP

DI2: fault → 1=FAULT, 0=OK

Relé: comando reset_fault (pulso pulse_ms)

Regras: FAULT sobrepõe RUN/STOP; aplicar debounce/histerese.

6) Banco de dados — Timescale (telemetria)

Hypertable única:

CREATE TABLE public.ts_measure (
  tenant_id  uuid NOT NULL,
  device_id  uuid NOT NULL,
  point_id   uuid NOT NULL,
  ts         timestamptz NOT NULL,
  v_num      double precision,
  v_bool     boolean,
  v_text     text,
  unit       text,
  qual       smallint DEFAULT 0,
  meta       jsonb
);
SELECT create_hypertable('public.ts_measure','ts');

-- Índices
CREATE INDEX ON public.ts_measure (tenant_id, device_id, point_id, ts DESC);
CREATE INDEX ON public.ts_measure (tenant_id, ts DESC);

-- RLS (exemplo)
ALTER TABLE public.ts_measure ENABLE ROW LEVEL SECURITY;
CREATE POLICY ts_tenant_isolation ON public.ts_measure
USING (tenant_id = current_setting('app.tenant_id')::uuid);

-- Retenção/Compressão/Agregados
SELECT add_retention_policy('public.ts_measure', INTERVAL '365 days');
SELECT add_compression_policy('public.ts_measure', INTERVAL '7 days');
CREATE MATERIALIZED VIEW public.ts_measure_1m WITH (timescaledb.continuous) AS
SELECT time_bucket('1 min', ts) tb, tenant_id, device_id, point_id,
       avg(v_num) v_avg, min(v_num) v_min, max(v_num) v_max
FROM public.ts_measure WHERE v_num IS NOT NULL
GROUP BY tb, tenant_id, device_id, point_id;


Copilot: sempre respeitar RLS via SET app.tenant_id = '<uuid>' na conexão (middleware no Django; setter no ingest ao persistir).

7) Ingest (serviço assíncrono)

Assinar .../telem e .../ack via asyncio-mqtt

Validar payloads com Pydantic (adapters por vendor: parsec_v1)

Converter para envelope normalizado e inserir em lote (asyncpg.executemany ou COPY)

DLQ (ingest_errors) para payload inválido

Publicar eventos (regras) no Redis/Celery quando necessário

Skeleton (conceitual):

# /ingest/main.py
import asyncio, os, asyncpg
from asyncio_mqtt import Client
from adapters.parsec_v1 import normalize as norm

async def run():
  pool = await asyncpg.create_pool(os.environ["DATABASE_URL"])
  async with Client(os.environ["MQTT_HOST"]) as mqtt, mqtt.unfiltered_messages() as msgs:
    await mqtt.subscribe("traksense/+/+/+/telem")
    async for m in msgs:
      t, s, d, _ = m.topic.split("/")[1:5]
      rows = norm(m.payload, tenant=t, device=d)  # retorna tuplas p/ INSERT
      async with pool.acquire() as con:
        await con.execute("SET app.tenant_id = $1", t)
        await con.executemany(
          "INSERT INTO public.ts_measure(tenant_id,device_id,point_id,ts,v_num,v_bool,v_text,unit,meta)"
          "VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)", rows)

if __name__ == "__main__":
  asyncio.run(run())

8) API DRF (contratos principais)

POST /api/devices/ (somente internal_ops) → cria Device/Points, provisiona EMQX, instancia DashboardConfig a partir de DashboardTemplate do DeviceTemplate.

GET /api/dashboards/{device_id} → retorna DashboardConfig (JSON) p/ o frontend Spark renderizar.

GET /api/data/points?device=...&point=...&from=...&to=...&agg=1m → séries com agregação (usa continuous aggregates).

POST /api/cmd/{device_id} → publica comando, registra Command e aguarda ACK (timeout configurável).

Regras de RBAC:

internal_ops: CRUD de Device/Point/Template/DashboardTemplate, provisionamento EMQX.

customer_admin: leitura; comandos permitidos (se habilitado).

viewer: leitura.

9) EMQX — provisionamento e ACL

Ao criar Device, gerar username/password e gravar ACL:

publish: .../state|telem|event|alarm|ack

subscribe: .../cmd

LWT em state com retain.

TLS no 8883 em produção.

Script CLI/HTTP: /scripts/provision_emqx.py.

10) Dashboards (templates e instância)

DashboardTemplate (por DeviceTemplate) define painéis (tipos: timeseries, status, timeline, kpi, button).

DashboardConfig é gerado ao criar o Device (filtra pontos contratados).

O frontend Spark consome DashboardConfig e renderiza (ECharts). Não renderizar aqui.

Exemplo de painel:

{
  "schema":"v1",
  "panels":[
    {"type":"status","title":"Estado","point":"device_state","mappings":{"RUN":"Em operação","STOP":"Parado","FAULT":"Falha"}},
    {"type":"timeseries","title":"Temperatura da água","point":"temp_agua","agg":"1m","yUnit":"°C"},
    {"type":"button","title":"Reset falha","op":"reset_fault","params":{"pulse_ms":500}}
  ],
  "layout":"cards-2col"
}

11) Qualidade e DevEx

Lint/format: Ruff + Black; typing: mypy (estrito em ingest).

Testes: Pytest (unit/integration), fixtures de payloads e consultas de séries.

CI: lint + testes + migrações.

Docker/Compose: subir EMQX, Timescale, Redis, API, Ingest.

Secrets via .env.* (não commitar).

12) Tarefas típicas que o Copilot deve ajudar (com prioridade)

Gerar models DRF (DeviceTemplate/PointTemplate/Device/Point/Rule/Command/DashboardTemplate/Config).

Produzir migrações SQL p/ Timescale (hypertable, índices, policies RLS, retention/compression, continuous aggregates).

Implementar provision_emqx.py (Auth/ACL) e hooks de criação de device.

Escrever adapters Pydantic (ex.: parsec_v1) com validação e normalização.

Implementar endpoints /api/devices, /api/dashboards/{id}, /api/data/points, /api/cmd/{id} (+ testes).

Criar jobs Celery para regras/alertas (threshold/histerese/janelas).

Gerar DTOs/JSON Schema e tipos TS em /shared/types para consumo no frontend.

13) Fora de escopo (nesta codebase / Fase 1)

Qualquer UI React/HTML/CSS (está no frontend Spark, outro repo).

Integração CMMS/TrakNor (será feita depois).

Persistir telemetria por schema de tenant (não fazer).

Grafana (não usar aqui; dashboards são do frontend Spark).

14) Convenções de nome e commit

Tópicos MQTT, colunas e nomes de pontos são snake_case.

tenant_id, device_id, point_id como UUID/ULID.

Mensagens de commit: feat(ingest): batch insert asyncpg, fix(api): RLS setter, etc.

15) Glossário rápido

DeviceTemplate/PointTemplate: definem tipo de equipamento e pontos padrão.

DashboardTemplate/Config: modelo de painéis → instância por device.

RLS: Row Level Security — filtra dados por tenant_id.

LWT: Last Will and Testament (offline no state).

ACK: confirmação de comando.

16) Como o Copilot deve proceder quando houver ambiguidade

Priorizar padrões estabelecidos acima.

Se faltarem campos, propor extensões mantendo compatibilidade (ex.: adicionar qual/meta).

Não inventar novos tópicos MQTT, não mover telemetria para tabelas por tenant.

Documentar decisões em comentários e, se relevante, criar ADR em /docs/adr/ADR-00X.md.

Lembrete final: o frontend (Spark) é outro projeto. Aqui, entregue APIs estáveis, ingest confiável, provisionamento EMQX, Timescale + RLS, e templates JSON de dashboards — nada de UI.



Sempre comente os codigos para ajudar no entendimento do codigo em portugues.