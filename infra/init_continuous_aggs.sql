-- ============================================================================
-- Continuous Aggregates para TimescaleDB
-- Nota: Deve ser executado FORA de transação (atomic=False)
-- ============================================================================

-- 1. Aggregate 1 minuto
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

-- 2. Aggregate 5 minutos
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

-- 3. Aggregate 1 hora
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

-- 4. Refresh Policies
SELECT add_continuous_aggregate_policy('public.ts_measure_1m',
    start_offset => INTERVAL '3 hours',
    end_offset => INTERVAL '1 minute',
    schedule_interval => INTERVAL '5 minutes',
    if_not_exists => TRUE
);

SELECT add_continuous_aggregate_policy('public.ts_measure_5m',
    start_offset => INTERVAL '12 hours',
    end_offset => INTERVAL '5 minutes',
    schedule_interval => INTERVAL '15 minutes',
    if_not_exists => TRUE
);

SELECT add_continuous_aggregate_policy('public.ts_measure_1h',
    start_offset => INTERVAL '3 days',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists => TRUE
);
