import logging
from datetime import datetime

from django.db import connection
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.tenants.models import Tenant
from .models import Telemetry

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class IngestView(APIView):
    """
    Endpoint to receive telemetry data from EMQX Rule Engine.
    
    This endpoint bypasses multi-tenant middleware by manually switching
    to the tenant schema based on x-tenant header.
    
    Expected payload from EMQX:
    {
        "client_id": "device-001",
        "topic": "tenants/umc/devices/001/sensors/temperature",
        "payload": {"value": 23.5, "unit": "celsius"},
        "ts": 1697572800000  // Unix timestamp in milliseconds
    }
    
    Headers expected:
    - x-tenant: tenant slug (e.g., "umc")
    - content-type: application/json
    """
    
    # Disable authentication for MQTT ingestion
    # (EMQX is within Docker network, not exposed to internet)
    authentication_classes = []
    permission_classes = []
    
    def post(self, request, *args, **kwargs):
        """
        Process incoming telemetry data from EMQX.
        """
        # Debug logging
        logger.info(f"🔵 IngestView POST recebido")
        logger.info(f"  Headers: {dict(request.headers)}")
        logger.info(f"  Content-Type: {request.content_type}")
        logger.info(f"  Body (raw): {request.body[:500]}")  # First 500 chars
        logger.info(f"  Data (parsed): {request.data}")
        
        # Extract tenant from header
        tenant_slug = request.headers.get('x-tenant')
        if not tenant_slug:
            logger.warning("Missing x-tenant header in ingest request")
            return Response(
                {"error": "Missing x-tenant header"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get tenant from public schema and switch to its schema
        try:
            # Ensure we're searching in public schema
            connection.set_schema_to_public()
            tenant = Tenant.objects.get(slug=tenant_slug)
            # Switch to tenant schema for saving data
            connection.set_tenant(tenant)
        except Tenant.DoesNotExist:
            logger.warning(f"Tenant not found: {tenant_slug}")
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Validate payload structure
        data = request.data
        if not isinstance(data, dict):
            logger.warning(f"Invalid payload type: {type(data)}")
            return Response(
                {"error": "Payload must be JSON object"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Extract fields from EMQX payload
        client_id = data.get('client_id')
        topic = data.get('topic')
        payload = data.get('payload')
        ts = data.get('ts')  # Unix timestamp in milliseconds
        
        # Validate required fields
        if not all([client_id, topic, payload, ts]):
            missing = [f for f in ['client_id', 'topic', 'payload', 'ts'] 
                      if not data.get(f)]
            logger.warning(f"Missing required fields: {missing}")
            return Response(
                {"error": f"Missing required fields: {', '.join(missing)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Convert Unix milliseconds to datetime
        try:
            timestamp = datetime.fromtimestamp(ts / 1000.0)
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid timestamp: {ts} - {e}")
            return Response(
                {"error": "Invalid timestamp format"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Parse payload if it's a string (should already be dict from JSON)
        if isinstance(payload, str):
            import json
            try:
                payload = json.loads(payload)
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse payload JSON: {e}")
                return Response(
                    {"error": "Invalid JSON in payload"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Save to database
        try:
            telemetry = Telemetry.objects.create(
                device_id=client_id,
                topic=topic,
                payload=payload,
                timestamp=timestamp
            )
            
            logger.info(
                f"Telemetry saved: tenant={tenant_slug}, "
                f"device={client_id}, topic={topic}"
            )
            
            return Response(
                {
                    "status": "accepted",
                    "id": telemetry.id,
                    "device_id": telemetry.device_id,
                    "timestamp": telemetry.timestamp.isoformat()
                },
                status=status.HTTP_202_ACCEPTED
            )
            
        except Exception as e:
            logger.error(f"Failed to save telemetry: {e}", exc_info=True)
            return Response(
                {"error": "Failed to save telemetry"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
