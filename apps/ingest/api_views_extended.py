"""
Extended API Views for Telemetry - Device-centric endpoints.

Provides convenient endpoints for:
- Latest readings per device
- Historical data for specific devices/sensors
- Device summary with all sensors
"""
import json
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import connection
from django.utils import timezone
from datetime import timedelta
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from .models import Reading
from .serializers import ReadingSerializer


class LatestReadingsView(APIView):
    """
    Get latest readings for a device.
    
    Returns the most recent reading for each sensor of the specified device.
    Useful for dashboards showing current state.
    
    Query parameters:
    - sensor_id (optional): Filter by specific sensor
    """
    
    @extend_schema(
        summary="Get latest readings for device",
        description="""
        Returns the most recent reading for each sensor of the device.
        If sensor_id is provided, returns only that sensor's latest reading.
        """,
        parameters=[
            OpenApiParameter(
                name='device_id',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                required=True,
                description='Device identifier'
            ),
            OpenApiParameter(
                name='sensor_id',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                description='Filter by specific sensor (optional)'
            ),
        ],
        responses={
            200: ReadingSerializer(many=True),
            404: OpenApiTypes.OBJECT,
        }
    )
    def get(self, request, device_id):
        """Get latest readings for device."""
        sensor_id = request.query_params.get('sensor_id')
        
        # Query para pegar última leitura de cada sensor
        # Usa DISTINCT ON do PostgreSQL para eficiência
        sql = """
            SELECT DISTINCT ON (sensor_id)
                   id, device_id, sensor_id, value, labels, ts, created_at
            FROM reading
            WHERE device_id = %s
              AND (%s IS NULL OR sensor_id = %s)
            ORDER BY sensor_id, ts DESC
        """
        
        with connection.cursor() as cursor:
            cursor.execute(sql, [device_id, sensor_id, sensor_id])
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
        
        if not rows:
            return Response(
                {'detail': 'No readings found for this device'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Converter rows para dicts
        data = [dict(zip(columns, row)) for row in rows]
        
        # Serializar
        serializer = ReadingSerializer(data, many=True)
        return Response({
            'device_id': device_id,
            'last_update': max(r['ts'] for r in data),
            'count': len(data),
            'readings': serializer.data
        })


class DeviceHistoryView(APIView):
    """
    Get historical readings for a device.
    
    Returns time-series data for the device, optionally filtered by sensor.
    Supports automatic aggregation for large time ranges.
    
    Query parameters:
    - sensor_id (optional): Filter by specific sensor
    - from (optional): Start time (ISO-8601)
    - to (optional): End time (ISO-8601)
    - interval (optional): Aggregation interval (1m, 5m, 1h, raw)
    - limit (optional): Max results (default 500, max 5000)
    """
    
    MAX_LIMIT = 5000
    DEFAULT_LIMIT = 500
    
    @extend_schema(
        summary="Get historical data for device",
        description="""
        Returns time-series readings for the device.
        
        Intervals:
        - raw: No aggregation (default for < 1 hour)
        - 1m: 1-minute buckets
        - 5m: 5-minute buckets
        - 1h: 1-hour buckets
        
        Auto-aggregation:
        - Range < 1h → raw
        - Range 1h-6h → 1m
        - Range 6h-24h → 5m
        - Range > 24h → 1h
        """,
        parameters=[
            OpenApiParameter(
                name='device_id',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                required=True,
                description='Device identifier'
            ),
            OpenApiParameter(
                name='sensor_id',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                description='Filter by specific sensor'
            ),
            OpenApiParameter(
                name='from',
                type=OpenApiTypes.DATETIME,
                location=OpenApiParameter.QUERY,
                required=False,
                description='Start time (ISO-8601, default: 24h ago)'
            ),
            OpenApiParameter(
                name='to',
                type=OpenApiTypes.DATETIME,
                location=OpenApiParameter.QUERY,
                required=False,
                description='End time (ISO-8601, default: now)'
            ),
            OpenApiParameter(
                name='interval',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                enum=['raw', '1m', '5m', '1h'],
                description='Aggregation interval (default: auto)'
            ),
            OpenApiParameter(
                name='limit',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=False,
                description=f'Max results (default {DEFAULT_LIMIT}, max {MAX_LIMIT})'
            ),
        ],
        responses={
            200: OpenApiTypes.OBJECT,
            400: OpenApiTypes.OBJECT,
        }
    )
    def get(self, request, device_id):
        """Get historical data for device."""
        # Parse parameters
        sensor_id = request.query_params.get('sensor_id')
        from_str = request.query_params.get('from')
        to_str = request.query_params.get('to')
        interval = request.query_params.get('interval', 'auto')
        
        # Default time range: last 24 hours
        now = timezone.now()
        ts_to = timezone.datetime.fromisoformat(to_str.replace('Z', '+00:00')) if to_str else now
        ts_from = timezone.datetime.fromisoformat(from_str.replace('Z', '+00:00')) if from_str else (now - timedelta(hours=24))
        
        # Validate time range
        if ts_from >= ts_to:
            return Response(
                {'detail': 'Invalid time range: from must be before to'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Auto-select interval based on time range
        if interval == 'auto':
            time_diff = ts_to - ts_from
            if time_diff <= timedelta(hours=1):
                interval = 'raw'
            elif time_diff <= timedelta(hours=6):
                interval = '1m'
            elif time_diff <= timedelta(hours=24):
                interval = '5m'
            else:
                interval = '1h'
        
        # Limit
        try:
            limit = min(
                int(request.query_params.get('limit', self.DEFAULT_LIMIT)),
                self.MAX_LIMIT
            )
        except ValueError:
            return Response(
                {'detail': 'Invalid limit parameter'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Build query
        if interval == 'raw':
            # No aggregation
            sql = """
                SELECT ts, sensor_id, value
                FROM reading
                WHERE device_id = %s
                  AND (%s IS NULL OR sensor_id = %s)
                  AND ts >= %s
                  AND ts <= %s
                ORDER BY ts DESC
                LIMIT %s
            """
            params = [device_id, sensor_id, sensor_id, ts_from, ts_to, limit]
        else:
            # With aggregation
            bucket_interval = {'1m': '1 minute', '5m': '5 minutes', '1h': '1 hour'}[interval]
            sql = f"""
                SELECT time_bucket(%(bucket_interval)s, ts) AS bucket,
                       sensor_id,
                       avg(value) AS avg_value,
                       min(value) AS min_value,
                       max(value) AS max_value,
                       last(value, ts) AS last_value,
                       count(*) AS count
                FROM reading
                WHERE device_id = %(device_id)s
                  AND (%(sensor_id)s IS NULL OR sensor_id = %(sensor_id)s)
                  AND ts >= %(ts_from)s
                  AND ts <= %(ts_to)s
                GROUP BY bucket, sensor_id
                ORDER BY bucket DESC
                LIMIT %(limit)s
            """
            params = {
                'bucket_interval': bucket_interval,
                'device_id': device_id,
                'sensor_id': sensor_id,
                'ts_from': ts_from,
                'ts_to': ts_to,
                'limit': limit
            }
        
        # Execute query
        with connection.cursor() as cursor:
            if interval == 'raw':
                cursor.execute(sql, params)
            else:
                cursor.execute(sql, params)
            
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
        
        # Convert to dicts
        data = [dict(zip(columns, row)) for row in rows]
        
        return Response({
            'device_id': device_id,
            'sensor_id': sensor_id,
            'interval': interval,
            'from': ts_from.isoformat(),
            'to': ts_to.isoformat(),
            'count': len(data),
            'data': data
        })


class DeviceSummaryView(APIView):
    """
    Get summary of device with all sensors.
    
    Returns:
    - Device status (online/offline based on last reading)
    - List of all sensors with their latest readings
    - Statistics (total readings in last 24h, avg interval)
    """
    
    @extend_schema(
        summary="Get device summary",
        description="""
        Returns comprehensive summary of device:
        - Status (online if reading < 5 minutes old)
        - All sensors with latest readings
        - 24-hour statistics
        """,
        parameters=[
            OpenApiParameter(
                name='device_id',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                required=True,
                description='Device identifier'
            ),
        ],
        responses={
            200: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        }
    )
    def get(self, request, device_id):
        """Get device summary."""
        now = timezone.now()
        online_threshold = now - timedelta(minutes=5)
        stats_window = now - timedelta(hours=24)
        
        # Get latest reading per sensor
        sql_latest = """
            SELECT DISTINCT ON (sensor_id)
                   sensor_id,
                   value,
                   labels,
                   ts
            FROM reading
            WHERE device_id = %s
            ORDER BY sensor_id, ts DESC
        """
        
        # Get 24h statistics
        sql_stats = """
            SELECT COUNT(*) as total_readings,
                   COUNT(DISTINCT sensor_id) as sensor_count,
                   EXTRACT(EPOCH FROM (MAX(ts) - MIN(ts))) / COUNT(*) as avg_interval_seconds
            FROM reading
            WHERE device_id = %s
              AND ts >= %s
        """
        
        with connection.cursor() as cursor:
            # Latest readings
            cursor.execute(sql_latest, [device_id])
            latest_columns = [col[0] for col in cursor.description]
            latest_rows = cursor.fetchall()
            
            if not latest_rows:
                return Response(
                    {'detail': 'Device not found or no readings'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Statistics
            cursor.execute(sql_stats, [device_id, stats_window])
            stats_row = cursor.fetchone()
        
        # Convert to dicts
        sensors = []
        last_seen = None
        
        for row in latest_rows:
            reading_data = dict(zip(latest_columns, row))
            reading_ts = reading_data['ts']
            
            if last_seen is None or reading_ts > last_seen:
                last_seen = reading_ts
            
            # Parse labels (pode ser string JSON ou dict)
            labels = reading_data.get('labels', {})
            if isinstance(labels, str):
                try:
                    labels = json.loads(labels)
                except (json.JSONDecodeError, TypeError):
                    labels = {}
            
            # Determinar status: online se última leitura foi dentro do threshold
            is_online = reading_ts >= online_threshold
            
            sensors.append({
                'sensor_id': reading_data['sensor_id'],
                'sensor_name': reading_data['sensor_id'],  # Por enquanto usa o ID como nome
                'sensor_type': labels.get('type', 'unknown') if isinstance(labels, dict) else 'unknown',
                'unit': labels.get('unit', '') if isinstance(labels, dict) else '',
                'is_online': is_online,
                'last_value': reading_data['value'],
                'last_reading': reading_ts.isoformat(),
                'statistics_24h': {
                    'avg': None,  # TODO: Calcular estatísticas
                    'min': None,
                    'max': None,
                    'count': 0,
                    'stddev': None,
                }
            })
        
        # Device status
        device_status = 'online' if last_seen >= online_threshold else 'offline'
        
        # Format statistics
        total_readings, sensor_count, avg_interval = stats_row
        statistics = {
            'total_readings_24h': total_readings or 0,
            'sensor_count': sensor_count or 0,
            'avg_interval': f"{int(avg_interval or 0)}s" if avg_interval else 'N/A'
        }
        
        # DEBUG: Log response antes de retornar
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"📊 Summary response for {device_id}: {len(sensors)} sensors")
        if sensors:
            logger.info(f"📊 First sensor example: {sensors[0]}")
        
        return Response({
            'device_id': device_id,
            'status': device_status,
            'last_seen': last_seen.isoformat() if last_seen else None,
            'sensors': sensors,
            'statistics': statistics
        })
