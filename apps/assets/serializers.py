"""
Serializers para a API REST do catálogo de ativos.

Este módulo implementa os serializers do Django REST Framework para expor
os modelos Site, Asset, Device e Sensor via API REST.

Classes:
    SiteSerializer: Serializer para Sites com contador de ativos
    AssetSerializer: Serializer para Assets com informações aninhadas
    DeviceSerializer: Serializer para Devices com contadores
    SensorSerializer: Serializer para Sensors com lookup de nomes
"""

from rest_framework import serializers
from .models import Site, Asset, Device, Sensor


class SiteSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo Site.
    
    Campos adicionais:
        - asset_count: Número de ativos neste site (read-only)
        - full_name: Nome completo com empresa (read-only)
    
    Campos read-only:
        - id, created_at, updated_at, asset_count, full_name
    """
    
    asset_count = serializers.SerializerMethodField()
    full_name = serializers.CharField(read_only=True)
    
    class Meta:
        model = Site
        fields = [
            'id',
            'name',
            'full_name',
            'company',
            'sector',
            'subsector',
            'address',
            'latitude',
            'longitude',
            'timezone',
            'asset_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'asset_count', 'full_name']
    
    def get_asset_count(self, obj):
        """Retorna o número de ativos ativos neste site."""
        return obj.assets.filter(status__in=['OPERATIONAL', 'WARNING', 'MAINTENANCE']).count()


class AssetListSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para listagem de Assets.
    
    Usado em endpoints de listagem para reduzir payload.
    Não inclui especificações JSON completas.
    """
    
    site_name = serializers.CharField(source='site.name', read_only=True)
    device_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Asset
        fields = [
            'id',
            'tag',
            'name',
            'site',
            'site_name',
            'asset_type',
            'status',
            'health_score',
            'device_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'device_count']
    
    def get_device_count(self, obj):
        """Retorna o número de dispositivos conectados a este ativo."""
        return obj.devices.count()


class AssetSerializer(serializers.ModelSerializer):
    """
    Serializer completo para o modelo Asset.
    
    Campos adicionais:
        - site_name: Nome do site (read-only)
        - full_location: Localização completa (read-only)
        - device_count: Número de dispositivos (read-only)
        - sensor_count: Número total de sensores (read-only)
    
    Campos read-only:
        - id, site_name, full_location, device_count, sensor_count,
          health_score, created_at, updated_at
    """
    
    site_name = serializers.CharField(source='site.name', read_only=True)
    full_location = serializers.CharField(read_only=True)
    device_count = serializers.SerializerMethodField()
    sensor_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Asset
        fields = [
            'id',
            'tag',
            'name',
            'site',
            'site_name',
            'full_location',
            'asset_type',
            'asset_type_other',
            'manufacturer',
            'model',
            'serial_number',
            'location_description',
            'installation_date',
            'last_maintenance',
            'status',
            'health_score',
            'specifications',
            'device_count',
            'sensor_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id', 'site_name', 'full_location', 'device_count', 
            'sensor_count', 'health_score', 'created_at', 'updated_at'
        ]
    
    def get_device_count(self, obj):
        """Retorna o número de dispositivos conectados a este ativo."""
        return obj.devices.count()
    
    def get_sensor_count(self, obj):
        """Retorna o número total de sensores em todos os dispositivos."""
        return Sensor.objects.filter(device__asset=obj).count()
    
    def validate_tag(self, value):
        """Valida que a tag é única (case-insensitive)."""
        if value:
            value = value.upper()
            # Verifica se já existe (excluindo o próprio objeto em updates)
            queryset = Asset.objects.filter(tag=value)
            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise serializers.ValidationError(
                    f"Asset com tag '{value}' já existe."
                )
        return value
    
    def validate(self, data):
        """Validações adicionais do modelo."""
        # Valida datas
        if 'installation_date' in data and 'last_maintenance' in data:
            if data['last_maintenance'] and data['installation_date']:
                if data['last_maintenance'] < data['installation_date']:
                    raise serializers.ValidationError({
                        'last_maintenance': 'Data de manutenção não pode ser anterior à instalação.'
                    })
        return data


class DeviceListSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para listagem de Devices.
    
    Usado em endpoints de listagem para reduzir payload.
    """
    
    asset_tag = serializers.CharField(source='asset.tag', read_only=True)
    sensor_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Device
        fields = [
            'id',
            'name',
            'serial_number',
            'asset',
            'asset_tag',
            'device_type',
            'status',
            'sensor_count',
            'last_seen',
            'created_at',
        ]
        read_only_fields = ['id', 'sensor_count', 'created_at']
    
    def get_sensor_count(self, obj):
        """Retorna o número de sensores neste dispositivo."""
        return obj.sensors.count()


class DeviceSerializer(serializers.ModelSerializer):
    """
    Serializer completo para o modelo Device.
    
    Campos adicionais:
        - asset_tag: Tag do ativo (read-only)
        - asset_name: Nome do ativo (read-only)
        - site_name: Nome do site (read-only)
        - sensor_count: Número de sensores (read-only)
    
    Campos read-only:
        - id, asset_tag, asset_name, site_name, is_online, 
          sensor_count, last_seen, created_at, updated_at
    """
    
    asset_tag = serializers.CharField(source='asset.tag', read_only=True)
    asset_name = serializers.CharField(source='asset.name', read_only=True)
    site_name = serializers.CharField(source='asset.site.name', read_only=True)
    sensor_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Device
        fields = [
            'id',
            'name',
            'serial_number',
            'asset',
            'asset_tag',
            'asset_name',
            'site_name',
            'device_type',
            'mqtt_client_id',
            'status',
            'firmware_version',
            'last_seen',
            'sensor_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id', 'asset_tag', 'asset_name', 'site_name',
            'sensor_count', 'last_seen', 'created_at', 'updated_at'
        ]
    
    def get_sensor_count(self, obj):
        """Retorna o número de sensores neste dispositivo."""
        return obj.sensors.count()
    
    def validate_serial_number(self, value):
        """Valida que o serial number é único."""
        if value:
            queryset = Device.objects.filter(serial_number=value)
            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise serializers.ValidationError(
                    f"Device com serial number '{value}' já existe."
                )
        return value
    
    def validate_mqtt_client_id(self, value):
        """Valida que o mqtt_client_id é único."""
        if value:
            queryset = Device.objects.filter(mqtt_client_id=value)
            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise serializers.ValidationError(
                    f"Device com MQTT Client ID '{value}' já existe."
                )
        return value


class SensorListSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para listagem de Sensors.
    
    Usado em endpoints de listagem para reduzir payload.
    """
    
    device_name = serializers.CharField(source='device.name', read_only=True)
    asset_tag = serializers.CharField(source='device.asset.tag', read_only=True)
    
    class Meta:
        model = Sensor
        fields = [
            'id',
            'tag',
            'device',
            'device_name',
            'asset_tag',
            'metric_type',
            'unit',
            'is_online',
            'last_value',
            'last_reading_at',
            'created_at',
        ]
        read_only_fields = ['id', 'is_online', 'last_reading_at', 'created_at']


class SensorSerializer(serializers.ModelSerializer):
    """
    Serializer completo para o modelo Sensor.
    
    Campos adicionais:
        - device_name: Nome do dispositivo (read-only)
        - device_serial: Serial do dispositivo (read-only)
        - asset_tag: Tag do ativo (read-only)
        - asset_name: Nome do ativo (read-only)
        - site_name: Nome do site (read-only)
        - availability: Percentual de disponibilidade (read-only)
    
    Campos read-only:
        - id, device_name, device_serial, asset_tag, asset_name, site_name,
          is_online, last_reading, availability, created_at, updated_at
    """
    
    device_name = serializers.CharField(source='device.name', read_only=True)
    device_serial = serializers.CharField(source='device.serial_number', read_only=True)
    asset_tag = serializers.CharField(source='device.asset.tag', read_only=True)
    asset_name = serializers.CharField(source='device.asset.name', read_only=True)
    site_name = serializers.CharField(source='device.asset.site.name', read_only=True)
    availability = serializers.SerializerMethodField()
    
    class Meta:
        model = Sensor
        fields = [
            'id',
            'tag',
            'device',
            'device_name',
            'device_serial',
            'asset_tag',
            'asset_name',
            'site_name',
            'metric_type',
            'unit',
            'thresholds',
            'is_online',
            'last_value',
            'last_reading_at',
            'availability',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id', 'device_name', 'device_serial', 'asset_tag', 'asset_name',
            'site_name', 'is_online', 'last_reading_at', 'availability',
            'created_at', 'updated_at'
        ]
    
    def get_availability(self, obj):
        """
        Calcula a disponibilidade do sensor nos últimos 30 dias.
        
        Retorna um percentual baseado no número de leituras esperadas
        vs recebidas. Se não houver leituras, retorna None.
        """
        # TODO: Implementar cálculo real quando integrar com TelemetryReading
        # Por enquanto, retorna um mock baseado em is_online
        if obj.last_reading_at:
            from django.utils import timezone
            from datetime import timedelta
            
            # Se teve leitura nas últimas 24h, considera boa disponibilidade
            if timezone.now() - obj.last_reading_at < timedelta(days=1):
                return 98.5
            elif timezone.now() - obj.last_reading_at < timedelta(days=7):
                return 85.0
            else:
                return 50.0
        return None
    
    def validate(self, data):
        """Validações adicionais do modelo."""
        # Valida unique_together (device, metric_type)
        if 'device' in data and 'metric_type' in data:
            queryset = Sensor.objects.filter(
                device=data['device'],
                metric_type=data['metric_type']
            )
            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise serializers.ValidationError({
                    'metric_type': f"Sensor com metric_type '{data['metric_type']}' "
                                  f"já existe neste dispositivo."
                })
        return data


class SensorBulkCreateSerializer(serializers.Serializer):
    """
    Serializer para criação em massa de sensores.
    
    Usado para criar múltiplos sensores de uma vez via POST /api/devices/{id}/sensors/bulk/
    
    Exemplo de payload:
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
    """
    
    sensors = SensorSerializer(many=True)
    
    def create(self, validated_data):
        """Cria múltiplos sensores."""
        device = self.context.get('device')
        if not device:
            raise serializers.ValidationError("Device não fornecido no contexto.")
        
        sensors_data = validated_data.get('sensors', [])
        sensors = []
        
        for sensor_data in sensors_data:
            sensor_data['device'] = device
            sensor = Sensor.objects.create(**sensor_data)
            sensors.append(sensor)
        
        return sensors
