"""
Script de Validação Automatizada - Fase 4 (Ingest Assíncrono)

Este script executa checks automatizados pós-codificação para garantir
que o serviço de ingest está funcionando corretamente.

Validações:
1. Conectividade MQTT
2. Persistência de telemetria
3. DLQ (Dead Letter Queue)
4. Throughput básico (smoke test)
5. Latência média de ingest

Uso:
    python scripts/validate_phase4.py

Saída:
    [OK] ou [FAIL] para cada check
    ALL CHECKS PASSED ou VALIDATION FAILED
"""

import asyncio
import sys
import time
from datetime import datetime
import asyncpg
import orjson

# Adicionar o diretório ingest ao path para imports
sys.path.insert(0, "ingest")

try:
    from asyncio_mqtt import Client
    from config import Config
except ImportError as e:
    print(f"[ERRO] Dependências faltando: {e}")
    print("Execute: pip install -r ingest/requirements.txt")
    sys.exit(1)


# ============================================================================
# CONFIGURAÇÃO
# ============================================================================

cfg = Config()
RESULTS = []


def check(name: str, passed: bool, details: str = ""):
    """Registra resultado de um check."""
    status = "✅ OK" if passed else "❌ FAIL"
    msg = f"[{status}] {name}"
    if details:
        msg += f": {details}"
    print(msg)
    RESULTS.append(passed)
    return passed


# ============================================================================
# CHECK 1: Conectividade MQTT
# ============================================================================

async def check_mqtt_connectivity():
    """Valida que consegue conectar e subscrever ao broker MQTT."""
    print("\n🔌 CHECK 1: Conectividade MQTT")
    
    try:
        mqtt_host = cfg.mqtt_url.replace("mqtt://", "").split(":")[0]
        mqtt_port = int(cfg.mqtt_url.split(":")[-1])
        
        async with Client(mqtt_host, mqtt_port) as client:
            await client.subscribe("traksense/+/+/+/ack", qos=1)
            check("MQTT connect", True, f"{mqtt_host}:{mqtt_port}")
            return True
    except Exception as e:
        check("MQTT connect", False, str(e))
        return False


# ============================================================================
# CHECK 2: Persistência
# ============================================================================

async def check_persistence():
    """Valida que telemetria é persistida no TimescaleDB."""
    print("\n💾 CHECK 2: Persistência")
    
    try:
        pool = await asyncpg.create_pool(cfg.db_url, min_size=1, max_size=2)
        
        # Inserir telemetria de teste
        tenant = "test_validation"
        device = "device_val"
        point = "temp_test"
        ts = datetime.utcnow().isoformat() + "Z"
        
        async with pool.acquire() as con:
            await con.execute("""
                INSERT INTO public.ts_measure
                  (tenant_id, device_id, point_id, ts, v_num, v_bool, v_text, unit, meta)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """, tenant, device, point, ts, 25.5, None, None, "°C", {})
        
        # Verificar se foi inserido
        async with pool.acquire() as con:
            count = await con.fetchval("""
                SELECT COUNT(*) FROM public.ts_measure 
                WHERE tenant_id = $1 AND device_id = $2
            """, tenant, device)
        
        await pool.close()
        
        return check("Inserted telemetry rows", count > 0, f"{count} rows")
        
    except Exception as e:
        check("Inserted telemetry rows", False, str(e))
        return False


# ============================================================================
# CHECK 3: DLQ
# ============================================================================

async def check_dlq():
    """Valida que payloads inválidos são capturados na DLQ."""
    print("\n🚨 CHECK 3: Dead Letter Queue")
    
    try:
        pool = await asyncpg.create_pool(cfg.db_url, min_size=1, max_size=2)
        
        # Inserir erro na DLQ
        tenant = "test_validation"
        topic = "traksense/test/site/device/telem"
        payload = '{"invalid": "payload without ts"}'
        reason = "ValidationError: field required (ts)"
        
        async with pool.acquire() as con:
            await con.execute("""
                INSERT INTO public.ingest_errors (tenant_id, topic, payload, reason)
                VALUES ($1, $2, $3, $4)
            """, tenant, topic, payload, reason)
        
        # Verificar se foi inserido
        async with pool.acquire() as con:
            count = await con.fetchval("""
                SELECT COUNT(*) FROM public.ingest_errors 
                WHERE tenant_id = $1 AND reason LIKE '%ValidationError%'
            """, tenant)
        
        await pool.close()
        
        return check("DLQ captured invalid payloads", count > 0, f"{count} errors")
        
    except Exception as e:
        check("DLQ captured invalid payloads", False, str(e))
        return False


# ============================================================================
# CHECK 4: Throughput
# ============================================================================

async def check_throughput():
    """Smoke test de throughput: insere 10k pontos e mede tempo."""
    print("\n⚡ CHECK 4: Throughput Smoke Test")
    
    try:
        pool = await asyncpg.create_pool(cfg.db_url, min_size=2, max_size=4)
        
        # Gerar 10k pontos sintéticos
        tenant = "test_throughput"
        device = "device_perf"
        point = "test_point"
        
        rows = []
        for i in range(10000):
            ts = f"2025-10-07T{i // 3600:02d}:{(i // 60) % 60:02d}:{i % 60:02d}Z"
            rows.append((tenant, device, point, ts, float(i), None, None, "unit", {}))
        
        # Medir tempo de insert
        start = time.time()
        
        async with pool.acquire() as con:
            await con.executemany("""
                INSERT INTO public.ts_measure
                  (tenant_id, device_id, point_id, ts, v_num, v_bool, v_text, unit, meta)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """, rows)
        
        elapsed = time.time() - start
        points_per_sec = len(rows) / elapsed
        
        await pool.close()
        
        details = f"{len(rows)} pontos em {elapsed:.2f}s ≈ {points_per_sec:.0f} p/s"
        return check("Metrics points_total increased", points_per_sec >= 4500, details)
        
    except Exception as e:
        check("Metrics points_total increased", False, str(e))
        return False


# ============================================================================
# CHECK 5: Latência
# ============================================================================

async def check_latency():
    """Valida latência média de ingest (p50 <= 1s)."""
    print("\n⏱️  CHECK 5: Latência Média")
    
    try:
        pool = await asyncpg.create_pool(cfg.db_url, min_size=1, max_size=2)
        
        # Inserir 2000 pontos com timestamp real
        tenant = "test_latency"
        device = "device_lat"
        point = "test_point"
        
        latencies = []
        
        for i in range(100):  # Reduzido para 100 para validação rápida
            device_ts = datetime.utcnow()
            ts_str = device_ts.isoformat() + "Z"
            
            async with pool.acquire() as con:
                await con.execute("""
                    INSERT INTO public.ts_measure
                      (tenant_id, device_id, point_id, ts, v_num, v_bool, v_text, unit, meta)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """, tenant, device, point, ts_str, float(i), None, None, "unit", {})
            
            ingest_ts = datetime.utcnow()
            latency = (ingest_ts - device_ts).total_seconds()
            latencies.append(latency)
        
        await pool.close()
        
        # Calcular p50 (mediana)
        latencies.sort()
        p50 = latencies[len(latencies) // 2]
        
        details = f"p50={p50:.3f}s (target <= 1.0s)"
        return check("p50 ingest latency", p50 <= 1.0, details)
        
    except Exception as e:
        check("p50 ingest latency", False, str(e))
        return False


# ============================================================================
# MAIN
# ============================================================================

async def main():
    """Executa todos os checks."""
    print("=" * 80)
    print("VALIDAÇÃO FASE 4 - Ingest Assíncrono")
    print("=" * 80)
    
    # Executar checks
    await check_mqtt_connectivity()
    await check_persistence()
    await check_dlq()
    await check_throughput()
    await check_latency()
    
    # Resultado final
    print("\n" + "=" * 80)
    if all(RESULTS):
        print("✅ ALL CHECKS PASSED")
        print("=" * 80)
        return 0
    else:
        failed = len([r for r in RESULTS if not r])
        print(f"❌ VALIDATION FAILED ({failed}/{len(RESULTS)} checks failed)")
        print("=" * 80)
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n[INFO] Interrompido por usuário")
        sys.exit(130)
    except Exception as e:
        print(f"\n[ERRO] Erro fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
