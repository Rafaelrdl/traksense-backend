-- ============================================================================
-- WORKAROUND: Views normais ao invés de Continuous Aggregates
-- Motivo: TimescaleDB não permite continuous aggregates com RLS habilitado
-- 
-- Trade-off:
-- - Views normais: calculam em tempo real (mais lento mas funciona com RLS)
-- - Continuous Aggregates: pré-calculados (mais rápido mas incompatível com RLS)
--
-- Decisão: Usar views normais por ora. Em produção, avaliar:
--   1. Desabilitar RLS e usar app.tenant_id em WHERE manual
--   2. Criar aggregate tables separadas com triggers
--   3. Usar TimescaleDB >= 2.15 (se suportar RLS + CAGGs)
-- ============================================================================

-- 1. View agregada de 1 minuto
DROP VIEW IF EXISTS public.ts_measure_1m CASCADE;
CREATE VIEW public.ts_measure_1m AS
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

-- 2. View agregada de 5 minutos
DROP VIEW IF EXISTS public.ts_measure_5m CASCADE;
CREATE VIEW public.ts_measure_5m AS
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

-- 3. View agregada de 1 hora
DROP VIEW IF EXISTS public.ts_measure_1h CASCADE;
CREATE VIEW public.ts_measure_1h AS
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

-- Nota: Views normais respeitam RLS automaticamente (herdam da tabela base)
-- Performance: Ainda boa para queries com índices adequados e range limitado
