"""
Timeseries API Views - Endpoints para consulta de telemetria IoT

Este módulo fornece APIs REST para consulta de dados de time-series.

Endpoints:
---------
1. GET /data/points:
   - Consulta telemetria de um ponto específico
   - Suporta agregações (1m/5m/1h) via continuous aggregates
   - RLS automático via middleware (isolamento por tenant)

2. GET /health/timeseries:
   - Health check do sistema de telemetria
   - Verifica RLS, continuous aggregates, tenant_id

Arquitetura:
-----------
Views → Raw SQL → TimescaleDB (hypertable + continuous aggregates)
                                 ↓
                          RLS (tenant_id GUC)
                                 ↓
                        Apenas dados do tenant atual

Agregações (Continuous Aggregates):
----------------------------------
- raw: ts_measure (dados brutos, até 100k linhas)
- 1m: ts_measure_1m (média/min/max por minuto)
- 5m: ts_measure_5m (média/min/max por 5 minutos)
- 1h: ts_measure_1h (média/min/max por hora)

Performance:
-----------
Query de 30 dias:
- raw: ~43M linhas → timeout
- 1m: ~43k linhas → ~5s
- 1h: ~720 linhas → ~100ms ✓

RLS (Row Level Security):
-------------------------
TenantGucMiddleware seta app.tenant_id antes da view:
1. Middleware: SET LOCAL app.tenant_id = '<tenant_pk>'
2. View: SELECT * FROM public.ts_measure WHERE device_id = '...'
3. RLS aplica filtro: AND tenant_id = current_setting('app.tenant_id')::uuid
4. Resultado: apenas dados do tenant atual

Impossível vazar dados de outros tenants (garantido pelo PostgreSQL).

Autenticação:
------------
TODO (Fase 2):
- DRF authentication classes (SessionAuth, TokenAuth)
- Permissions: IsAuthenticated, TenantMemberPermission
- Rate limiting (throttling)

Autor: TrakSense Team
Data: 2025-10-07
"""
import logging
from django.db import connection
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .dbutils import get_aggregate_view_name, get_current_tenant_id

logger = logging.getLogger(__name__)


@api_view(["GET"])
def data_points(request):
    """
    Consulta telemetria de um ponto específico com agregações opcionais.
    
    Este endpoint é o CORE da plataforma TrakSense: consulta time-series
    de dispositivos IoT com isolamento automático por tenant (RLS).
    
    Query Parameters:
    ----------------
    - device_id (obrigatório): UUID do dispositivo
      Ex: "550e8400-e29b-41d4-a716-446655440000"
    
    - point_id (obrigatório): UUID do ponto de medição
      Ex: "660e8400-e29b-41d4-a716-446655440001"
    
    - from (obrigatório): Timestamp inicial (ISO 8601)
      Ex: "2025-10-06T00:00:00Z"
    
    - to (obrigatório): Timestamp final (ISO 8601)
      Ex: "2025-10-07T00:00:00Z"
    
    - agg (opcional): Nível de agregação. Default: "1m"
      Valores: "raw", "1m", "5m", "1h"
      
      raw: dados brutos (até 100k linhas, pode ser lento)
      1m: média/min/max por minuto (recomendado para 1-7 dias)
      5m: média/min/max por 5 minutos (recomendado para 7-30 dias)
      1h: média/min/max por hora (recomendado para 30-365 dias)
    
    Response (agregado):
    -------------------
    {
      "agg": "1m",
      "count": 1440,
      "rows": [
        {
          "ts": "2025-10-06T00:00:00Z",
          "v_avg": 23.5,
          "v_min": 22.1,
          "v_max": 25.3,
          "v_count": 60
        },
        ...
      ]
    }
    
    Response (raw):
    --------------
    {
      "agg": "raw",
      "count": 86400,
      "rows": [
        {
          "ts": "2025-10-06T00:00:00.123Z",
          "v_avg": 23.5,  // v_num renomeado para compatibilidade
          "v_bool": null,
          "v_text": null,
          "unit": "°C",
          "qual": 0
        },
        ...
      ]
    }
    
    Performance:
    -----------
    Query de 30 dias (1 ponto, 1 leitura/segundo):
    - raw: ~2.6M linhas → timeout (> 30s)
    - 1m: ~43k linhas → ~5s
    - 1h: ~720 linhas → ~100ms ✓
    
    Estratégia:
    - raw: apenas últimas horas (tempo real)
    - 1m: até 7 dias (dashboards)
    - 5m/1h: 30+ dias (relatórios históricos)
    
    RLS (Row Level Security):
    -------------------------
    TenantGucMiddleware seta app.tenant_id automaticamente.
    Todas as queries são filtradas por tenant_id (impossível vazar dados).
    
    Errors:
    ------
    - 400 Bad Request: parâmetros faltando ou inválidos
    - 500 Internal Server Error: erro de query (DB down, timeout, etc.)
    
    TODO (Fase 2):
    -------------
    - Authentication: @permission_classes([IsAuthenticated])
    - Pagination: cursor pagination para raw data
    - Caching: Redis cache para queries repetidas
    - Rate limiting: throttle por tenant
    - Compression: gzip response para queries grandes
    
    Example:
    -------
    GET /data/points?device_id=550e8400-e29b-41d4-a716-446655440000&point_id=660e8400-e29b-41d4-a716-446655440001&from=2025-10-06T00:00:00Z&to=2025-10-07T00:00:00Z&agg=1m
    """
    # Validar parâmetros obrigatórios
    device_id = request.GET.get("device_id")
    point_id = request.GET.get("point_id")
    ts_from = request.GET.get("from")  # ISO 8601: "2025-10-06T00:00:00Z"
    ts_to = request.GET.get("to")      # ISO 8601: "2025-10-07T00:00:00Z"
    agg = request.GET.get("agg", "1m")  # Default: 1 minuto
    
    if not all([device_id, point_id, ts_from, ts_to]):
        return Response(
            {"error": "Missing required parameters: device_id, point_id, from, to"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validar nível de agregação e obter nome da view
    try:
        view_name = get_aggregate_view_name(agg)
    except ValueError as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Logar tenant atual (debug/auditoria)
    tenant_id = get_current_tenant_id()
    logger.info(
        f"data_points query: tenant={tenant_id}, device={device_id}, "
        f"point={point_id}, agg={agg}, from={ts_from}, to={ts_to}"
    )
    
    # Construir query SQL baseada no nível de agregação
    if agg in ("1m", "5m", "1h"):
        # Usar continuous aggregate (materialized view)
        # Muito mais eficiente para períodos longos (dias/semanas)
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
        # Dados brutos (raw) com LIMIT para prevenir timeout
        # Use apenas para períodos curtos (horas) ou tempo real
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
    
    # Executar query
    # RLS é aplicado automaticamente (tenant_id GUC setado por middleware)
    try:
        with connection.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
            
        # Converter tuplas para dicts (mais fácil de consumir no frontend)
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
        # Logar erro completo (stack trace) para debug
        logger.error(f"data_points error: {e}", exc_info=True)
        return Response(
            {"error": "Database query failed", "detail": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
def health_ts(request):
    """
    Health check do sistema de telemetria (TimescaleDB + RLS).
    
    Este endpoint verifica a integridade do sistema:
    1. RLS está habilitado em ts_measure?
    2. Continuous aggregates existem (ts_measure_1m/5m/1h)?
    3. Tenant_id GUC está configurado?
    
    Response:
    --------
    {
      "status": "ok",
      "rls_enabled": true,
      "continuous_aggregates": 3,  // ts_measure_1m, 5m, 1h
      "tenant_id": "550e8400-e29b-41d4-a716-446655440000"
    }
    
    Checks:
    ------
    - RLS: se False, dados NÃO estão isolados (CRÍTICO!)
    - Aggregates: esperado 3 (1m, 5m, 1h)
    - Tenant_id: se None, queries serão bloqueadas por RLS
    
    Uso:
    ---
    Monitoramento (Prometheus/Grafana):
    - HTTP 200 + rls_enabled=true: OK
    - HTTP 500 ou rls_enabled=false: ALERTA
    
    Kubernetes liveness/readiness probe:
    - GET /health/timeseries (cada 10s)
    
    Example:
    -------
    GET /health/timeseries
    """
    from .dbutils import verify_rls_enabled
    
    try:
        # Verificar se RLS está habilitado (CRÍTICO para segurança)
        rls_enabled = verify_rls_enabled()
        
        # Verificar se continuous aggregates existem
        # Esperado: 3 views (ts_measure_1m, ts_measure_5m, ts_measure_1h)
        with connection.cursor() as cur:
            cur.execute("""
                SELECT count(*) 
                FROM pg_matviews 
                WHERE schemaname = 'public' 
                AND matviewname LIKE 'ts_measure_%'
            """)
            agg_count = cur.fetchone()[0]
        
        # Obter tenant_id atual (para debug)
        tenant_id = get_current_tenant_id()
        
        return Response({
            "status": "ok",
            "rls_enabled": rls_enabled,
            "continuous_aggregates": agg_count,
            "tenant_id": tenant_id
        })
        
    except Exception as e:
        # Logar erro completo para debug
        logger.error(f"health_ts error: {e}", exc_info=True)
        return Response(
            {"status": "error", "detail": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ============================================================================
# DATA POINTS API (Fase R - Opção B)
# ============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_data_points(request):
    """
    GET /api/data/points - Retorna dados de telemetria com roteamento automático.
    
    Query Params:
    -------------
    - device_id: UUID (obrigatório) - Dispositivo IoT
    - point_id: UUID (obrigatório) - Ponto de medição (sensor/tag)
    - start: ISO datetime (obrigatório) - Início da janela temporal
    - end: ISO datetime (obrigatório) - Fim da janela temporal
    - agg: 'raw' | '1m' | '5m' | '1h' (default: 'raw') - Nível de agregação
    
    Roteamento:
    -----------
    - agg=raw → ts_measure_tenant (dados brutos, retenção 14d)
    - agg=1m → ts_measure_1m_tenant (agregação 1min, retenção 365d)
    - agg=5m → ts_measure_5m_tenant (agregação 5min, retenção 730d)
    - agg=1h → ts_measure_1h_tenant (agregação 1h, retenção 1825d)
    
    Degradação Automática:
    ----------------------
    Se agg=raw e janela > 14 dias, degrada para agg=1m automaticamente.
    Response inclui: degraded_from='raw', degraded_to='1m', reason='...'
    
    Isolamento:
    -----------
    Middleware TenantGucMiddleware configura GUC app.tenant_id.
    VIEWs *_tenant filtram automaticamente por tenant.
    Impossível acessar dados de outros tenants (garantido por security_barrier).
    
    Respostas:
    ----------
    - 200: Dados retornados com sucesso
    - 400: Parâmetros inválidos (device_id, point_id, start, end ausentes)
    - 422: Degradação automática aplicada (ainda retorna dados)
    
    Exemplos:
    ---------
    GET /api/data/points?device_id=<uuid>&point_id=<uuid>&start=2025-10-01T00:00:00Z&end=2025-10-08T23:59:59Z&agg=1h
    
    Response:
    {
        "data": [
            {"bucket": "2025-10-01T00:00:00Z", "v_avg": 42.5, "v_max": 45.0, "v_min": 40.0, "n": 60},
            ...
        ],
        "count": 168,
        "agg": "1h",
        "start": "2025-10-01T00:00:00Z",
        "end": "2025-10-08T23:59:59Z"
    }
    """
    from django.utils.dateparse import parse_datetime
    from datetime import timedelta
    from .models import TsMeasureTenant, TsMeasure1mTenant, TsMeasure5mTenant, TsMeasure1hTenant
    from .serializers import TsMeasureRawSerializer, TsMeasureAggSerializer
    
    # Validar parâmetros obrigatórios
    device_id = request.GET.get('device_id')
    point_id = request.GET.get('point_id')
    start_str = request.GET.get('start')
    end_str = request.GET.get('end')
    agg = request.GET.get('agg', 'raw')
    
    if not all([device_id, point_id, start_str, end_str]):
        return Response(
            {
                'error': 'device_id, point_id, start, end são obrigatórios',
                'required_params': ['device_id', 'point_id', 'start', 'end'],
                'optional_params': ['agg (default: raw)']
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Parse datetime
    try:
        start = parse_datetime(start_str)
        end = parse_datetime(end_str)
        
        if not start or not end:
            raise ValueError("datetime inválido")
        
        if start >= end:
            return Response(
                {'error': 'start deve ser menor que end'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    except ValueError as e:
        return Response(
            {
                'error': f'start/end devem ser ISO datetime válidos: {str(e)}',
                'example': '2025-10-08T14:30:00Z'
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validar agg
    valid_aggs = ['raw', '1m', '5m', '1h']
    if agg not in valid_aggs:
        return Response(
            {
                'error': f"agg='{agg}' inválido",
                'valid_values': valid_aggs
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Calcular janela temporal
    window_days = (end - start).days
    
    # Degradação automática: raw com window > 14d → usar 1m
    degraded = False
    original_agg = agg
    
    if agg == 'raw' and window_days > 14:
        agg = '1m'
        degraded = True
        logger.info(
            f"get_data_points: Degradação automática aplicada "
            f"(window={window_days}d > 14d, raw → 1m)"
        )
    
    # Roteamento para MODEL correto (VIEW tenant-scoped)
    if agg == 'raw':
        model = TsMeasureTenant
        time_field = 'ts'
        serializer_class = TsMeasureRawSerializer
    elif agg == '1m':
        model = TsMeasure1mTenant
        time_field = 'bucket'
        serializer_class = TsMeasureAggSerializer
    elif agg == '5m':
        model = TsMeasure5mTenant
        time_field = 'bucket'
        serializer_class = TsMeasureAggSerializer
    elif agg == '1h':
        model = TsMeasure1hTenant
        time_field = 'bucket'
        serializer_class = TsMeasureAggSerializer
    
    # Montar filtros (Django ORM)
    filters = {
        'device_id': device_id,
        'point_id': point_id,
        f'{time_field}__gte': start,
        f'{time_field}__lte': end
    }
    
    # Executar query (isolamento automático via VIEW + GUC)
    try:
        qs = model.objects.filter(**filters).order_by(time_field)
        
        # Limite de segurança: máximo 10k pontos
        MAX_POINTS = 10000
        data = list(qs[:MAX_POINTS])
        
        # Verificar se atingiu limite
        limit_reached = len(data) == MAX_POINTS
        
        # Serializar dados
        serializer = serializer_class(data, many=True)
        
        # Montar response
        response_data = {
            'data': serializer.data,
            'count': len(serializer.data),
            'agg': agg,
            'start': start.isoformat(),
            'end': end.isoformat(),
            'device_id': device_id,
            'point_id': point_id,
        }
        
        # Adicionar info de degradação (se aplicável)
        if degraded:
            response_data['degraded_from'] = original_agg
            response_data['degraded_to'] = agg
            response_data['reason'] = f'window ({window_days}d) exceeds raw retention (14d)'
        
        # Adicionar warning se atingiu limite
        if limit_reached:
            response_data['warning'] = f'Result limited to {MAX_POINTS} points. Consider using higher aggregation level.'
        
        # Status code: 200 se normal, 422 se degradado (mas ainda retorna dados)
        status_code = status.HTTP_200_OK if not degraded else status.HTTP_UNPROCESSABLE_ENTITY
        
        return Response(response_data, status=status_code)
    
    except Exception as e:
        logger.error(f"get_data_points error: {e}", exc_info=True)
        return Response(
            {
                'error': 'Erro ao consultar telemetria',
                'detail': str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
