"""
Timeseries API views.
Provides endpoints for querying telemetry data with aggregations.
"""
import logging
from django.db import connection
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .dbutils import get_aggregate_view_name, get_current_tenant_id

logger = logging.getLogger(__name__)


@api_view(["GET"])
def data_points(request):
    """
    Query telemetry data with optional aggregations.
    
    Query Parameters:
        - device_id (required): UUID of the device
        - point_id (required): UUID of the point
        - from (required): Start timestamp (ISO 8601)
        - to (required): End timestamp (ISO 8601)
        - agg (optional): Aggregation level (raw|1m|5m|1h). Default: 1m
        
    Returns:
        JSON response with rows array containing:
        - For aggregated data: ts, v_avg, v_min, v_max, v_count
        - For raw data: ts, v_avg (which is actually v_num)
        
    Performance:
        - Uses continuous aggregates (materialized views) for 1m/5m/1h
        - Raw data is limited to 100k rows to prevent timeout
        - RLS is automatically enforced via middleware GUC
        
    Example:
        GET /data/points?device_id=xxx&point_id=yyy&from=2025-10-06T00:00:00Z&to=2025-10-07T00:00:00Z&agg=1m
    """
    # Validate required parameters
    device_id = request.GET.get("device_id")
    point_id = request.GET.get("point_id")
    ts_from = request.GET.get("from")
    ts_to = request.GET.get("to")
    agg = request.GET.get("agg", "1m")
    
    if not all([device_id, point_id, ts_from, ts_to]):
        return Response(
            {"error": "Missing required parameters: device_id, point_id, from, to"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate aggregation level
    try:
        view_name = get_aggregate_view_name(agg)
    except ValueError as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Log current tenant (for debugging)
    tenant_id = get_current_tenant_id()
    logger.info(
        f"data_points query: tenant={tenant_id}, device={device_id}, "
        f"point={point_id}, agg={agg}, from={ts_from}, to={ts_to}"
    )
    
    # Build query based on aggregation level
    if agg in ("1m", "5m", "1h"):
        # Use continuous aggregate (materialized view)
        sql = f"""
            SELECT tb AS ts, v_avg, v_min, v_max, v_count
            FROM {view_name}
            WHERE device_id = %s AND point_id = %s
              AND tb >= %s AND tb < %s
            ORDER BY tb ASC
        """
        params = [device_id, point_id, ts_from, ts_to]
        columns = ["ts", "v_avg", "v_min", "v_max", "v_count"]
    else:
        # Raw data with limit to prevent timeout
        sql = """
            SELECT ts, v_num AS v_avg, v_bool, v_text, unit, qual
            FROM public.ts_measure
            WHERE device_id = %s AND point_id = %s
              AND ts >= %s AND ts < %s
            ORDER BY ts ASC
            LIMIT 100000
        """
        params = [device_id, point_id, ts_from, ts_to]
        columns = ["ts", "v_avg", "v_bool", "v_text", "unit", "qual"]
    
    # Execute query
    try:
        with connection.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
            
        # Convert to list of dicts
        result = [
            dict(zip(columns, row))
            for row in rows
        ]
        
        logger.info(f"data_points result: {len(result)} rows returned")
        
        return Response({
            "agg": agg,
            "count": len(result),
            "rows": result
        })
        
    except Exception as e:
        logger.error(f"data_points error: {e}", exc_info=True)
        return Response(
            {"error": "Database query failed", "detail": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
def health_ts(request):
    """
    Health check for timeseries service.
    Verifies RLS is enabled and continuous aggregates exist.
    """
    from .dbutils import verify_rls_enabled
    
    try:
        # Check RLS
        rls_enabled = verify_rls_enabled()
        
        # Check if continuous aggregates exist
        with connection.cursor() as cur:
            cur.execute("""
                SELECT count(*) 
                FROM pg_matviews 
                WHERE schemaname = 'public' 
                AND matviewname LIKE 'ts_measure_%'
            """)
            agg_count = cur.fetchone()[0]
        
        return Response({
            "status": "ok",
            "rls_enabled": rls_enabled,
            "continuous_aggregates": agg_count,
            "tenant_id": get_current_tenant_id()
        })
        
    except Exception as e:
        logger.error(f"health_ts error: {e}", exc_info=True)
        return Response(
            {"status": "error", "detail": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
