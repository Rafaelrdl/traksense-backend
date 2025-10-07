"""
Timeseries DB Utilities - Helpers para queries e RLS

Este módulo fornece funções utilitárias para operações de telemetria.

Funções:
-------
1. set_tenant_guc_for_conn(tenant_id):
   - Configura app.tenant_id GUC (Grand Unified Configuration)
   - Usado por ingest service antes de inserir dados
   - Habilita RLS (Row Level Security) para isolamento de tenant

2. get_current_tenant_id():
   - Retorna tenant_id atual do GUC
   - Útil para debug/auditoria

3. verify_rls_enabled():
   - Verifica se RLS está habilitado em ts_measure
   - Usado em checks de inicialização

4. get_aggregate_view_name(agg):
   - Retorna nome da view de agregação (1m/5m/1h)
   - Usado em queries de dados agregados

RLS (Row Level Security):
-------------------------
PostgreSQL RLS filtra linhas automaticamente com base em policies:

CREATE POLICY ts_tenant_isolation ON public.ts_measure
USING (tenant_id = current_setting('app.tenant_id')::uuid);

Fluxo:
1. Middleware: SET LOCAL app.tenant_id = '<tenant_pk>'
2. Query: SELECT * FROM public.ts_measure WHERE device_id = '...'
3. RLS aplica filtro automático: AND tenant_id = current_setting('app.tenant_id')::uuid
4. Resultado: apenas dados do tenant atual

Benefícios:
- Isolamento garantido no DB (não depende de código)
- Impossível vazar dados de outros tenants (mesmo com bug em views)
- Performance: índice em (tenant_id, device_id, point_id, ts DESC)

GUC (Grand Unified Configuration):
----------------------------------
Custom settings do PostgreSQL (nível de sessão/transação):

SET app.tenant_id = '550e8400-e29b-41d4-a716-446655440000';
SET LOCAL app.tenant_id = '...';  -- válido apenas na transação atual

Namespaces:
- Sem ponto (ex: timezone): built-in PostgreSQL
- Com ponto (ex: app.tenant_id): custom (qualquer nome)

Scope:
- SET: válido até fim da conexão (perigoso em connection pooling!)
- SET LOCAL: válido até fim da transação (seguro, recomendado)

Uso:
---
# Em views (via middleware - automático)
# GUC já está setado por TenantGucMiddleware

# Em ingest service (asyncpg)
async with pool.acquire() as conn:
    await conn.execute("SET app.tenant_id = $1", tenant_id)
    await conn.executemany(
        "INSERT INTO public.ts_measure(...) VALUES (...)",
        rows
    )

# Em management commands
from timeseries.dbutils import set_tenant_guc_for_conn
set_tenant_guc_for_conn(tenant_id)
# Agora queries respeitam RLS

Autor: TrakSense Team
Data: 2025-10-07
"""
from django.db import connection
import logging

logger = logging.getLogger(__name__)


def set_tenant_guc_for_conn(tenant_id: str):
    """
    Configura PostgreSQL GUC (app.tenant_id) para Row Level Security.
    
    Esta função deve ser chamada antes de queries de telemetria em contextos
    onde o middleware não está disponível (management commands, ingest service).
    
    GUC (Grand Unified Configuration):
    - Custom setting do PostgreSQL (namespace: app.*)
    - Usado por RLS policy para filtrar dados por tenant
    - Escopo: SET (sessão) ou SET LOCAL (transação)
    
    Args:
        tenant_id: UUID string do tenant (ex: "550e8400-e29b-41d4-a716-446655440000")
        
    Raises:
        DatabaseError: Se query falhar (conexão perdida, etc.)
        
    Example:
        >>> from timeseries.dbutils import set_tenant_guc_for_conn
        >>> 
        >>> # Em management command
        >>> tenant_id = "550e8400-e29b-41d4-a716-446655440000"
        >>> set_tenant_guc_for_conn(tenant_id)
        >>> 
        >>> # Agora queries respeitam RLS
        >>> with connection.cursor() as cur:
        >>>     cur.execute("SELECT COUNT(*) FROM public.ts_measure")
        >>>     count = cur.fetchone()[0]  # Apenas dados do tenant atual
        
    Notas:
    -----
    - Usa SET (não SET LOCAL) pois connection.cursor() não está em transação
    - Em prod: usar connection pooling com reset de GUC entre requests
    - Ingest service: usar SET LOCAL em cada transação (asyncpg)
    """
    with connection.cursor() as cur:
        # SET app.tenant_id (válido até fim da conexão)
        # Alternativa: SET LOCAL (válido apenas na transação)
        cur.execute("SET app.tenant_id = %s", [tenant_id])
        logger.debug(f"GUC app.tenant_id configurado: {tenant_id}")


def get_current_tenant_id() -> str:
    """
    Obtém tenant_id atual do GUC.
    
    Útil para:
    - Debug: verificar se GUC foi configurado corretamente
    - Auditoria: logar queries com tenant_id
    - Validação: garantir que middleware setou GUC
    
    Returns:
        Tenant ID string (UUID) ou None se GUC não foi configurado
        
    Example:
        >>> from timeseries.dbutils import get_current_tenant_id
        >>> 
        >>> tenant_id = get_current_tenant_id()
        >>> if tenant_id:
        >>>     print(f"Queries filtradas por tenant: {tenant_id}")
        >>> else:
        >>>     print("⚠️ GUC não configurado! Queries podem vazar dados!")
        
    Notas:
    -----
    - current_setting(..., TRUE): retorna NULL se GUC não existe (não lança erro)
    - Se retornar None: RLS bloqueará TODOS os acessos (SELECT retorna 0 linhas)
    """
    with connection.cursor() as cur:
        # current_setting com missing_ok=TRUE (não lança erro se GUC não existe)
        cur.execute("SELECT current_setting('app.tenant_id', TRUE)")
        result = cur.fetchone()
        tenant_id = result[0] if result and result[0] else None
        
        if not tenant_id:
            logger.warning("GUC app.tenant_id NÃO configurado! RLS bloqueará queries.")
        
        return tenant_id


def verify_rls_enabled() -> bool:
    """
    Verifica se Row Level Security está habilitado em ts_measure.
    
    Útil para:
    - Checks de inicialização (AppConfig.ready())
    - Testes de integração
    - Validação pós-migration
    
    Returns:
        True se RLS está habilitado, False caso contrário
        
    Raises:
        DatabaseError: Se tabela ts_measure não existe
        
    Example:
        >>> from timeseries.dbutils import verify_rls_enabled
        >>> 
        >>> if not verify_rls_enabled():
        >>>     print("⚠️ RLS desabilitado! Execute migrations.")
        >>> else:
        >>>     print("✓ RLS habilitado. Dados isolados por tenant.")
        
    SQL:
    ---
    SELECT relrowsecurity FROM pg_class WHERE oid = 'public.ts_measure'::regclass;
    
    - relrowsecurity: bool, True se RLS habilitado
    - pg_class: catálogo do PostgreSQL com metadados de tabelas
    - regclass: cast para obter OID da tabela
    
    Notas:
    -----
    - Se tabela não existe: lança DatabaseError
    - Se RLS desabilitado: retorna False (CRÍTICO!)
    - Migration 0001_ts_schema.py habilita RLS automaticamente
    """
    with connection.cursor() as cur:
        cur.execute("""
            SELECT relrowsecurity 
            FROM pg_class 
            WHERE oid = 'public.ts_measure'::regclass
        """)
        result = cur.fetchone()
        
        rls_enabled = result[0] if result else False
        
        if not rls_enabled:
            logger.error("⚠️ RLS DESABILITADO em ts_measure! Risco de vazamento de dados!")
        else:
            logger.debug("✓ RLS habilitado em ts_measure")
        
        return rls_enabled


def get_aggregate_view_name(agg: str) -> str:
    """
    Retorna nome da view de agregação para o nível solicitado.
    
    TimescaleDB continuous aggregates (materialized views):
    - ts_measure_1m: média/min/max por minuto (time_bucket 1 min)
    - ts_measure_5m: média/min/max por 5 minutos (time_bucket 5 min)
    - ts_measure_1h: média/min/max por hora (time_bucket 1 hour)
    
    Uso:
    ---
    Views de agregação são mais eficientes para queries longas:
    - raw: milhões de linhas (lento)
    - 1m: ~1.440 linhas/dia (24h × 60min)
    - 1h: ~24 linhas/dia
    
    Args:
        agg: Nível de agregação ('raw', '1m', '5m', '1h')
        
    Returns:
        Nome da view/tabela:
        - 'raw' → 'public.ts_measure'
        - '1m' → 'public.ts_measure_1m'
        - '5m' → 'public.ts_measure_5m'
        - '1h' → 'public.ts_measure_1h'
        
    Raises:
        ValueError: Se nível de agregação inválido
        
    Example:
        >>> from timeseries.dbutils import get_aggregate_view_name
        >>> 
        >>> # Query de 30 dias
        >>> view = get_aggregate_view_name('1h')  # ts_measure_1h
        >>> sql = f"SELECT tb, v_avg FROM {view} WHERE ..."
        >>> 
        >>> # Query de 1 hora (tempo real)
        >>> view = get_aggregate_view_name('raw')  # ts_measure
        >>> sql = f"SELECT ts, v_num FROM {view} WHERE ..."
        
    Performance:
    -----------
    - raw: ~10 leituras/segundo (alta latência)
    - 1m: ~1.000 leituras/segundo (média latência)
    - 1h: ~10.000 leituras/segundo (baixa latência)
    
    Notas:
    -----
    - Views são atualizadas automaticamente (refresh policies)
    - Refresh interval: 1 minuto (configurável em migration)
    - RLS também se aplica a views (tenant_id filtrado)
    """
    # Validar nível de agregação
    valid_aggs = ['raw', '1m', '5m', '1h']
    
    if agg not in valid_aggs:
        raise ValueError(
            f"Nível de agregação inválido: '{agg}'. "
            f"Use: {', '.join(valid_aggs)}"
        )
    
    # Retornar nome da view
    if agg == 'raw':
        return 'public.ts_measure'
    else:
        return f'public.ts_measure_{agg}'
