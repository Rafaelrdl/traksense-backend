-- ============================================================================
-- Inicialização manual do TimescaleDB (workaround para atomic migration)
-- ============================================================================

-- 1. HYPERTABLE: public.ts_measure
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

-- Criar hypertable
SELECT create_hypertable(
    'public.ts_measure',
    'ts',
    if_not_exists => TRUE,
    chunk_time_interval => INTERVAL '1 day'
);

-- 2. ÍNDICES
CREATE INDEX IF NOT EXISTS ts_measure_tenant_devpt_ts_idx
  ON public.ts_measure (tenant_id, device_id, point_id, ts DESC);

CREATE INDEX IF NOT EXISTS ts_measure_tenant_ts_idx
  ON public.ts_measure (tenant_id, ts DESC);

CREATE INDEX IF NOT EXISTS ts_measure_device_ts_idx
  ON public.ts_measure (device_id, ts DESC);

-- 3. ROW LEVEL SECURITY (RLS)
ALTER TABLE public.ts_measure ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS ts_tenant_isolation ON public.ts_measure;

CREATE POLICY ts_tenant_isolation ON public.ts_measure
USING (tenant_id::text = current_setting('app.tenant_id', TRUE));
