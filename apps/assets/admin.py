"""
Django Admin configuration para app Assets.

Registra os 4 models principais com interfaces otimizadas:
- Site: Hierarquia organizacional e localização física
- Asset: Equipamentos HVAC
- Device: Dispositivos IoT conectados
- Sensor: Canais de telemetria
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import Site, Asset, Device, Sensor


@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    """Admin interface para Sites (localizações físicas)"""
    
    list_display = [
        'name',
        'company',
        'sector',
        'timezone',
        'asset_count',
        'is_active',
        'created_at'
    ]
    
    list_filter = [
        'is_active',
        'company',
        'sector',
        'timezone',
        'created_at'
    ]
    
    search_fields = [
        'name',
        'address',
        'company',
        'sector',
        'subsector'
    ]
    
    readonly_fields = [
        'created_at',
        'updated_at',
        'full_name',
        'asset_count'
    ]
    
    fieldsets = (
        ('Identificação', {
            'fields': ('name', 'full_name')
        }),
        ('Hierarquia Organizacional', {
            'fields': ('company', 'sector', 'subsector'),
            'description': 'Estrutura organizacional do frontend'
        }),
        ('Localização', {
            'fields': ('address', 'latitude', 'longitude', 'timezone')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'asset_count'),
            'classes': ('collapse',)
        }),
    )
    
    def asset_count(self, obj):
        """Conta quantos assets ativos estão neste site"""
        count = obj.assets.filter(is_active=True).count()
        return format_html('<b>{}</b> ativos', count)
    asset_count.short_description = '# Assets'


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    """Admin interface para Assets (equipamentos HVAC)"""
    
    list_display = [
        'tag',
        'name_display',
        'asset_type',
        'site',
        'manufacturer',
        'status_badge',
        'health_score',
        'device_count',
        'is_active'
    ]
    
    list_filter = [
        'asset_type',
        'status',
        'site',
        'manufacturer',
        'is_active',
        'created_at'
    ]
    
    search_fields = [
        'tag',
        'name',
        'manufacturer',
        'model',
        'serial_number',
        'site__name'
    ]
    
    readonly_fields = [
        'created_at',
        'updated_at',
        'full_location',
        'device_count'
    ]
    
    autocomplete_fields = ['site']
    
    fieldsets = (
        ('Identificação', {
            'fields': ('tag', 'name', 'site', 'full_location')
        }),
        ('Tipo de Equipamento', {
            'fields': ('asset_type', 'asset_type_other')
        }),
        ('Fabricante', {
            'fields': ('manufacturer', 'model', 'serial_number')
        }),
        ('Status Operacional', {
            'fields': ('status', 'health_score')
        }),
        ('Localização no Site', {
            'fields': ('location_description',)
        }),
        ('Especificações Técnicas (JSON)', {
            'fields': ('specifications',),
            'classes': ('collapse',),
            'description': 'JSON com capacity, voltage, refrigerant, etc.'
        }),
        ('Datas', {
            'fields': ('installation_date', 'last_maintenance')
        }),
        ('Controles', {
            'fields': ('is_active',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'device_count'),
            'classes': ('collapse',)
        }),
    )
    
    def name_display(self, obj):
        """Exibe nome ou tag se nome estiver vazio"""
        return obj.name if obj.name else format_html('<i style="color: gray;">(sem nome)</i>')
    name_display.short_description = 'Nome'
    
    def status_badge(self, obj):
        """Exibe status com badge colorido"""
        colors = {
            'OK': 'green',
            'MAINTENANCE': 'orange',
            'STOPPED': 'red',
            'ALERT': 'red'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="padding: 3px 8px; border-radius: 3px; background: {}; color: white; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def device_count(self, obj):
        """Conta quantos devices ativos estão conectados"""
        count = obj.devices.filter(is_active=True).count()
        return format_html('<b>{}</b> devices', count)
    device_count.short_description = '# Devices'


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    """Admin interface para Devices (dispositivos IoT)"""
    
    list_display = [
        'name',
        'mqtt_client_id',
        'asset',
        'device_type',
        'status_badge',
        'last_seen_display',
        'sensor_count',
        'is_active'
    ]
    
    list_filter = [
        'device_type',
        'status',
        'is_active',
        'asset__site',
        'created_at'
    ]
    
    search_fields = [
        'name',
        'serial_number',
        'mqtt_client_id',
        'asset__tag',
        'asset__name'
    ]
    
    readonly_fields = [
        'created_at',
        'updated_at',
        'last_seen',
        'sensor_count'
    ]
    
    autocomplete_fields = ['asset']
    
    fieldsets = (
        ('Identificação', {
            'fields': ('name', 'serial_number', 'asset')
        }),
        ('Conectividade MQTT/EMQX', {
            'fields': ('mqtt_client_id', 'status', 'last_seen')
        }),
        ('Tipo e Informações', {
            'fields': ('device_type', 'firmware_version')
        }),
        ('Controles', {
            'fields': ('is_active',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'sensor_count'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        """Exibe status com badge colorido"""
        colors = {
            'ONLINE': 'green',
            'OFFLINE': 'gray',
            'ERROR': 'red',
            'MAINTENANCE': 'orange'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="padding: 3px 8px; border-radius: 3px; background: {}; color: white; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def last_seen_display(self, obj):
        """Formata última conexão"""
        if not obj.last_seen:
            return format_html('<i style="color: gray;">Nunca</i>')
        
        from django.utils import timezone
        from django.utils.timesince import timesince
        
        delta = timezone.now() - obj.last_seen
        if delta.total_seconds() < 300:  # < 5 minutos
            return format_html('<span style="color: green;">● {} atrás</span>', timesince(obj.last_seen))
        elif delta.total_seconds() < 3600:  # < 1 hora
            return format_html('<span style="color: orange;">● {} atrás</span>', timesince(obj.last_seen))
        else:
            return format_html('<span style="color: red;">● {} atrás</span>', timesince(obj.last_seen))
    last_seen_display.short_description = 'Última Conexão'
    
    def sensor_count(self, obj):
        """Conta quantos sensores ativos estão conectados"""
        count = obj.sensors.filter(is_active=True).count()
        return format_html('<b>{}</b> sensores', count)
    sensor_count.short_description = '# Sensores'


@admin.register(Sensor)
class SensorAdmin(admin.ModelAdmin):
    """Admin interface para Sensors (canais de telemetria)"""
    
    list_display = [
        'tag',
        'device',
        'asset_tag',
        'metric_type',
        'unit',
        'online_status',
        'last_value_display',
        'last_reading_display',
        'availability',
        'is_active'
    ]
    
    list_filter = [
        'metric_type',
        'is_online',
        'is_active',
        'device__asset__site',
        'created_at'
    ]
    
    search_fields = [
        'tag',
        'device__name',
        'device__mqtt_client_id',
        'device__asset__tag'
    ]
    
    readonly_fields = [
        'created_at',
        'updated_at',
        'last_value',
        'last_reading_at',
        'asset_tag'
    ]
    
    autocomplete_fields = ['device']
    
    fieldsets = (
        ('Identificação', {
            'fields': ('tag', 'device', 'asset_tag')
        }),
        ('Tipo de Medição', {
            'fields': ('metric_type', 'unit')
        }),
        ('Thresholds (JSON)', {
            'fields': ('thresholds',),
            'description': 'JSON com limites: min, max, setpoint, warning_low, etc.'
        }),
        ('Status', {
            'fields': ('is_online', 'availability')
        }),
        ('Última Leitura (Cache)', {
            'fields': ('last_value', 'last_reading_at'),
            'classes': ('collapse',)
        }),
        ('Controles', {
            'fields': ('is_active',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def asset_tag(self, obj):
        """Exibe tag do asset através do device"""
        return obj.device.asset.tag
    asset_tag.short_description = 'Asset'
    
    def online_status(self, obj):
        """Exibe status online/offline com ícone"""
        if obj.is_online:
            return format_html('<span style="color: green; font-size: 16px;">● Online</span>')
        else:
            return format_html('<span style="color: red; font-size: 16px;">● Offline</span>')
    online_status.short_description = 'Conectividade'
    
    def last_value_display(self, obj):
        """Formata última leitura com unidade"""
        if obj.last_value is None:
            return format_html('<i style="color: gray;">—</i>')
        return format_html('<b>{:.2f}</b> {}', obj.last_value, obj.unit)
    last_value_display.short_description = 'Última Leitura'
    
    def last_reading_display(self, obj):
        """Formata timestamp da última leitura"""
        if not obj.last_reading_at:
            return format_html('<i style="color: gray;">Nunca</i>')
        
        from django.utils import timezone
        from django.utils.timesince import timesince
        
        delta = timezone.now() - obj.last_reading_at
        if delta.total_seconds() < 300:  # < 5 minutos
            return format_html('<span style="color: green;">{} atrás</span>', timesince(obj.last_reading_at))
        elif delta.total_seconds() < 3600:  # < 1 hora
            return format_html('<span style="color: orange;">{} atrás</span>', timesince(obj.last_reading_at))
        else:
            return format_html('<span style="color: red;">{} atrás</span>', timesince(obj.last_reading_at))
    last_reading_display.short_description = 'Última Atualização'

