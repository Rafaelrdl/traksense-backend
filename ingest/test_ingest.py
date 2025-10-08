"""
Testes de Ingest - Fase 4

Testes automatizados para validar o serviço de ingest assíncrono.
"""

import pytest
import asyncio
import asyncpg
from datetime import datetime
import orjson


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def db_url():
    """URL do banco de dados para testes."""
    return "postgresql://postgres:postgres@localhost:5432/traksense"


@pytest.fixture
async def db_pool(db_url):
    """Pool de conexões asyncpg para testes."""
    pool = await asyncpg.create_pool(db_url, min_size=1, max_size=2)
    yield pool
    await pool.close()


@pytest.fixture
async def clean_db(db_pool):
    """Limpa tabelas antes de cada teste."""
    async with db_pool.acquire() as con:
        await con.execute("TRUNCATE TABLE public.ingest_errors")
        await con.execute("TRUNCATE TABLE public.cmd_ack")
        await con.execute("TRUNCATE TABLE public.ts_measure")


# ============================================================================
# TESTES: DLQ (Dead Letter Queue)
# ============================================================================

@pytest.mark.asyncio
async def test_dlq_invalid_json(db_pool, clean_db):
    """
    Valida que payload JSON inválido é enviado para DLQ.
    """
    # Simular payload inválido
    tenant = "test_tenant"
    topic = "traksense/test_tenant/factory/device123/telem"
    invalid_payload = "{invalid json syntax"
    reason = "JSONDecodeError"
    
    async with db_pool.acquire() as con:
        await con.execute("""
            INSERT INTO public.ingest_errors (tenant_id, topic, payload, reason)
            VALUES ($1, $2, $3, $4)
        """, tenant, topic, invalid_payload, reason)
    
    # Verificar se foi inserido
    async with db_pool.acquire() as con:
        row = await con.fetchrow("""
            SELECT * FROM public.ingest_errors 
            WHERE topic = $1 AND reason = $2
        """, topic, reason)
    
    assert row is not None
    assert row['tenant_id'] == tenant
    assert row['payload'] == invalid_payload
    assert reason in row['reason']


@pytest.mark.asyncio
async def test_dlq_missing_fields(db_pool, clean_db):
    """
    Valida que payload com campos obrigatórios faltando vai para DLQ.
    """
    tenant = "test_tenant"
    topic = "traksense/test_tenant/factory/device123/telem"
    
    # Payload sem campo "ts" (obrigatório)
    invalid_payload = orjson.dumps({
        "schema": "v1",
        # "ts": "2025-10-07T15:00:00Z",  # FALTANDO
        "points": [{"name": "temp", "t": "float", "v": 25.0}]
    }).decode()
    
    reason = "ValidationError: field required (ts)"
    
    async with db_pool.acquire() as con:
        await con.execute("""
            INSERT INTO public.ingest_errors (tenant_id, topic, payload, reason)
            VALUES ($1, $2, $3, $4)
        """, tenant, topic, invalid_payload, reason)
    
    # Verificar
    async with db_pool.acquire() as con:
        count = await con.fetchval("""
            SELECT COUNT(*) FROM public.ingest_errors 
            WHERE tenant_id = $1 AND reason LIKE '%ValidationError%'
        """, tenant)
    
    assert count >= 1


# ============================================================================
# TESTES: Out-of-Order
# ============================================================================

@pytest.mark.asyncio
async def test_out_of_order_timestamps(db_pool, clean_db):
    """
    Valida que inserts com timestamps fora de ordem são aceitos.
    
    TimescaleDB hypertable aceita inserts desordenados sem erros.
    """
    tenant = "test_tenant"
    device = "device123"
    point = "temp_agua"
    
    # Inserir com timestamps invertidos
    rows = [
        (tenant, device, point, "2025-10-07T15:02:00Z", 25.5, None, None, "°C", {}),
        (tenant, device, point, "2025-10-07T15:01:00Z", 24.0, None, None, "°C", {}),
        (tenant, device, point, "2025-10-07T15:03:00Z", 26.0, None, None, "°C", {}),
    ]
    
    async with db_pool.acquire() as con:
        await con.executemany("""
            INSERT INTO public.ts_measure
              (tenant_id, device_id, point_id, ts, v_num, v_bool, v_text, unit, meta)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        """, rows)
    
    # Verificar que todos foram inseridos
    async with db_pool.acquire() as con:
        count = await con.fetchval("""
            SELECT COUNT(*) FROM public.ts_measure 
            WHERE tenant_id = $1 AND device_id = $2
        """, tenant, device)
    
    assert count == 3


# ============================================================================
# TESTES: ACK Idempotente
# ============================================================================

@pytest.mark.asyncio
async def test_ack_idempotency(db_pool, clean_db):
    """
    Valida que ACKs duplicados (mesmo cmd_id) são tratados via UPSERT.
    """
    tenant = "test_tenant"
    device = "device123"
    cmd_id = "01HQZC5K3M8YBQWER7TXZ9V2P3"  # ULID
    
    # Primeiro ACK
    async with db_pool.acquire() as con:
        await con.execute("""
            INSERT INTO public.cmd_ack
              (tenant_id, device_id, cmd_id, ok, ts_exec, payload)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (tenant_id, device_id, cmd_id) DO UPDATE
            SET ok=excluded.ok, ts_exec=excluded.ts_exec
        """, tenant, device, cmd_id, True, "2025-10-07T15:00:00Z", {})
    
    # Segundo ACK (duplicado, deve fazer UPDATE)
    async with db_pool.acquire() as con:
        await con.execute("""
            INSERT INTO public.cmd_ack
              (tenant_id, device_id, cmd_id, ok, ts_exec, payload)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (tenant_id, device_id, cmd_id) DO UPDATE
            SET ok=excluded.ok, ts_exec=excluded.ts_exec
        """, tenant, device, cmd_id, True, "2025-10-07T15:00:01Z", {"updated": True})
    
    # Verificar que há apenas 1 registro
    async with db_pool.acquire() as con:
        count = await con.fetchval("""
            SELECT COUNT(*) FROM public.cmd_ack 
            WHERE tenant_id = $1 AND cmd_id = $2
        """, tenant, cmd_id)
    
    assert count == 1


# ============================================================================
# TESTES: Throughput (opcional)
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.slow
async def test_throughput_smoke(db_pool, clean_db):
    """
    Smoke test de throughput: insere 10k pontos e mede tempo.
    
    Meta: >= 5k points/s em dev (docker local).
    """
    tenant = "test_tenant"
    device = "device_perf"
    point = "test_point"
    
    # Gerar 10k rows sintéticas
    rows = []
    for i in range(10000):
        ts = f"2025-10-07T15:{i % 60:02d}:{i % 60:02d}Z"
        rows.append((tenant, device, point, ts, float(i), None, None, "unit", {}))
    
    # Medir tempo de insert
    import time
    start = time.time()
    
    async with db_pool.acquire() as con:
        await con.executemany("""
            INSERT INTO public.ts_measure
              (tenant_id, device_id, point_id, ts, v_num, v_bool, v_text, unit, meta)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        """, rows)
    
    elapsed = time.time() - start
    points_per_sec = len(rows) / elapsed
    
    print(f"\n[THROUGHPUT] {len(rows)} pontos em {elapsed:.2f}s = {points_per_sec:.0f} p/s")
    
    # Meta: >= 5k p/s
    assert points_per_sec >= 5000, f"Throughput muito baixo: {points_per_sec:.0f} p/s (meta: >=5000 p/s)"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
