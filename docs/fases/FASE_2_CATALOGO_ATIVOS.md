# 📦 FASE 2: CATÁLOGO DE ATIVOS - PLANEJAMENTO E IMPLEMENTAÇÃO

**Objetivo:** Implementar a estrutura hierárquica Sites → Assets → Devices → Sensors no backend Django

**Duração estimada:** 1.5 semanas

---

## 🎯 ANÁLISE DO FRONTEND EXISTENTE

### Estrutura Atual no Frontend (`traksense-hvac-monit`)

#### 1. **Tipos e Interfaces** (`src/types/hvac.ts`)

```typescript
export interface HVACAsset {
  id: string;
  tag: string;  // Ex: "AHU-001", "CH-001"
  type: 'AHU' | 'Chiller' | 'VRF' | 'RTU' | 'Boiler' | 'CoolingTower';
  
  // Localização (hierarquia atual)
  location: string;      // Ex: "Casa de Máquinas - Torre A"
  company?: string;      // Ex: "TrakSense Healthcare"
  sector?: string;       // Ex: "Climatização", "Centro Cirúrgico"
  subsector?: string;    // Ex: "Chillers", "Sala 01"
  
  // Status e métricas
  healthScore: number;           // 0-100
  powerConsumption: number;      // kWh/day
  status: 'OK' | 'Maintenance' | 'Stopped' | 'Alert';
  operatingHours: number;
  lastMaintenance: Date;
  
  // Especificações técnicas
  specifications: {
    capacity?: number;           // tons ou kW
    voltage?: number;
    maxCurrent?: number;
    refrigerant?: string;
    brand?: string;              // Marca (ex: Carrier, Trane)
    model?: string;              // Modelo
    serialNumber?: string;
    equipmentType?: EquipmentType;  // Tipo expandido (15 opções)
    equipmentTypeOther?: string;    // Texto livre quando OTHER
  };
}

export type EquipmentType =
  | 'CHILLER'
  | 'AHU'            // Unidade de Tratamento de Ar
  | 'FAN_COIL'
  | 'PUMP'
  | 'BOILER'
  | 'COOLING_TOWER'
  | 'VRF'
  | 'RTU'
  | 'VALVE'
  | 'SENSOR'
  | 'CONTROLLER'
  | 'FILTER'
  | 'DUCT'
  | 'METER'
  | 'OTHER';

export interface Sensor {
  id: string;
  tag: string;           // Ex: "AHU-001-TEMP-SUPPLY"
  assetId: string;       // Relacionamento com HVACAsset
  type: SensorType;      // 30+ tipos de sensores
  unit: string;          // Ex: "°C", "kW", "Pa"
  location: string;
  online: boolean;
  lastReading: SensorReading | null;
  availability: number;  // porcentagem
  min?: number;
  max?: number;
  setpoint?: number;
}

export type SensorType = 
  | 'temp_supply' | 'temp_return' | 'temp_external'
  | 'humidity' | 'dewpoint'
  | 'pressure_suction' | 'pressure_discharge'
  | 'dp_filter' | 'dp_fan'
  | 'airflow' | 'rpm_fan'
  | 'voltage' | 'current' | 'power_kw' | 'energy_kwh'
  | 'power_factor' | 'superheat' | 'subcooling'
  | 'vibration' | 'noise'
  | 'compressor_state' | 'valve_position'
  | 'cop' | 'eer'
  | 'maintenance' | 'maintenance_reminder';
```

#### 2. **Modal de Adicionar Ativo** (`src/components/assets/AddAssetDialog.tsx`)

**Funcionalidades implementadas:**

- **3 Abas de cadastro:**
  1. **Informações Básicas:** Tag*, Tipo de Equipamento*, Marca, Modelo, Capacidade, Número de Série
  2. **Localização:** Empresa*, Setor*, Subsetor, Localização Descritiva
  3. **Especificações:** Tensão, Corrente, Refrigerante

- **Validações:**
  - Tag obrigatória
  - Empresa e Setor obrigatórios
  - Tipo "OTHER" requer texto customizado (min 3 caracteres)
  - Geração automática de `location` baseado em "Empresa - Setor - Subsetor"

- **Campos gerados automaticamente no frontend:**
  - `id`: `asset-${Date.now()}-${Math.random()}`
  - `healthScore`: 100 (novo ativo)
  - `powerConsumption`: 0
  - `status`: 'OK'
  - `operatingHours`: 0
  - `lastMaintenance`: Date.now()

#### 3. **Página de Ativos** (`src/components/pages/AssetsPage.tsx`)

**Funcionalidades:**

- **Filtros avançados:**
  - Busca por tag, localização ou equipamento
  - Filtro por tipo de equipamento (dropdown com 15 tipos)
  - Filtro por status (all/OK/Maintenance/Stopped/Alert)

- **Visualização:**
  - Cards de resumo (Total, Ativos, Em Manutenção, Críticos)
  - Tabela com: Tag, Equipamento, Localização, Status, Ações
  - Navegação para detalhes do ativo

- **Store Zustand:** `useAppStore`
  - `assets: HVACAsset[]`
  - `addAsset(asset): void`
  - `setSelectedAsset(id): void`

#### 4. **Sensores** (`src/components/pages/SensorsPage.tsx`)

**Funcionalidades:**

- **Grid de sensores** com:
  - Tag do sensor
  - Equipamento associado (link clicável para navegar ao ativo)
  - Tipo de sensor
  - Última leitura
  - Status (online/offline)
  - Disponibilidade

- **Relacionamento Sensor → Asset:**
  - Cada sensor tem `assetId`
  - Interface permite navegar do sensor para o ativo
  - `onNavigateToEquipment(equipmentId)`

#### 5. **Store de Equipamentos** (`src/store/equipment.ts`)

**Dados atuais (mock):**

```typescript
{
  id: 'eq-001',
  name: 'Chiller Principal Torre A',
  tag: 'CH-001',
  assetTypeId: 'Chiller',
  iotDeviceId: 'iot-chiller-001',     // 🎯 Relacionamento com Device IoT
  location: 'Casa de Máquinas - Torre A',
  company: 'TrakSense Healthcare',
  sector: 'Climatização',
  subsector: 'Chillers',
  status: 'active',
  createdAt: Date
}
```

---

## 🏗️ ARQUITETURA BACKEND PROPOSTA

### Hierarquia de Models

```
┌──────────────────────────────────────────────────────────┐
│  Site (Localização Física)                              │
│  - name, address, coordinates, timezone                 │
└─────────────┬────────────────────────────────────────────┘
              │ 1:N
              ▼
┌──────────────────────────────────────────────────────────┐
│  Asset (Equipamento HVAC)                               │
│  - tag, type, manufacturer, model, site_id              │
│  - specifications (JSON: capacity, voltage, etc.)       │
└─────────────┬────────────────────────────────────────────┘
              │ 1:N
              ▼
┌──────────────────────────────────────────────────────────┐
│  Device (Dispositivo IoT)                               │
│  - name, serial, asset_id, mqtt_client_id               │
│  - device_type, firmware_version, status                │
└─────────────┬────────────────────────────────────────────┘
              │ 1:N
              ▼
┌──────────────────────────────────────────────────────────┐
│  Sensor (Canal de Telemetria)                           │
│  - device_id, metric_type, unit                         │
│  - thresholds (JSON: min, max, setpoint)                │
└──────────────────────────────────────────────────────────┘
              │ 1:N
              ▼
┌──────────────────────────────────────────────────────────┐
│  TelemetryReading (apps/ingest/models.py - já existe)  │
│  - device_id, sensor_id, timestamp, value               │
└──────────────────────────────────────────────────────────┘
```

---

## 📋 CHECKLIST DE IMPLEMENTAÇÃO

### **Semana 2 - Models e APIs**

#### ✅ Preparação

- [x] Analisar estrutura frontend (HVACAsset, Sensor, Equipment)
- [x] Mapear campos existentes vs necessários
- [x] Definir hierarquia Sites → Assets → Devices → Sensors
- [ ] Criar app `assets` no backend

#### 🏗️ 1. Model: Site

**Arquivo:** `apps/assets/models.py`

```python
from django.db import models
from apps.tenants.models import TenantAwareModel

class Site(TenantAwareModel):
    """
    Site/Localização física onde os equipamentos estão instalados.
    
    Exemplo:
    - Hospital Central - Unidade Brasília
    - Data Center São Paulo
    - Shopping Center Norte
    """
    name = models.CharField('Nome do Site', max_length=200)
    address = models.TextField('Endereço', blank=True)
    
    # Coordenadas geográficas
    latitude = models.DecimalField(
        'Latitude', 
        max_digits=9, 
        decimal_places=6, 
        null=True, 
        blank=True
    )
    longitude = models.DecimalField(
        'Longitude', 
        max_digits=9, 
        decimal_places=6, 
        null=True, 
        blank=True
    )
    
    timezone = models.CharField(
        'Fuso Horário',
        max_length=50,
        default='America/Sao_Paulo',
        help_text='IANA timezone (ex: America/Sao_Paulo)'
    )
    
    # Campos de organização (mapeamento do frontend)
    company = models.CharField('Empresa', max_length=200, blank=True)
    sector = models.CharField('Setor', max_length=200, blank=True)
    subsector = models.CharField('Subsetor', max_length=200, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField('Ativo', default=True)
    
    class Meta:
        db_table = 'sites'
        ordering = ['name']
        verbose_name = 'Site'
        verbose_name_plural = 'Sites'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['company', 'sector']),
        ]
    
    def __str__(self):
        return self.name
```

**Tarefas:**
- [ ] Criar model `Site`
- [ ] Criar migration
- [ ] Registrar no admin
- [ ] Adicionar testes unitários

#### 🔧 2. Model: Asset

```python
class Asset(TenantAwareModel):
    """
    Asset/Equipamento HVAC (ex: Chiller, AHU, VRF).
    
    Mapeamento direto com HVACAsset do frontend.
    """
    ASSET_TYPE_CHOICES = [
        ('CHILLER', 'Chiller'),
        ('AHU', 'Air Handling Unit'),
        ('FAN_COIL', 'Fan Coil'),
        ('PUMP', 'Bomba'),
        ('BOILER', 'Caldeira'),
        ('COOLING_TOWER', 'Torre de Resfriamento'),
        ('VRF', 'VRF (Variable Refrigerant Flow)'),
        ('RTU', 'Roof Top Unit'),
        ('VALVE', 'Válvula'),
        ('SENSOR', 'Sensor'),
        ('CONTROLLER', 'Controlador'),
        ('FILTER', 'Filtro'),
        ('DUCT', 'Duto'),
        ('METER', 'Medidor'),
        ('OTHER', 'Outro'),
    ]
    
    STATUS_CHOICES = [
        ('OK', 'Operacional'),
        ('MAINTENANCE', 'Em Manutenção'),
        ('STOPPED', 'Parado'),
        ('ALERT', 'Alerta'),
    ]
    
    # Identificação
    tag = models.CharField(
        'Tag',
        max_length=100,
        unique=True,
        help_text='Identificador único (ex: AHU-001, CH-001)'
    )
    name = models.CharField('Nome', max_length=200, blank=True)
    
    # Relacionamento
    site = models.ForeignKey(
        Site,
        on_delete=models.PROTECT,
        related_name='assets',
        verbose_name='Site'
    )
    
    # Tipo e características
    asset_type = models.CharField(
        'Tipo de Equipamento',
        max_length=20,
        choices=ASSET_TYPE_CHOICES
    )
    asset_type_other = models.CharField(
        'Outro Tipo (texto livre)',
        max_length=200,
        blank=True,
        help_text='Usado quando asset_type = OTHER'
    )
    
    manufacturer = models.CharField('Fabricante', max_length=200, blank=True)
    model = models.CharField('Modelo', max_length=200, blank=True)
    serial_number = models.CharField('Número de Série', max_length=200, blank=True)
    
    # Status
    status = models.CharField(
        'Status',
        max_length=20,
        choices=STATUS_CHOICES,
        default='OK'
    )
    health_score = models.IntegerField(
        'Health Score',
        default=100,
        help_text='0-100'
    )
    
    # Localização dentro do site
    location_description = models.CharField(
        'Descrição da Localização',
        max_length=500,
        blank=True,
        help_text='Ex: 3º Andar - Ala Leste'
    )
    
    # Especificações técnicas (JSON)
    specifications = models.JSONField(
        'Especificações',
        default=dict,
        blank=True,
        help_text='''
        {
          "capacity": 500,
          "capacity_unit": "TR",
          "voltage": 380,
          "max_current": 100,
          "refrigerant": "R-410A",
          "power_consumption": 0,
          "operating_hours": 0
        }
        '''
    )
    
    # Datas
    installation_date = models.DateField('Data de Instalação', null=True, blank=True)
    last_maintenance = models.DateTimeField('Última Manutenção', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField('Ativo', default=True)
    
    class Meta:
        db_table = 'assets'
        ordering = ['tag']
        verbose_name = 'Asset'
        verbose_name_plural = 'Assets'
        indexes = [
            models.Index(fields=['tag']),
            models.Index(fields=['site', 'asset_type']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.tag} - {self.get_asset_type_display()}"
    
    @property
    def full_location(self):
        """Retorna localização completa: Site + descrição"""
        parts = [self.site.name]
        if self.location_description:
            parts.append(self.location_description)
        return ' - '.join(parts)
```

**Tarefas:**
- [ ] Criar model `Asset`
- [ ] Criar migration
- [ ] Registrar no admin com filtros (site, tipo, status)
- [ ] Adicionar testes unitários
- [ ] Criar método `calculate_health_score()` (futuro)

#### 📡 3. Model: Device

```python
class Device(TenantAwareModel):
    """
    Device/Dispositivo IoT físico conectado ao equipamento.
    
    Um Asset pode ter múltiplos Devices (ex: controlador + medidor de energia).
    """
    DEVICE_TYPE_CHOICES = [
        ('CONTROLLER', 'Controlador Principal'),
        ('ENERGY_METER', 'Medidor de Energia'),
        ('SENSOR_HUB', 'Hub de Sensores'),
        ('GATEWAY', 'Gateway IoT'),
        ('OTHER', 'Outro'),
    ]
    
    STATUS_CHOICES = [
        ('ONLINE', 'Online'),
        ('OFFLINE', 'Offline'),
        ('ERROR', 'Erro'),
        ('MAINTENANCE', 'Manutenção'),
    ]
    
    # Identificação
    name = models.CharField('Nome', max_length=200)
    serial_number = models.CharField(
        'Número de Série',
        max_length=200,
        unique=True
    )
    
    # Relacionamento
    asset = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,
        related_name='devices',
        verbose_name='Asset'
    )
    
    # Conectividade MQTT
    mqtt_client_id = models.CharField(
        'Client ID MQTT',
        max_length=200,
        unique=True,
        help_text='Usado para pub/sub no EMQX'
    )
    
    # Tipo e informações
    device_type = models.CharField(
        'Tipo de Dispositivo',
        max_length=20,
        choices=DEVICE_TYPE_CHOICES,
        default='CONTROLLER'
    )
    firmware_version = models.CharField(
        'Versão do Firmware',
        max_length=50,
        blank=True
    )
    
    # Status e conectividade
    status = models.CharField(
        'Status',
        max_length=20,
        choices=STATUS_CHOICES,
        default='OFFLINE'
    )
    last_seen = models.DateTimeField('Última Conexão', null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField('Ativo', default=True)
    
    class Meta:
        db_table = 'devices'
        ordering = ['name']
        verbose_name = 'Device'
        verbose_name_plural = 'Devices'
        indexes = [
            models.Index(fields=['mqtt_client_id']),
            models.Index(fields=['asset', 'status']),
            models.Index(fields=['serial_number']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.mqtt_client_id})"
```

**Tarefas:**
- [ ] Criar model `Device`
- [ ] Criar migration
- [ ] Registrar no admin
- [ ] Adicionar testes unitários
- [ ] Implementar método `update_status()` via MQTT

#### 📊 4. Model: Sensor

```python
class Sensor(TenantAwareModel):
    """
    Sensor/Canal de telemetria de um Device.
    
    Um Device pode ter múltiplos Sensors (ex: temp_supply, temp_return, humidity).
    """
    SENSOR_TYPE_CHOICES = [
        # Temperatura
        ('temp_supply', 'Temperatura de Suprimento'),
        ('temp_return', 'Temperatura de Retorno'),
        ('temp_external', 'Temperatura Externa'),
        ('temp_setpoint', 'Setpoint de Temperatura'),
        
        # Umidade
        ('humidity', 'Umidade Relativa'),
        ('dewpoint', 'Ponto de Orvalho'),
        
        # Pressão
        ('pressure_suction', 'Pressão de Sucção'),
        ('pressure_discharge', 'Pressão de Descarga'),
        ('dp_filter', 'Diferencial de Pressão - Filtro'),
        ('dp_fan', 'Diferencial de Pressão - Ventilador'),
        
        # Fluxo
        ('airflow', 'Vazão de Ar'),
        
        # Rotação
        ('rpm_fan', 'Rotação do Ventilador'),
        
        # Elétrico
        ('voltage', 'Tensão'),
        ('current', 'Corrente'),
        ('power_kw', 'Potência (kW)'),
        ('energy_kwh', 'Energia (kWh)'),
        ('power_factor', 'Fator de Potência'),
        
        # Refrigeração
        ('superheat', 'Superaquecimento'),
        ('subcooling', 'Sub-resfriamento'),
        
        # Vibração e ruído
        ('vibration', 'Vibração'),
        ('noise', 'Ruído'),
        
        # Estados
        ('compressor_state', 'Estado do Compressor'),
        ('valve_position', 'Posição da Válvula'),
        
        # Performance
        ('cop', 'Coeficiente de Performance'),
        ('eer', 'Energy Efficiency Ratio'),
        
        # Manutenção
        ('maintenance', 'Status de Manutenção'),
        ('maintenance_reminder', 'Lembrete de Manutenção'),
    ]
    
    # Identificação
    tag = models.CharField(
        'Tag',
        max_length=200,
        help_text='Ex: AHU-001-TEMP-SUPPLY'
    )
    
    # Relacionamento
    device = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,
        related_name='sensors',
        verbose_name='Device'
    )
    
    # Tipo e unidade
    metric_type = models.CharField(
        'Tipo de Métrica',
        max_length=50,
        choices=SENSOR_TYPE_CHOICES
    )
    unit = models.CharField(
        'Unidade',
        max_length=20,
        help_text='Ex: °C, kW, Pa, %'
    )
    
    # Thresholds (JSON)
    thresholds = models.JSONField(
        'Limites',
        default=dict,
        blank=True,
        help_text='''
        {
          "min": 18.0,
          "max": 26.0,
          "setpoint": 22.0,
          "warning_low": 19.0,
          "warning_high": 25.0,
          "critical_low": 16.0,
          "critical_high": 28.0
        }
        '''
    )
    
    # Status
    is_online = models.BooleanField('Online', default=False)
    availability = models.FloatField(
        'Disponibilidade (%)',
        default=0.0,
        help_text='Porcentagem de uptime'
    )
    
    # Última leitura (cache)
    last_value = models.FloatField('Última Leitura', null=True, blank=True)
    last_reading_at = models.DateTimeField('Data da Última Leitura', null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField('Ativo', default=True)
    
    class Meta:
        db_table = 'sensors'
        ordering = ['tag']
        verbose_name = 'Sensor'
        verbose_name_plural = 'Sensors'
        unique_together = [('device', 'metric_type')]
        indexes = [
            models.Index(fields=['device', 'metric_type']),
            models.Index(fields=['tag']),
            models.Index(fields=['is_online']),
        ]
    
    def __str__(self):
        return f"{self.tag} ({self.get_metric_type_display()})"
    
    @property
    def asset(self):
        """Atalho para acessar o Asset através do Device"""
        return self.device.asset
```

**Tarefas:**
- [ ] Criar model `Sensor`
- [ ] Criar migration
- [ ] Registrar no admin
- [ ] Adicionar testes unitários
- [ ] Implementar método `update_last_reading()` (usado pelo ingest)

---

### 📡 5. Endpoints REST API

#### **Serializers** (`apps/assets/serializers.py`)

```python
from rest_framework import serializers
from .models import Site, Asset, Device, Sensor

class SiteSerializer(serializers.ModelSerializer):
    asset_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Site
        fields = [
            'id', 'name', 'address', 'latitude', 'longitude',
            'timezone', 'company', 'sector', 'subsector',
            'is_active', 'created_at', 'updated_at', 'asset_count'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_asset_count(self, obj):
        return obj.assets.filter(is_active=True).count()


class AssetSerializer(serializers.ModelSerializer):
    site_name = serializers.CharField(source='site.name', read_only=True)
    device_count = serializers.SerializerMethodField()
    full_location = serializers.ReadOnlyField()
    
    class Meta:
        model = Asset
        fields = [
            'id', 'tag', 'name', 'site', 'site_name',
            'asset_type', 'asset_type_other',
            'manufacturer', 'model', 'serial_number',
            'status', 'health_score',
            'location_description', 'full_location',
            'specifications',
            'installation_date', 'last_maintenance',
            'is_active', 'created_at', 'updated_at',
            'device_count'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'full_location']
    
    def get_device_count(self, obj):
        return obj.devices.filter(is_active=True).count()


class DeviceSerializer(serializers.ModelSerializer):
    asset_tag = serializers.CharField(source='asset.tag', read_only=True)
    sensor_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Device
        fields = [
            'id', 'name', 'serial_number',
            'asset', 'asset_tag',
            'mqtt_client_id', 'device_type',
            'firmware_version', 'status',
            'last_seen', 'is_active',
            'created_at', 'updated_at',
            'sensor_count'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_sensor_count(self, obj):
        return obj.sensors.filter(is_active=True).count()


class SensorSerializer(serializers.ModelSerializer):
    device_name = serializers.CharField(source='device.name', read_only=True)
    asset_tag = serializers.CharField(source='device.asset.tag', read_only=True)
    
    class Meta:
        model = Sensor
        fields = [
            'id', 'tag', 'device', 'device_name', 'asset_tag',
            'metric_type', 'unit', 'thresholds',
            'is_online', 'availability',
            'last_value', 'last_reading_at',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_value', 'last_reading_at']
```

#### **ViewSets** (`apps/assets/views.py`)

```python
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Site, Asset, Device, Sensor
from .serializers import (
    SiteSerializer, AssetSerializer,
    DeviceSerializer, SensorSerializer
)

class SiteViewSet(viewsets.ModelViewSet):
    """
    CRUD para Sites.
    
    list: GET /api/sites/
    create: POST /api/sites/
    retrieve: GET /api/sites/{id}/
    update: PUT /api/sites/{id}/
    partial_update: PATCH /api/sites/{id}/
    destroy: DELETE /api/sites/{id}/
    """
    queryset = Site.objects.all()
    serializer_class = SiteSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['company', 'sector', 'is_active']
    search_fields = ['name', 'address', 'company', 'sector']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']


class AssetViewSet(viewsets.ModelViewSet):
    """
    CRUD para Assets.
    
    Filtros disponíveis:
    - ?site=1
    - ?asset_type=CHILLER
    - ?status=OK
    - ?search=AHU
    """
    queryset = Asset.objects.select_related('site').all()
    serializer_class = AssetSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['site', 'asset_type', 'status', 'is_active']
    search_fields = ['tag', 'name', 'manufacturer', 'model']
    ordering_fields = ['tag', 'health_score', 'created_at']
    ordering = ['tag']
    
    @action(detail=True, methods=['get'])
    def devices(self, request, pk=None):
        """GET /api/assets/{id}/devices/ - Lista devices do asset"""
        asset = self.get_object()
        devices = asset.devices.filter(is_active=True)
        serializer = DeviceSerializer(devices, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def sensors(self, request, pk=None):
        """GET /api/assets/{id}/sensors/ - Lista todos os sensors do asset"""
        asset = self.get_object()
        sensors = Sensor.objects.filter(
            device__asset=asset,
            is_active=True
        ).select_related('device')
        serializer = SensorSerializer(sensors, many=True)
        return Response(serializer.data)


class DeviceViewSet(viewsets.ModelViewSet):
    """
    CRUD para Devices.
    
    Filtros disponíveis:
    - ?asset=1
    - ?device_type=CONTROLLER
    - ?status=ONLINE
    """
    queryset = Device.objects.select_related('asset').all()
    serializer_class = DeviceSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['asset', 'device_type', 'status', 'is_active']
    search_fields = ['name', 'serial_number', 'mqtt_client_id']
    ordering_fields = ['name', 'last_seen', 'created_at']
    ordering = ['name']
    
    @action(detail=True, methods=['get'])
    def sensors(self, request, pk=None):
        """GET /api/devices/{id}/sensors/ - Lista sensors do device"""
        device = self.get_object()
        sensors = device.sensors.filter(is_active=True)
        serializer = SensorSerializer(sensors, many=True)
        return Response(serializer.data)


class SensorViewSet(viewsets.ModelViewSet):
    """
    CRUD para Sensors.
    
    Filtros disponíveis:
    - ?device=1
    - ?metric_type=temp_supply
    - ?is_online=true
    """
    queryset = Sensor.objects.select_related('device', 'device__asset').all()
    serializer_class = SensorSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['device', 'metric_type', 'is_online', 'is_active']
    search_fields = ['tag']
    ordering_fields = ['tag', 'last_reading_at', 'created_at']
    ordering = ['tag']
```

#### **URLs** (`apps/assets/urls.py`)

```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SiteViewSet, AssetViewSet, DeviceViewSet, SensorViewSet

router = DefaultRouter()
router.register(r'sites', SiteViewSet, basename='site')
router.register(r'assets', AssetViewSet, basename='asset')
router.register(r'devices', DeviceViewSet, basename='device')
router.register(r'sensors', SensorViewSet, basename='sensor')

urlpatterns = [
    path('', include(router.urls)),
]
```

**Tarefas:**
- [ ] Criar serializers (Site, Asset, Device, Sensor)
- [ ] Criar viewsets com CRUD completo
- [ ] Adicionar filtros (DjangoFilterBackend)
- [ ] Adicionar busca (SearchFilter)
- [ ] Criar custom actions (ex: `/api/assets/{id}/sensors/`)
- [ ] Configurar URLs no router
- [ ] Adicionar testes de API (APITestCase)

---

## 🔗 INTEGRAÇÃO COM APPS EXISTENTES

### 1. **Integração com `apps/ingest`**

**Atualizar `TelemetryReading` para usar novos models:**

```python
# apps/ingest/models.py (modificar)

from apps.assets.models import Device, Sensor

class TelemetryReading(models.Model):
    # ANTES:
    # device_id = models.CharField(max_length=100)
    # sensor_id = models.CharField(max_length=100)
    
    # DEPOIS:
    device = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,
        related_name='readings'
    )
    sensor = models.ForeignKey(
        Sensor,
        on_delete=models.CASCADE,
        related_name='readings'
    )
    
    timestamp = models.DateTimeField()
    value = models.FloatField()
    quality = models.CharField(max_length=20, default='good')
    
    class Meta:
        db_table = 'telemetry_readings'
        indexes = [
            models.Index(fields=['sensor', 'timestamp']),
            models.Index(fields=['device', 'timestamp']),
        ]
```

**Tarefas:**
- [ ] Criar migration para adicionar ForeignKeys
- [ ] Manter campos legados `device_id` e `sensor_id` por compatibilidade (DEPRECATED)
- [ ] Atualizar view de ingestão para salvar em ambos os formatos
- [ ] Adicionar signal para atualizar `Sensor.last_value` e `Sensor.last_reading_at`

### 2. **Integração com EMQX (apps/ops)**

**Conectar MQTT client_id com Device:**

```python
# Quando EMQX autentica um device:
# 1. Buscar Device por mqtt_client_id
# 2. Atualizar Device.status = 'ONLINE'
# 3. Atualizar Device.last_seen = now()

# apps/ops/emqx_handlers.py (novo)
from apps.assets.models import Device

def on_device_connected(client_id):
    """Callback quando device conecta no EMQX"""
    try:
        device = Device.objects.get(mqtt_client_id=client_id)
        device.status = 'ONLINE'
        device.last_seen = timezone.now()
        device.save(update_fields=['status', 'last_seen'])
    except Device.DoesNotExist:
        logger.warning(f"Device {client_id} conectou mas não existe no banco")

def on_device_disconnected(client_id):
    """Callback quando device desconecta do EMQX"""
    try:
        device = Device.objects.get(mqtt_client_id=client_id)
        device.status = 'OFFLINE'
        device.save(update_fields=['status'])
    except Device.DoesNotExist:
        pass
```

**Tarefas:**
- [ ] Criar handlers para eventos EMQX (connect/disconnect)
- [ ] Adicionar management command `sync_device_status` (task periódica)
- [ ] Atualizar dashboard de status de devices

---

## 🧪 TESTES

### Estrutura de Testes

```python
# apps/assets/tests/test_models.py
from django.test import TestCase
from apps.assets.models import Site, Asset, Device, Sensor

class SiteModelTests(TestCase):
    def test_create_site(self):
        site = Site.objects.create(
            name='Hospital Central',
            address='Rua X, 123',
            timezone='America/Sao_Paulo'
        )
        self.assertEqual(str(site), 'Hospital Central')

class AssetModelTests(TestCase):
    def test_asset_full_location(self):
        site = Site.objects.create(name='Hospital')
        asset = Asset.objects.create(
            tag='AHU-001',
            site=site,
            asset_type='AHU',
            location_description='3º Andar'
        )
        self.assertEqual(asset.full_location, 'Hospital - 3º Andar')

# apps/assets/tests/test_api.py
from rest_framework.test import APITestCase
from rest_framework import status

class AssetAPITests(APITestCase):
    def setUp(self):
        # Criar tenant, user, autenticar
        pass
    
    def test_list_assets(self):
        response = self.client.get('/api/assets/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_create_asset(self):
        data = {
            'tag': 'CH-001',
            'site': self.site.id,
            'asset_type': 'CHILLER',
            'manufacturer': 'Carrier',
            'model': '30XA-1002'
        }
        response = self.client.post('/api/assets/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
```

**Tarefas:**
- [ ] Testes de models (criação, validação, relacionamentos)
- [ ] Testes de API (CRUD, filtros, paginação)
- [ ] Testes de permissions (tenant isolation)
- [ ] Testes de serializers

---

## 📄 DOCUMENTAÇÃO

### Admin Dashboard

```python
# apps/assets/admin.py
from django.contrib import admin
from .models import Site, Asset, Device, Sensor

@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ['name', 'company', 'sector', 'timezone', 'asset_count', 'is_active']
    list_filter = ['is_active', 'company', 'sector']
    search_fields = ['name', 'address']
    
    def asset_count(self, obj):
        return obj.assets.count()

@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ['tag', 'site', 'asset_type', 'status', 'health_score', 'is_active']
    list_filter = ['asset_type', 'status', 'site', 'is_active']
    search_fields = ['tag', 'name', 'manufacturer', 'model']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ['name', 'asset', 'mqtt_client_id', 'status', 'last_seen']
    list_filter = ['device_type', 'status', 'is_active']
    search_fields = ['name', 'serial_number', 'mqtt_client_id']

@admin.register(Sensor)
class SensorAdmin(admin.ModelAdmin):
    list_display = ['tag', 'device', 'metric_type', 'is_online', 'last_reading_at']
    list_filter = ['metric_type', 'is_online', 'is_active']
    search_fields = ['tag']
```

---

## 🎯 ENTREGÁVEIS FASE 2

### ✅ Checklist Final

- [ ] **Models criados:**
  - [ ] Site (name, address, coordinates, timezone)
  - [ ] Asset (tag, type, manufacturer, model, site_id)
  - [ ] Device (name, serial, asset_id, mqtt_client_id)
  - [ ] Sensor (device_id, metric_type, unit, thresholds)

- [ ] **Migrations aplicadas:**
  - [ ] `0001_initial.py` para app `assets`
  - [ ] Migração de dados legados (se houver)

- [ ] **APIs REST funcionais:**
  - [ ] GET/POST /api/sites/
  - [ ] GET/POST/PUT/PATCH/DELETE /api/assets/
  - [ ] GET/POST/PUT/PATCH/DELETE /api/devices/
  - [ ] GET/POST/PUT/PATCH/DELETE /api/sensors/
  - [ ] Custom actions: `/api/assets/{id}/devices/`, `/api/assets/{id}/sensors/`

- [ ] **Filtros implementados:**
  - [ ] Filtro por site, tipo, status em Assets
  - [ ] Busca por tag, nome, fabricante
  - [ ] Ordenação por múltiplos campos

- [ ] **Integrações:**
  - [ ] TelemetryReading → Sensor (ForeignKey)
  - [ ] EMQX → Device (status sync)
  - [ ] Signals para atualizar `last_reading`

- [ ] **Testes:**
  - [ ] Testes unitários de models (cobertura > 80%)
  - [ ] Testes de API (todos os endpoints)
  - [ ] Testes de tenant isolation

- [ ] **Documentação:**
  - [ ] Admin configurado e funcional
  - [ ] README da app `assets`
  - [ ] Exemplos de uso da API

- [ ] **Frontend Integration Ready:**
  - [ ] Endpoints compatíveis com tipos TypeScript do frontend
  - [ ] Campos mapeados: `HVACAsset`, `Sensor`, `Equipment`
  - [ ] JSON schema para `specifications` e `thresholds`

---

## 🔄 PRÓXIMAS FASES

### FASE 3: Ingestão de Telemetria em Tempo Real
- Conectar EMQX → Backend → TimescaleDB
- Agregação de dados (1min, 5min, 1h)
- Cálculo de KPIs em tempo real

### FASE 4: Alertas e Regras
- Engine de regras baseada em thresholds
- Notificações (email, push, webhook)
- Histórico de alertas

---

## 📝 NOTAS IMPORTANTES

1. **Tenant Isolation:**
   - Todos os models herdam de `TenantAwareModel`
   - Usar `connection.set_tenant(tenant)` em management commands
   - Filtrar queries por tenant automaticamente

2. **Performance:**
   - Usar `select_related('site', 'asset')` em queries
   - Indexar campos de busca (tag, mqtt_client_id)
   - Considerar cache Redis para status de devices

3. **Compatibilidade com Frontend:**
   - Manter campos como `company`, `sector`, `subsector` no Site
   - Suportar campo legado `location` em Asset
   - JSON `specifications` segue estrutura do `HVACAsset` do frontend

4. **Migration Strategy:**
   - Criar models novos
   - Migrar dados legados (se houver)
   - Manter campos deprecated por 2 versões
   - Remover campos legados na Fase 3

---

## 🚀 COMEÇAR IMPLEMENTAÇÃO

**Próximo passo:**
```bash
cd traksense-backend
docker exec -it traksense-api python manage.py startapp assets
```

Vamos começar pela implementação dos models! 🎯
