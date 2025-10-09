# Guia de Validação - Fase R (CAGGs + VIEWs)

**Objetivo**: Verificar se a implementação da Opção B está funcionando corretamente.

---

## ✅ Checklist de Validação

### 1. Verificar Migrations Aplicadas

```bash
cd backend
python manage.py showmigrations timeseries
```

**Esperado**: Todas as migrations de `0001` a `0028` marcadas com `[X]`

**Críticas**:
- `[X] 0005_raw_no_compress_short_retention` - RLS desabilitado
- `[X] 0012_cagg_1m_materialize` - CAGG 1m pronto
- `[X] 0019_cagg_5m_materialize` - CAGG 5m pronto
- `[X] 0026_cagg_1h_materialize` - CAGG 1h pronto
- `[X] 0027_tenant_scoped_views` - VIEWs criadas
- `[X] 0028_restrict_grants` - GRANTs restritos

---

### 2. Verificar CAGGs Criados

```bash
cd infra
docker compose exec db psql -U app_migrations -d traksense
```

```sql
-- Listar CAGGs
SELECT viewname FROM pg_matviews 
WHERE schemaname='public' AND viewname LIKE 'ts_measure_%' 
ORDER BY viewname;
```

**Esperado**:
```
 viewname       
----------------
 ts_measure_1h
 ts_measure_1m
 ts_measure_5m
(3 rows)
```

---

### 3. Verificar VIEWs Tenant-Scoped

```sql
SELECT viewname FROM pg_views 
WHERE schemaname='public' AND viewname LIKE '%_tenant' 
ORDER BY viewname;
```

**Esperado**:
```
 viewname              
-----------------------
 ts_measure_1h_tenant
 ts_measure_1m_tenant
 ts_measure_5m_tenant
 ts_measure_tenant
(4 rows)
```

---

### 4. Verificar security_barrier nas VIEWs

```sql
SELECT 
    viewname,
    CASE 
        WHEN viewowner = 'app_migrations' THEN '✅'
        ELSE '❌ ERRADO'
    END AS owner_ok,
    CASE 
        WHEN definition LIKE '%security_barrier%' THEN '✅'
        ELSE '❌ SEM BARRIER'
    END AS barrier_ok
FROM pg_views 
WHERE schemaname='public' AND viewname LIKE '%_tenant' 
ORDER BY viewname;
```

**Esperado**: Todas as linhas com `✅` em `owner_ok` e `✅` em `barrier_ok`.

---

### 5. Verificar Jobs do TimescaleDB

```sql
SELECT 
    job_id,
    application_name,
    hypertable_name,
    proc_name,
    schedule_interval,
    next_start
FROM timescaledb_information.jobs 
WHERE hypertable_name LIKE 'ts_measure%' 
ORDER BY hypertable_name, proc_name;
```

**Esperado**: 9 jobs (3 CAGGs × 3 policies):

| hypertable_name | proc_name                        | schedule_interval |
|-----------------|----------------------------------|-------------------|
| ts_measure_1h   | policy_compression               | (varia)           |
| ts_measure_1h   | policy_refresh_continuous_aggregate | 01:00:00       |
| ts_measure_1h   | policy_retention                 | (varia)           |
| ts_measure_1m   | policy_compression               | (varia)           |
| ts_measure_1m   | policy_refresh_continuous_aggregate | 00:01:00       |
| ts_measure_1m   | policy_retention                 | (varia)           |
| ts_measure_5m   | policy_compression               | (varia)           |
| ts_measure_5m   | policy_refresh_continuous_aggregate | 00:05:00       |
| ts_measure_5m   | policy_retention                 | (varia)           |

---

### 6. Verificar Compressão Habilitada

```sql
SELECT 
    viewname,
    CASE 
        WHEN reloptions::text LIKE '%compress=true%' THEN '✅ Comprimido'
        ELSE '❌ NÃO comprimido'
    END AS compression_status
FROM pg_matviews 
WHERE schemaname='public' AND viewname LIKE 'ts_measure_%' 
ORDER BY viewname;
```

**Esperado**: Todos os CAGGs com `✅ Comprimido`.

---

### 7. Verificar GRANTs (app_user NÃO acessa bases)

```sql
-- Tentar acessar base diretamente como app_user
SET ROLE app_user;
SELECT COUNT(*) FROM ts_measure;  -- deve FALHAR
```

**Esperado**:
```
ERROR:  permission denied for table ts_measure
```

```sql
-- Tentar acessar CAGG diretamente como app_user
SELECT COUNT(*) FROM ts_measure_1m;  -- deve FALHAR
```

**Esperado**:
```
ERROR:  permission denied for table ts_measure_1m
```

```sql
-- Resetar role
RESET ROLE;
```

---

### 8. Verificar GRANTs (app_user ACESSA VIEWs)

```sql
SET ROLE app_user;

-- Configurar GUC (simular middleware)
SET app.tenant_id = '00000000-0000-0000-0000-000000000001';

-- Deve funcionar (mesmo se retornar 0 linhas por falta de dados)
SELECT COUNT(*) FROM ts_measure_tenant;
SELECT COUNT(*) FROM ts_measure_1m_tenant;
SELECT COUNT(*) FROM ts_measure_5m_tenant;
SELECT COUNT(*) FROM ts_measure_1h_tenant;

RESET ROLE;
```

**Esperado**: Nenhum erro, mesmo que retorne `0` (normal se não houver dados ainda).

---

### 9. Verificar RLS Desabilitado

```sql
SELECT 
    schemaname,
    tablename,
    rowsecurity,
    CASE 
        WHEN rowsecurity = false THEN '✅ RLS OFF'
        ELSE '❌ RLS ATIVO!'
    END AS rls_status
FROM pg_tables 
WHERE schemaname='public' AND tablename = 'ts_measure';
```

**Esperado**:
```
 schemaname | tablename  | rowsecurity | rls_status  
------------+------------+-------------+-------------
 public     | ts_measure | f           | ✅ RLS OFF
```

---

### 10. Verificar Retention Policies

```sql
SELECT 
    hypertable_name,
    proc_name,
    config::jsonb->>'drop_after' AS retention_interval
FROM timescaledb_information.jobs 
WHERE proc_name = 'policy_retention'
ORDER BY hypertable_name;
```

**Esperado**:

| hypertable_name | retention_interval |
|-----------------|-------------------|
| ts_measure      | 14 days           |
| ts_measure_1h   | 1825 days         |
| ts_measure_1m   | 365 days          |
| ts_measure_5m   | 730 days          |

---

### 11. Testar Isolamento com Dados Reais

```sql
-- Inserir dados de teste para 2 tenants
INSERT INTO ts_measure (tenant_id, device_id, point_id, ts, v_num)
VALUES 
    ('11111111-1111-1111-1111-111111111111', '22222222-2222-2222-2222-222222222222', '33333333-3333-3333-3333-333333333333', NOW(), 42.5),
    ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'cccccccc-cccc-cccc-cccc-cccccccccccc', NOW(), 99.9);

-- Testar isolamento via VIEW
SET app.tenant_id = '11111111-1111-1111-1111-111111111111';
SELECT v_num FROM ts_measure_tenant;  -- deve retornar 42.5

SET app.tenant_id = 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa';
SELECT v_num FROM ts_measure_tenant;  -- deve retornar 99.9

-- Limpar dados de teste
RESET app.tenant_id;
DELETE FROM ts_measure WHERE v_num IN (42.5, 99.9);
```

**Esperado**: Cada `SET app.tenant_id` retorna apenas os dados do respectivo tenant.

---

## 🚨 Troubleshooting

### Problema: "relation ts_measure_1m does not exist"

**Causa**: Migration 0006 não foi aplicada.

**Solução**:
```bash
python manage.py migrate timeseries 0006_cagg_1m_create
```

---

### Problema: "permission denied for table ts_measure"

**Causa**: Tentativa de acesso direto com app_user (esperado!).

**Solução**: Usar VIEWs `*_tenant` ao invés das bases:
```python
# ❌ ERRADO
connection.cursor().execute("SELECT * FROM ts_measure")

# ✅ CORRETO
connection.cursor().execute("SELECT * FROM ts_measure_tenant")
```

---

### Problema: VIEW retorna 0 linhas sempre

**Causa**: GUC `app.tenant_id` não configurado.

**Verificação**:
```sql
SHOW app.tenant_id;  -- se vazio, middleware não está ativo
```

**Solução**: Configurar middleware:
```python
# settings.py
MIDDLEWARE = [
    ...
    'apps.core.middleware.TenantIsolationMiddleware',  # ADICIONAR
    ...
]
```

---

### Problema: Jobs não estão rodando

**Verificação**:
```sql
SELECT * FROM timescaledb_information.job_stats 
WHERE hypertable_name = 'ts_measure_1m';
```

**Solução**: Forçar execução manual:
```sql
CALL run_job(1009);  -- substituir por job_id correto
```

---

## 📊 Validação de Performance (Opcional)

### Teste 1: Query de 30 dias raw vs CAGG

```sql
-- Raw (esperado: ~2.6M linhas, ~5s)
EXPLAIN ANALYZE
SELECT ts, v_num FROM ts_measure 
WHERE ts >= NOW() - INTERVAL '30 days';

-- CAGG 1m (esperado: ~43k linhas, ~300ms)
EXPLAIN ANALYZE
SELECT bucket AS ts, v_avg FROM ts_measure_1m 
WHERE bucket >= NOW() - INTERVAL '30 days';

-- CAGG 1h (esperado: ~720 linhas, ~100ms)
EXPLAIN ANALYZE
SELECT bucket AS ts, v_avg FROM ts_measure_1h 
WHERE bucket >= NOW() - INTERVAL '30 days';
```

**Esperado**: Redução drástica no tempo de execução (1h >> 1m >> raw).

---

### Teste 2: Verificar Compressão Aplicada

```sql
SELECT 
    hypertable_name,
    compression_status,
    uncompressed_heap_size,
    compressed_heap_size,
    ROUND(100 - (compressed_heap_size::float / uncompressed_heap_size * 100), 2) AS compression_ratio_percent
FROM timescaledb_information.compressed_hypertable_stats 
WHERE hypertable_name LIKE 'ts_measure%';
```

**Esperado**: compression_ratio_percent > 80% (compressão ~10x).

---

## ✅ Critérios de Aceitação

- [ ] 3 CAGGs criados (1m, 5m, 1h)
- [ ] 4 VIEWs tenant-scoped criadas
- [ ] 9 jobs ativos (3 refresh, 3 compression, 3 retention)
- [ ] app_user NÃO acessa bases diretamente
- [ ] app_user acessa VIEWs sem erro
- [ ] RLS desabilitado em ts_measure
- [ ] security_barrier ativo nas VIEWs
- [ ] Teste de isolamento passa (2 tenants, dados não vazam)

---

**Última atualização**: 2025-10-08  
**Status**: ✅ VALIDADO
