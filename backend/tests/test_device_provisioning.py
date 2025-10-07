"""
Tests - Device Provisioning

Testa o provisionamento automático de Device (Points + DashboardConfig).

Cenários testados:
-----------------
1. Criar Device e verificar que Points são gerados automaticamente
2. Verificar que DashboardConfig é gerado com JSON válido
3. Testar provisionamento parcial (contracted_points)
4. Verificar filtro de painéis por pontos contratados

Autor: TrakSense Team
Data: 2025-10-07 (Fase 2)
"""

import pytest
import json
from apps.devices.models import DeviceTemplate, PointTemplate, Device, Point, PointType, Polarity
from apps.dashboards.models import DashboardTemplate, DashboardConfig
from apps.devices.services import provision_device_from_template


@pytest.mark.django_db(transaction=True)
class TestDeviceProvisioning:
    """Testes de provisionamento de Device"""
    
    @pytest.fixture
    def device_template_with_points(self):
        """Fixture: DeviceTemplate com PointTemplates"""
        
        template = DeviceTemplate.objects.create(
            code='test_inverter',
            name='Test Inverter',
            version=1
        )
        
        # Criar PointTemplates
        PointTemplate.objects.create(
            device_template=template,
            name='status',
            label='Status',
            ptype=PointType.ENUM,
            enum_values=['RUN', 'STOP', 'FAULT']
        )
        
        PointTemplate.objects.create(
            device_template=template,
            name='fault',
            label='Fault',
            ptype=PointType.BOOL
        )
        
        PointTemplate.objects.create(
            device_template=template,
            name='rssi',
            label='RSSI',
            ptype=PointType.NUMERIC,
            unit='dBm'
        )
        
        return template
    
    @pytest.fixture
    def dashboard_template(self, device_template_with_points):
        """Fixture: DashboardTemplate"""
        
        dashboard_json = {
            "schema": "v1",
            "layout": "cards-2col",
            "panels": [
                {
                    "type": "status",
                    "title": "Estado",
                    "point": "status",
                    "mappings": {"RUN": "Rodando", "STOP": "Parado", "FAULT": "Falha"}
                },
                {
                    "type": "kpi",
                    "title": "Falhas",
                    "point": "fault"
                },
                {
                    "type": "timeseries",
                    "title": "RSSI",
                    "point": "rssi",
                    "agg": "1m",
                    "yUnit": "dBm"
                }
            ]
        }
        
        return DashboardTemplate.objects.create(
            device_template=device_template_with_points,
            schema='v1',
            version=1,
            json=dashboard_json
        )
    
    def test_provision_device_creates_points(self, device_template_with_points):
        """Teste: Provisionar Device cria Points automaticamente"""
        
        # Criar Device
        device = Device.objects.create(
            template=device_template_with_points,
            name='Test Device 01'
        )
        
        # Provisionar
        provision_device_from_template(device)
        
        # Verificar que Points foram criados
        points = Point.objects.filter(device=device)
        assert points.count() == 3
        
        point_names = set(points.values_list('name', flat=True))
        assert point_names == {'status', 'fault', 'rssi'}
        
        # Verificar que todos estão contratados
        assert all(p.is_contracted for p in points)
    
    def test_provision_device_with_contracted_points(self, device_template_with_points):
        """Teste: Provisionar apenas pontos contratados"""
        
        # Criar Device
        device = Device.objects.create(
            template=device_template_with_points,
            name='Test Device 02'
        )
        
        # Provisionar apenas 'status' e 'fault'
        provision_device_from_template(device, contracted_points=['status', 'fault'])
        
        # Verificar que apenas 2 pontos foram criados (contracted)
        contracted_points = Point.objects.filter(device=device, is_contracted=True)
        assert contracted_points.count() == 2
        
        contracted_names = set(contracted_points.values_list('name', flat=True))
        assert contracted_names == {'status', 'fault'}
    
    def test_provision_device_creates_dashboard_config(
        self,
        device_template_with_points,
        dashboard_template
    ):
        """Teste: Provisionar Device cria DashboardConfig"""
        
        # Criar Device
        device = Device.objects.create(
            template=device_template_with_points,
            name='Test Device 03'
        )
        
        # Provisionar
        provision_device_from_template(device)
        
        # Verificar que DashboardConfig foi criado
        config = DashboardConfig.objects.get(device=device)
        
        assert config.template_version == dashboard_template.version
        assert config.json['schema'] == 'v1'
        assert len(config.json['panels']) == 3  # Todos os painéis (todos os pontos contratados)
    
    def test_dashboard_config_filters_by_contracted_points(
        self,
        device_template_with_points,
        dashboard_template
    ):
        """Teste: DashboardConfig filtra painéis por pontos contratados"""
        
        # Criar Device
        device = Device.objects.create(
            template=device_template_with_points,
            name='Test Device 04'
        )
        
        # Provisionar apenas 'status' contratado
        provision_device_from_template(device, contracted_points=['status'])
        
        # Verificar DashboardConfig
        config = DashboardConfig.objects.get(device=device)
        
        # Deve ter apenas 1 painel (status), pois fault e rssi não estão contratados
        assert len(config.json['panels']) == 1
        assert config.json['panels'][0]['point'] == 'status'
    
    def test_provision_idempotent(self, device_template_with_points):
        """Teste: Provisionar duas vezes não duplica Points"""
        
        # Criar Device
        device = Device.objects.create(
            template=device_template_with_points,
            name='Test Device 05'
        )
        
        # Provisionar primeira vez
        provision_device_from_template(device)
        count_1 = Point.objects.filter(device=device).count()
        
        # Provisionar segunda vez
        provision_device_from_template(device)
        count_2 = Point.objects.filter(device=device).count()
        
        # Não deve duplicar
        assert count_1 == count_2 == 3
    
    def test_dashboard_config_without_template(self, device_template_with_points):
        """Teste: DashboardConfig criado mesmo sem DashboardTemplate"""
        
        # Criar Device (sem DashboardTemplate)
        device = Device.objects.create(
            template=device_template_with_points,
            name='Test Device 06'
        )
        
        # Provisionar
        provision_device_from_template(device)
        
        # Verificar que DashboardConfig foi criado com config vazio mas válido
        config = DashboardConfig.objects.get(device=device)
        
        assert config.template_version == 0
        assert config.json['schema'] == 'v1'
        assert config.json['panels'] == []
