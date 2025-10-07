"""
Timeseries Models - Telemetria IoT (TimescaleDB)

Este arquivo está INTENCIONALMENTE VAZIO.

Por quê?
-------
A tabela public.ts_measure NÃO é definida via Django ORM (models.Model).
Em vez disso, é criada via SQL puro (RunSQL) na migration 0001_ts_schema.py.

Motivo:
------
TimescaleDB requer features SQL específicas que Django ORM não suporta:
1. Hypertables (create_hypertable)
2. Continuous aggregates (materialized views com refresh policies)
3. Compression policies
4. Retention policies
5. Row Level Security (RLS) com custom GUCs

Estrutura da tabela:
-------------------
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

-- Hypertable
SELECT create_hypertable('public.ts_measure', 'ts');

-- RLS
ALTER TABLE public.ts_measure ENABLE ROW LEVEL SECURITY;
CREATE POLICY ts_tenant_isolation ON public.ts_measure
USING (tenant_id = current_setting('app.tenant_id')::uuid);

-- Continuous Aggregates
CREATE MATERIALIZED VIEW public.ts_measure_1m ...;
CREATE MATERIALIZED VIEW public.ts_measure_5m ...;
CREATE MATERIALIZED VIEW public.ts_measure_1h ...;

-- Compression
SELECT add_compression_policy('public.ts_measure', INTERVAL '7 days');

-- Retention
SELECT add_retention_policy('public.ts_measure', INTERVAL '365 days');

Como acessar dados:
------------------
Não use Django ORM! Use raw SQL ou asyncpg.

Exemplo 1 - Django raw SQL:
    from django.db import connection
    with connection.cursor() as cur:
        cur.execute("SET LOCAL app.tenant_id = %s", [tenant_id])
        cur.execute("SELECT * FROM public.ts_measure WHERE device_id = %s", [device_id])
        rows = cur.fetchall()

Exemplo 2 - asyncpg (ingest):
    async with pool.acquire() as conn:
        await conn.execute("SET app.tenant_id = $1", tenant_id)
        await conn.executemany(
            "INSERT INTO public.ts_measure(...) VALUES (...)", rows
        )

Ver também:
----------
- views.py: queries com agregação (1m/5m/1h)
- dbutils.py: helpers (set_tenant_guc_for_conn, get_aggregate_view_name)
- migrations/0001_ts_schema.py: DDL completo (hypertable, RLS, aggregates)

Autor: TrakSense Team
Data: 2025-10-07
"""

# Este arquivo está intencionalmente vazio
# A tabela ts_measure é criada via SQL migration (0001_ts_schema.py)
# Não há Django models aqui

# Por quê não usar Django ORM?
# - TimescaleDB hypertables requerem create_hypertable() (SQL nativo)
# - Continuous aggregates são materialized views (não suportadas por ORM)
# - RLS com custom GUCs (app.tenant_id) requer SQL nativo
# - Compression/retention policies são extensões TimescaleDB

# Como acessar dados?
# - Raw SQL: connection.cursor() + cur.execute()
# - asyncpg: pool.acquire() + conn.execute() (ingest)
# - Ver views.py e dbutils.py para helpers
