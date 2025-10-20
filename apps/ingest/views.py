import logging
from datetime import datetime

from django.db import connection
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.tenants.models import Tenant
from .models import Telemetry, Reading

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
        logger.info("=" * 60)
        logger.info("🔵 INGEST POST INICIADO")
        logger.info(f"Headers: {dict(request.headers)}")
        logger.info(f"Content-Type: {request.content_type}")
        logger.info(f"Body (primeiros 500 chars): {request.body[:500]}")
        logger.info("=" * 60)
        
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
        
        # DEBUG: Log incoming data
        logger.info(f"📥 Ingest received data: {data}")
        
        if not isinstance(data, dict):
            logger.warning(f"Invalid payload type: {type(data)}")
            return Response(
                {"error": "Payload must be JSON object"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Extract fields from EMQX payload
        client_id = data.get('client_id')  # Optional, will use device_id from payload
        topic = data.get('topic')
        payload = data.get('payload')
        ts = data.get('ts')  # Unix timestamp in milliseconds
        
        # Validate required fields (client_id is optional)
        if not all([topic, payload, ts]):
            missing = [f for f in ['topic', 'payload', 'ts'] 
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
        
        # Extract device_id from payload (correct device ID, not MQTT client_id)
        device_id = payload.get('device_id') if isinstance(payload, dict) else None
        if not device_id:
            logger.warning(f"Missing device_id in payload. Using client_id as fallback: {client_id}")
            device_id = client_id
        
        # Save to database
        try:
            # 1. Save raw telemetry (MQTT message)
            telemetry = Telemetry.objects.create(
                device_id=device_id,  # Use device_id from payload, not MQTT client_id
                topic=topic,
                payload=payload,
                timestamp=timestamp
            )
            
            # 2. Auto-vincular sensores ao ativo baseado no tópico MQTT
            # Padrão esperado: tenants/{tenant}/assets/{asset_tag}/telemetry
            asset_tag = self._extract_asset_tag_from_topic(topic)
            if asset_tag:
                logger.info(f"🔗 Asset tag extraído do tópico: {asset_tag}")
                self._auto_link_sensors_to_asset(asset_tag, payload, device_id)
            else:
                logger.warning(f"⚠️ Não foi possível extrair asset_tag do tópico: {topic}")
            
            # 3. Extract and save individual sensor readings
            sensors = payload.get('sensors', []) if isinstance(payload, dict) else []
            readings_created = 0
            
            for sensor in sensors:
                if isinstance(sensor, dict):
                    sensor_id = sensor.get('sensor_id')
                    value = sensor.get('value')
                    
                    if sensor_id and value is not None:
                        # Extract labels (type, unit, location, description)
                        labels = sensor.get('labels', {})
                        if not isinstance(labels, dict):
                            labels = {}
                        
                        # Add unit to labels if not already there
                        if 'unit' not in labels and sensor.get('unit'):
                            labels['unit'] = sensor.get('unit')
                        
                        # Add type to labels if not already there
                        if 'type' not in labels and sensor.get('type'):
                            labels['type'] = sensor.get('type')
                        
                        Reading.objects.create(
                            device_id=device_id,
                            sensor_id=sensor_id,
                            value=float(value),
                            labels=labels,
                            ts=timestamp
                        )
                        readings_created += 1
            
            logger.info(
                f"Telemetry saved: tenant={tenant_slug}, "
                f"device={device_id}, topic={topic}"
            )
            logger.info(f"📊 Created {readings_created} sensor readings")
            
            return Response(
                {
                    "status": "accepted",
                    "id": telemetry.id,
                    "device_id": telemetry.device_id,
                    "timestamp": telemetry.timestamp.isoformat(),
                    "sensors_saved": readings_created
                },
                status=status.HTTP_202_ACCEPTED
            )
            
        except Exception as e:
            logger.error(f"Failed to save telemetry: {e}", exc_info=True)
            return Response(
                {"error": "Failed to save telemetry"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _extract_asset_tag_from_topic(self, topic):
        """
        Extrai o asset_tag do tópico MQTT.
        
        Padrões suportados:
        - tenants/{tenant}/assets/{asset_tag}/telemetry
        - tenants/{tenant}/devices/{device_id}/assets/{asset_tag}
        - {asset_tag}/telemetry
        
        Args:
            topic (str): Tópico MQTT completo
        
        Returns:
            str or None: Asset tag extraído ou None se não encontrado
        """
        parts = topic.split('/')
        
        # Padrão 1: tenants/{tenant}/assets/{asset_tag}/telemetry
        if 'assets' in parts:
            try:
                asset_idx = parts.index('assets')
                if asset_idx + 1 < len(parts):
                    asset_tag = parts[asset_idx + 1]
                    logger.info(f"✅ Asset tag extraído (padrão 1): {asset_tag}")
                    return asset_tag
            except (ValueError, IndexError):
                pass
        
        # Padrão 2: {asset_tag}/telemetry (tag diretamente)
        # Valida se o primeiro componente parece uma tag de ativo (ex: CH-001, AHU-001)
        if len(parts) >= 1:
            potential_tag = parts[0]
            if '-' in potential_tag and len(potential_tag) <= 50:
                logger.info(f"✅ Asset tag extraído (padrão 2): {potential_tag}")
                return potential_tag
        
        return None
    
    def _auto_link_sensors_to_asset(self, asset_tag, payload, device_id):
        """
        Vincula automaticamente sensores ao ativo baseado no tópico.
        
        Fluxo:
        1. Busca o Asset pelo tag
        2. Para cada sensor no payload:
           a. Busca ou cria um Device padrão para o Asset
           b. Busca o Sensor pelo sensor_id
           c. Se o Sensor existe mas não está vinculado corretamente, atualiza
           d. Se o Sensor não existe, apenas registra no log (será criado manualmente)
        
        Args:
            asset_tag (str): Tag do ativo (ex: CH-001)
            payload (dict): Payload MQTT com lista de sensores
            device_id (str): ID do dispositivo MQTT
        """
        try:
            from apps.assets.models import Asset, Device, Sensor
            
            # Busca o ativo pelo tag
            try:
                asset = Asset.objects.get(tag=asset_tag, is_active=True)
                logger.info(f"🎯 Asset encontrado: {asset.tag} - {asset.name}")
            except Asset.DoesNotExist:
                logger.warning(f"⚠️ Asset não encontrado: {asset_tag}")
                return
            
            # Busca ou cria um Device padrão para o ativo
            # Usa o mqtt_client_id como referência
            device, device_created = Device.objects.get_or_create(
                mqtt_client_id=device_id,
                defaults={
                    'asset': asset,
                    'name': f'Gateway {asset_tag}',
                    'serial_number': f'SN-{device_id}',
                    'device_type': 'GATEWAY',
                    'status': 'ONLINE'
                }
            )
            
            if device_created:
                logger.info(f"✨ Device criado automaticamente: {device.name} para asset {asset_tag}")
            else:
                # Se o device já existe mas está em outro asset, atualiza
                if device.asset_id != asset.id:
                    logger.info(f"🔄 Device {device.name} movido de {device.asset.tag} para {asset_tag}")
                    device.asset = asset
                    device.save(update_fields=['asset', 'updated_at'])
            
            # Processa cada sensor no payload
            sensors = payload.get('sensors', []) if isinstance(payload, dict) else []
            
            for sensor_data in sensors:
                if not isinstance(sensor_data, dict):
                    continue
                
                sensor_id = sensor_data.get('sensor_id')
                if not sensor_id:
                    continue
                
                try:
                    # Busca o sensor pelo tag (sensor_id)
                    sensor = Sensor.objects.filter(tag=sensor_id, is_active=True).first()
                    
                    if sensor:
                        # Se o sensor existe mas está em device diferente, atualiza
                        if sensor.device_id != device.id:
                            old_asset = sensor.device.asset.tag if sensor.device else 'N/A'
                            logger.info(f"🔄 Sensor {sensor_id} movido de {old_asset} para {asset_tag}")
                            sensor.device = device
                            sensor.save(update_fields=['device', 'updated_at'])
                        else:
                            logger.debug(f"✅ Sensor {sensor_id} já vinculado ao asset {asset_tag}")
                    else:
                        # Sensor não existe - apenas registra no log
                        # O técnico deve criar manualmente no admin
                        logger.info(
                            f"ℹ️ Sensor {sensor_id} não encontrado. "
                            f"Criar manualmente no admin e vincular ao device {device.mqtt_client_id}"
                        )
                
                except Exception as e:
                    logger.error(f"❌ Erro ao processar sensor {sensor_id}: {e}", exc_info=True)
        
        except Exception as e:
            logger.error(f"❌ Erro no auto-link de sensores ao asset {asset_tag}: {e}", exc_info=True)
