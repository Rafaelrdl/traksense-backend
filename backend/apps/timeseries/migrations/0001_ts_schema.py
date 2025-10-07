"""
TimescaleDB schema: hypertable, índices, RLS e continuous aggregates.

IMPORTANTE: Esta migration cria a estrutura de telemetria no schema public.
- Hypertable única (ts_measure) com particionamento por tempo
- RLS por tenant_id (usando GUC app.tenant_id)
- Continuous aggregates (1m, 5m, 1h) para performance
- Políticas de refresh automático
"""
from django.db import migrations


DDL_CREATE = r"""
-- ============================================================================
-- 1. HYPERTABLE: public.ts_measure
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.ts_measure (
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

-- Criar hypertable (se já não existir)
SELECT create_hypertable(
    'public.ts_measure',
    'ts',
    if_not_exists => TRUE,
    chunk_time_interval => INTERVAL '1 day'
);

-- ============================================================================
-- 2. ÍNDICES para performance
-- ============================================================================
CREATE INDEX IF NOT EXISTS ts_measure_tenant_devpt_ts_idx
  ON public.ts_measure (tenant_id, device_id, point_id, ts DESC);

CREATE INDEX IF NOT EXISTS ts_measure_tenant_ts_idx
  ON public.ts_measure (tenant_id, ts DESC);

CREATE INDEX IF NOT EXISTS ts_measure_device_ts_idx
  ON public.ts_measure (device_id, ts DESC);

-- ============================================================================
-- 3. ROW LEVEL SECURITY (RLS)
-- ============================================================================
ALTER TABLE public.ts_measure ENABLE ROW LEVEL SECURITY;

-- Drop policy se existir (para permitir rerun da migration)
DROP POLICY IF EXISTS ts_tenant_isolation ON public.ts_measure;

-- Policy: apenas dados do tenant atual (via GUC app.tenant_id)
CREATE POLICY ts_tenant_isolation ON public.ts_measure
USING (tenant_id::text = current_setting('app.tenant_id', TRUE));

-- IMPORTANTE: Superuser bypassa RLS por padrão. Para forçar RLS mesmo em superuser:
-- ALTER TABLE public.ts_measure FORCE ROW LEVEL SECURITY;
-- (Descomente acima se necessário em produção)

-- ============================================================================
-- 4. CONTINUOUS AGGREGATES (Materialized Views)
-- ============================================================================

-- 4.1. Aggregate 1 minuto
DROP MATERIALIZED VIEW IF EXISTS public.ts_measure_1m CASCADE;
CREATE MATERIALIZED VIEW public.ts_measure_1m
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('1 minute', ts) AS tb,
    tenant_id, 
    device_id, 
    point_id,
    avg(v_num) AS v_avg, 
    min(v_num) AS v_min, 
    max(v_num) AS v_max,
    count(*) AS v_count
FROM public.ts_measure
WHERE v_num IS NOT NULL
GROUP BY tb, tenant_id, device_id, point_id;

-- 4.2. Aggregate 5 minutos
DROP MATERIALIZED VIEW IF EXISTS public.ts_measure_5m CASCADE;
CREATE MATERIALIZED VIEW public.ts_measure_5m
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('5 minutes', ts) AS tb,
    tenant_id, 
    device_id, 
    point_id,
    avg(v_num) AS v_avg, 
    min(v_num) AS v_min, 
    max(v_num) AS v_max,
    count(*) AS v_count
FROM public.ts_measure
WHERE v_num IS NOT NULL
GROUP BY tb, tenant_id, device_id, point_id;

-- 4.3. Aggregate 1 hora
DROP MATERIALIZED VIEW IF EXISTS public.ts_measure_1h CASCADE;
CREATE MATERIALIZED VIEW public.ts_measure_1h
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('1 hour', ts) AS tb,
    tenant_id, 
    device_id, 
    point_id,
    avg(v_num) AS v_avg, 
    min(v_num) AS v_min, 
    max(v_num) AS v_max,
    count(*) AS v_count
FROM public.ts_measure
WHERE v_num IS NOT NULL
GROUP BY tb, tenant_id, device_id, point_id;

-- ============================================================================
-- 5. REFRESH POLICIES (atualização automática dos aggregates)
-- ============================================================================

-- 5.1. Policy para aggregate 1m (refresh a cada 5 minutos)
SELECT add_continuous_aggregate_policy(
    'public.ts_measure_1m',
    start_offset => INTERVAL '2 days',
    end_offset   => INTERVAL '5 minutes',
    schedule_interval => INTERVAL '5 minutes',
    if_not_exists => TRUE
);

-- 5.2. Policy para aggregate 5m (refresh a cada 15 minutos)
SELECT add_continuous_aggregate_policy(
    'public.ts_measure_5m',
    start_offset => INTERVAL '7 days',
    end_offset   => INTERVAL '15 minutes',
    schedule_interval => INTERVAL '15 minutes',
    if_not_exists => TRUE
);

-- 5.3. Policy para aggregate 1h (refresh a cada 1 hora)
SELECT add_continuous_aggregate_policy(
    'public.ts_measure_1h',
    start_offset => INTERVAL '60 days',
    end_offset   => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists => TRUE
);

-- ============================================================================
-- 6. RETENTION POLICY (opcional - descomentar se quiser limitar retenção)
-- ============================================================================
-- Exemplo: manter dados raw por 90 dias
-- SELECT add_retention_policy('public.ts_measure', INTERVAL '90 days', if_not_exists => TRUE);

-- ============================================================================
-- 7. COMPRESSION POLICY (opcional - descomentar para habilitar compressão)
-- ============================================================================
-- Comprimir chunks com mais de 7 dias
-- ALTER TABLE public.ts_measure SET (
--   timescaledb.compress,
--   timescaledb.compress_segmentby = 'tenant_id,device_id,point_id'
-- );
-- SELECT add_compression_policy('public.ts_measure', INTERVAL '7 days', if_not_exists => TRUE);

"""

DDL_DROP = r"""
-- Rollback: remove tudo (cuidado em produção!)
DROP POLICY IF EXISTS ts_tenant_isolation ON public.ts_measure;
DROP MATERIALIZED VIEW IF EXISTS public.ts_measure_1h CASCADE;
DROP MATERIALIZED VIEW IF EXISTS public.ts_measure_5m CASCADE;
DROP MATERIALIZED VIEW IF EXISTS public.ts_measure_1m CASCADE;
DROP TABLE IF EXISTS public.ts_measure CASCADE;
"""


class Migration(migrations.Migration):

    initial = True
    
    dependencies = []

    operations = [
        migrations.RunSQL(
            sql=DDL_CREATE,
            reverse_sql=DDL_DROP,
        ),
    ]
