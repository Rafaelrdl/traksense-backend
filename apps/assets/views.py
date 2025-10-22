"""
ViewSets para a API REST do catálogo de ativos.

Este módulo implementa as views da API REST usando Django REST Framework
ViewSets para expor operações CRUD e ações customizadas.

Classes:
    SiteViewSet: CRUD para Sites com filtros e listagem de assets
    AssetViewSet: CRUD para Assets com filtros avançados e ações customizadas
    DeviceViewSet: CRUD para Devices com filtros e listagem de sensors
    SensorViewSet: CRUD para Sensors com filtros por métricas
"""

from django.utils import timezone
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import Site, Asset, Device, Sensor
from .serializers import (
    SiteSerializer,
    AssetSerializer,
    AssetListSerializer,
    DeviceSerializer,
    DeviceListSerializer,
    SensorSerializer,
    SensorListSerializer,
    SensorBulkCreateSerializer,
)


class SiteViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciamento de Sites.
    
    Endpoints:
        GET /api/sites/ - Lista todos os sites
        POST /api/sites/ - Cria novo site
        GET /api/sites/{id}/ - Detalhes de um site
        PUT /api/sites/{id}/ - Atualiza site completo
        PATCH /api/sites/{id}/ - Atualiza site parcial
        DELETE /api/sites/{id}/ - Remove site
        GET /api/sites/{id}/assets/ - Lista assets do site
        GET /api/sites/{id}/stats/ - Estatísticas do site
    
    Filtros:
        - company: Filtra por empresa
        - sector: Filtra por setor
        - subsector: Filtra por subsetor
        - city: Filtra por cidade
        - state: Filtra por estado
        - country: Filtra por país
        - timezone: Filtra por timezone
    
    Busca:
        - name, company, address, city
    
    Ordenação:
        - name, company, created_at (padrão: name)
    """
    
    queryset = Site.objects.all()
    serializer_class = SiteSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['company', 'sector', 'subsector', 'timezone']
    search_fields = ['name', 'company', 'address', 'city']
    ordering_fields = ['name', 'company', 'created_at']
    ordering = ['name']
    
    @action(detail=True, methods=['get'])
    def assets(self, request, pk=None):
        """
        Lista todos os assets de um site específico.
        
        GET /api/sites/{id}/assets/
        
        Query params:
            - status: Filtra por status (OPERATIONAL, WARNING, etc)
            - asset_type: Filtra por tipo de ativo
        """
        site = self.get_object()
        assets = site.assets.all()
        
        # Filtros opcionais
        status_filter = request.query_params.get('status')
        if status_filter:
            assets = assets.filter(status=status_filter)
        
        asset_type = request.query_params.get('asset_type')
        if asset_type:
            assets = assets.filter(asset_type=asset_type)
        
        serializer = AssetListSerializer(assets, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def devices(self, request, pk=None):
        """
        Lista todos os devices de um site específico (via assets).
        
        GET /api/sites/{id}/devices/
        
        Query params:
            - device_type: Filtra por tipo de dispositivo (GATEWAY, CONTROLLER, etc)
            - status: Filtra por status
            - is_online: Filtra por status online (true/false)
        """
        site = self.get_object()
        
        # Buscar devices através dos assets do site
        devices = Device.objects.filter(asset__site=site).select_related('asset')
        
        # Filtros opcionais
        device_type = request.query_params.get('device_type')
        if device_type:
            devices = devices.filter(device_type=device_type)
        
        status_filter = request.query_params.get('status')
        if status_filter:
            devices = devices.filter(status=status_filter)
        
        is_online = request.query_params.get('is_online')
        if is_online is not None:
            is_online_bool = is_online.lower() == 'true'
            devices = devices.filter(is_online=is_online_bool)
        
        serializer = DeviceListSerializer(devices, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """
        Retorna estatísticas do site.
        
        GET /api/sites/{id}/stats/
        
        Retorna:
            - total_assets: Total de ativos
            - assets_by_status: Contagem por status
            - assets_by_type: Contagem por tipo
            - total_devices: Total de dispositivos
            - total_sensors: Total de sensores
            - online_devices: Dispositivos online
            - online_sensors: Sensores online
        """
        site = self.get_object()
        assets = site.assets.all()
        
        # Estatísticas de assets
        stats = {
            'total_assets': assets.count(),
            'assets_by_status': {},
            'assets_by_type': {},
            'total_devices': 0,
            'total_sensors': 0,
            'online_devices': 0,
            'online_sensors': 0,
        }
        
        # Contagem por status
        for asset in assets:
            status_key = asset.status
            stats['assets_by_status'][status_key] = stats['assets_by_status'].get(status_key, 0) + 1
            
            # Contagem por tipo
            type_key = asset.asset_type
            stats['assets_by_type'][type_key] = stats['assets_by_type'].get(type_key, 0) + 1
        
        # Estatísticas de devices e sensors
        devices = Device.objects.filter(asset__site=site)
        stats['total_devices'] = devices.count()
        stats['online_devices'] = devices.filter(is_online=True).count()
        
        sensors = Sensor.objects.filter(device__asset__site=site)
        stats['total_sensors'] = sensors.count()
        stats['online_sensors'] = sensors.filter(is_online=True).count()
        
        return Response(stats)


class AssetViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciamento de Assets.
    
    Endpoints:
        GET /api/assets/ - Lista todos os assets (usa AssetListSerializer)
        POST /api/assets/ - Cria novo asset
        GET /api/assets/{id}/ - Detalhes de um asset (usa AssetSerializer completo)
        PUT /api/assets/{id}/ - Atualiza asset completo
        PATCH /api/assets/{id}/ - Atualiza asset parcial
        DELETE /api/assets/{id}/ - Remove asset
        GET /api/assets/{id}/devices/ - Lista devices do asset
        GET /api/assets/{id}/sensors/ - Lista todos os sensors do asset
        POST /api/assets/{id}/calculate_health/ - Recalcula health score
    
    Filtros:
        - site: Filtra por site
        - asset_type: Filtra por tipo de ativo
        - status: Filtra por status
        - manufacturer: Filtra por fabricante
    
    Busca:
        - tag, name, manufacturer, model, serial_number
    
    Ordenação:
        - tag, name, status, health_score, created_at (padrão: tag)
    """
    
    queryset = Asset.objects.select_related('site').all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['site', 'asset_type', 'status', 'manufacturer']
    search_fields = ['tag', 'name', 'manufacturer', 'model', 'serial_number']
    ordering_fields = ['tag', 'name', 'status', 'health_score', 'created_at']
    ordering = ['tag']
    
    def get_serializer_class(self):
        """
        Usa AssetListSerializer para listagem e AssetSerializer para detalhes.
        """
        if self.action == 'list':
            return AssetListSerializer
        return AssetSerializer
    
    @action(detail=True, methods=['get'])
    def devices(self, request, pk=None):
        """
        Lista todos os devices de um asset específico.
        
        GET /api/assets/{id}/devices/
        
        Query params:
            - status: Filtra por status (ACTIVE, INACTIVE, etc)
            - device_type: Filtra por tipo de dispositivo
            - is_online: Filtra por status online (true/false)
        """
        asset = self.get_object()
        devices = asset.devices.all()
        
        # Filtros opcionais
        status_filter = request.query_params.get('status')
        if status_filter:
            devices = devices.filter(status=status_filter)
        
        device_type = request.query_params.get('device_type')
        if device_type:
            devices = devices.filter(device_type=device_type)
        
        is_online = request.query_params.get('is_online')
        if is_online is not None:
            is_online_bool = is_online.lower() == 'true'
            devices = devices.filter(is_online=is_online_bool)
        
        serializer = DeviceListSerializer(devices, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def sensors(self, request, pk=None):
        """
        Lista todos os sensors de um asset (através dos devices).
        
        GET /api/assets/{id}/sensors/
        
        Query params:
            - metric_type: Filtra por tipo de métrica
            - is_online: Filtra por status online (true/false)
        """
        asset = self.get_object()
        sensors = Sensor.objects.filter(device__asset=asset).select_related('device')
        
        # Filtros opcionais
        metric_type = request.query_params.get('metric_type')
        if metric_type:
            sensors = sensors.filter(metric_type=metric_type)
        
        is_online = request.query_params.get('is_online')
        if is_online is not None:
            is_online_bool = is_online.lower() == 'true'
            sensors = sensors.filter(is_online=is_online_bool)
        
        serializer = SensorListSerializer(sensors, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def calculate_health(self, request, pk=None):
        """
        Recalcula o health score do asset.
        
        POST /api/assets/{id}/calculate_health/
        
        Retorna:
            - health_score: Novo valor calculado (0-100)
            - updated_at: Timestamp da atualização
        """
        asset = self.get_object()
        
        # TODO: Implementar lógica real de cálculo
        # Por enquanto, usa o método placeholder do modelo
        asset.calculate_health_score()
        asset.save()
        
        return Response({
            'health_score': asset.health_score,
            'updated_at': asset.updated_at,
        })


class DeviceViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciamento de Devices.
    
    Endpoints:
        GET /api/devices/ - Lista todos os devices (usa DeviceListSerializer)
        POST /api/devices/ - Cria novo device
        GET /api/devices/{id}/ - Detalhes de um device (usa DeviceSerializer completo)
        PUT /api/devices/{id}/ - Atualiza device completo
        PATCH /api/devices/{id}/ - Atualiza device parcial
        DELETE /api/devices/{id}/ - Remove device
        GET /api/devices/{id}/sensors/ - Lista sensors do device
        POST /api/devices/{id}/sensors/bulk/ - Cria múltiplos sensors de uma vez
        POST /api/devices/{id}/heartbeat/ - Registra heartbeat (atualiza last_seen)
    
    Filtros:
        - asset: Filtra por asset
        - device_type: Filtra por tipo de dispositivo
        - status: Filtra por status
        - is_online: Filtra por status online
    
    Busca:
        - name, serial_number, mqtt_client_id
    
    Ordenação:
        - name, serial_number, status, last_seen, created_at (padrão: name)
    """
    
    queryset = Device.objects.select_related('asset', 'asset__site').all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['asset', 'device_type', 'status']
    search_fields = ['name', 'serial_number', 'mqtt_client_id']
    ordering_fields = ['name', 'serial_number', 'status', 'last_seen', 'created_at']
    ordering = ['name']
    
    def get_serializer_class(self):
        """
        Usa DeviceListSerializer para listagem e DeviceSerializer para detalhes.
        """
        if self.action == 'list':
            return DeviceListSerializer
        return DeviceSerializer
    
    @action(detail=True, methods=['get'])
    def sensors(self, request, pk=None):
        """
        Lista todos os sensors de um device específico.
        
        GET /api/devices/{id}/sensors/
        
        Query params:
            - metric_type: Filtra por tipo de métrica
            - is_online: Filtra por status online (true/false)
        """
        device = self.get_object()
        sensors = device.sensors.all()
        
        # Filtros opcionais
        metric_type = request.query_params.get('metric_type')
        if metric_type:
            sensors = sensors.filter(metric_type=metric_type)
        
        is_online = request.query_params.get('is_online')
        if is_online is not None:
            is_online_bool = is_online.lower() == 'true'
            sensors = sensors.filter(is_online=is_online_bool)
        
        serializer = SensorListSerializer(sensors, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def sensors_bulk(self, request, pk=None):
        """
        Cria múltiplos sensors de uma vez para este device.
        
        POST /api/devices/{id}/sensors/bulk/
        
        Body:
            {
                "sensors": [
                    {
                        "tag": "TEMP-001",
                        "metric_type": "TEMPERATURE",
                        "unit": "°C",
                        "description": "Temperatura de entrada"
                    },
                    {
                        "tag": "PRES-001",
                        "metric_type": "PRESSURE",
                        "unit": "bar"
                    }
                ]
            }
        
        Retorna: Lista dos sensors criados
        """
        device = self.get_object()
        serializer = SensorBulkCreateSerializer(
            data=request.data,
            context={'device': device}
        )
        serializer.is_valid(raise_exception=True)
        sensors = serializer.save()
        
        output_serializer = SensorSerializer(sensors, many=True)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def heartbeat(self, request, pk=None):
        """
        Registra um heartbeat do device (atualiza last_seen).
        
        POST /api/devices/{id}/heartbeat/
        
        Retorna:
            - last_seen: Timestamp atualizado
            - is_online: Status online do device
        """
        device = self.get_object()
        device.update_status()
        
        return Response({
            'last_seen': device.last_seen,
            'is_online': device.is_online,
            'status': device.status,
        })


class SensorViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciamento de Sensors.
    
    Endpoints:
        GET /api/sensors/ - Lista todos os sensors (usa SensorListSerializer)
        POST /api/sensors/ - Cria novo sensor
        GET /api/sensors/{id}/ - Detalhes de um sensor (usa SensorSerializer completo)
        PUT /api/sensors/{id}/ - Atualiza sensor completo
        PATCH /api/sensors/{id}/ - Atualiza sensor parcial
        DELETE /api/sensors/{id}/ - Remove sensor
        POST /api/sensors/{id}/update_reading/ - Atualiza leitura do sensor
    
    Filtros:
        - device: Filtra por device
        - metric_type: Filtra por tipo de métrica
        - unit: Filtra por unidade
        - is_online: Filtra por status online
    
    Busca:
        - tag, description
    
    Ordenação:
        - tag, metric_type, last_reading, created_at (padrão: tag)
    """
    
    queryset = Sensor.objects.select_related(
        'device',
        'device__asset',
        'device__asset__site'
    ).all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['device', 'metric_type', 'unit', 'is_online']
    search_fields = ['tag', 'description']
    ordering_fields = ['tag', 'metric_type', 'last_reading', 'created_at']
    ordering = ['tag']
    
    def get_serializer_class(self):
        """
        Usa SensorListSerializer para listagem e SensorSerializer para detalhes.
        """
        if self.action == 'list':
            return SensorListSerializer
        return SensorSerializer
    
    @action(detail=True, methods=['post'])
    def update_reading(self, request, pk=None):
        """
        Atualiza a última leitura do sensor.
        
        POST /api/sensors/{id}/update_reading/
        
        Body:
            {
                "value": 23.5,
                "timestamp": "2025-10-19T10:30:00Z"  # Opcional
            }
        
        Retorna:
            - last_value: Novo valor
            - last_reading: Timestamp da leitura
            - is_online: Status atualizado
        """
        sensor = self.get_object()
        value = request.data.get('value')
        timestamp = request.data.get('timestamp')
        
        if value is None:
            return Response(
                {'error': 'Campo "value" é obrigatório.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Converte timestamp se fornecido
        if timestamp:
            from dateutil import parser
            try:
                timestamp = parser.parse(timestamp)
            except (ValueError, TypeError):
                return Response(
                    {'error': 'Formato de timestamp inválido. Use ISO 8601.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            timestamp = timezone.now()
        
        # Atualiza sensor
        sensor.update_last_reading(value, timestamp)
        
        return Response({
            'last_value': sensor.last_value,
            'last_reading': sensor.last_reading,
            'is_online': sensor.is_online,
        })
