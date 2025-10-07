"""
Database utilities for timeseries operations.
Helper functions for ingest service and views.
"""
from django.db import connection
import logging

logger = logging.getLogger(__name__)


def set_tenant_guc_for_conn(tenant_id: str):
    """
    Set PostgreSQL GUC (app.tenant_id) for RLS.
    
    Use this in ingest service before inserting telemetry data.
    
    Args:
        tenant_id: UUID string of the tenant
        
    Example:
        >>> from timeseries.dbutils import set_tenant_guc_for_conn
        >>> set_tenant_guc_for_conn("550e8400-e29b-41d4-a716-446655440000")
        >>> # Now all queries will be filtered by this tenant
    """
    with connection.cursor() as cur:
        cur.execute("SET app.tenant_id = %s", [tenant_id])
        logger.debug(f"GUC app.tenant_id set to {tenant_id}")


def get_current_tenant_id() -> str:
    """
    Get current tenant_id from GUC.
    
    Returns:
        Tenant ID string or None if not set
    """
    with connection.cursor() as cur:
        cur.execute("SELECT current_setting('app.tenant_id', TRUE)")
        result = cur.fetchone()
        return result[0] if result else None


def verify_rls_enabled() -> bool:
    """
    Verify that RLS is enabled on ts_measure table.
    
    Returns:
        True if RLS is enabled, False otherwise
    """
    with connection.cursor() as cur:
        cur.execute("""
            SELECT relrowsecurity 
            FROM pg_class 
            WHERE oid = 'public.ts_measure'::regclass
        """)
        result = cur.fetchone()
        return result[0] if result else False


def get_aggregate_view_name(agg: str) -> str:
    """
    Get the appropriate materialized view name for aggregation level.
    
    Args:
        agg: Aggregation level ('raw', '1m', '5m', '1h')
        
    Returns:
        View name or 'public.ts_measure' for raw data
        
    Raises:
        ValueError: If aggregation level is invalid
    """
    if agg == 'raw':
        return 'public.ts_measure'
    elif agg in ('1m', '5m', '1h'):
        return f'public.ts_measure_{agg}'
    else:
        raise ValueError(f"Invalid aggregation level: {agg}. Use: raw, 1m, 5m, 1h")
