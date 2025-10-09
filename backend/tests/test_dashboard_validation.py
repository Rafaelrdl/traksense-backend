"""
Testes de validação de DashboardConfig - JSON Schema v1

Valida que o campo json de DashboardConfig segue o schema v1:
- schema: 'v1' (obrigatório)
- layout: string (obrigatório)
- panels: array de objetos com type e title (obrigatório)
- Painéis suportados: timeseries, status, timeline, kpi, button

Autor: TrakSense Team
Data: 2025-12-12 (Fase R)
"""

import pytest
from django.core.exceptions import ValidationError
from apps.tenancy.models import Client, Domain
from apps.devices.models import Device, DeviceTemplate
from apps.dashboards.models import DashboardConfig


@pytest.mark.django_db(transaction=True)
class TestDashboardConfigValidation:
    """Testes de validação JSON Schema para DashboardConfig"""

    @pytest.fixture
    def tenant(self):
        """Fixture: Cria tenant de teste"""
        client = Client.objects.create(
            schema_name='test_validation',
            name='Test Validation Tenant'
        )
        Domain.objects.create(
            tenant=client,
            domain='test-validation.localhost',
            is_primary=True
        )
        return client

    @pytest.fixture
    def device_template(self, tenant):
        """Fixture: Cria DeviceTemplate de teste"""
        with tenant:
            return DeviceTemplate.objects.create(
                code='test-device',
                name='Test Device',
                version=1,
                description='Device for validation tests'
            )

    @pytest.fixture
    def device(self, tenant, device_template):
        """Fixture: Cria Device de teste"""
        with tenant:
            return Device.objects.create(
                template=device_template,
                name='Test Device Instance',
                mqtt_topic='test/device/01'
            )

    def test_valid_dashboard_config_minimal(self, tenant, device):
        """Teste: DashboardConfig com JSON mínimo válido"""
        with tenant:
            config_json = {
                "schema": "v1",
                "layout": "cards-2col",
                "panels": []
            }

            config = DashboardConfig(
                device=device,
                template_version=0,
                json=config_json
            )

            # Deve validar sem erros
            config.full_clean()
            config.save()

            assert config.json == config_json

    def test_valid_dashboard_config_full(self, tenant, device):
        """Teste: DashboardConfig com JSON completo válido"""
        with tenant:
            config_json = {
                "schema": "v1",
                "layout": "grid",
                "panels": [
                    {
                        "type": "kpi",
                        "title": "Temperatura",
                        "point": "temperature"
                    },
                    {
                        "type": "status",
                        "title": "Estado",
                        "point": "state",
                        "mappings": {
                            "ON": "Ligado",
                            "OFF": "Desligado"
                        }
                    },
                    {
                        "type": "timeseries",
                        "title": "Histórico Temperatura",
                        "point": "temperature",
                        "agg": "1m",
                        "yUnit": "°C"
                    },
                    {
                        "type": "timeline",
                        "title": "Eventos",
                        "points": ["state", "fault"]
                    },
                    {
                        "type": "button",
                        "title": "Resetar Falha",
                        "op": "reset_fault",
                        "params": {"ack": True}
                    }
                ]
            }

            config = DashboardConfig(
                device=device,
                template_version=1,
                json=config_json
            )

            # Deve validar sem erros
            config.full_clean()
            config.save()

            assert len(config.json['panels']) == 5

    def test_invalid_schema_missing(self, tenant, device):
        """Teste: JSON sem campo 'schema' (obrigatório)"""
        with tenant:
            config_json = {
                "layout": "cards-2col",
                "panels": []
            }

            config = DashboardConfig(
                device=device,
                template_version=0,
                json=config_json
            )

            # Deve falhar na validação
            with pytest.raises(ValidationError) as exc_info:
                config.full_clean()

            assert 'json' in exc_info.value.message_dict
            assert "'schema' is a required property" in str(exc_info.value)

    def test_invalid_schema_wrong_value(self, tenant, device):
        """Teste: schema com valor diferente de 'v1'"""
        with tenant:
            config_json = {
                "schema": "v2",  # Inválido! Deve ser 'v1'
                "layout": "cards-2col",
                "panels": []
            }

            config = DashboardConfig(
                device=device,
                template_version=0,
                json=config_json
            )

            # Deve falhar na validação
            with pytest.raises(ValidationError) as exc_info:
                config.full_clean()

            assert 'json' in exc_info.value.message_dict
            assert "is not valid under any of the given schemas" in str(exc_info.value) or "'v2' was expected" in str(exc_info.value)

    def test_invalid_layout_missing(self, tenant, device):
        """Teste: JSON sem campo 'layout' (obrigatório)"""
        with tenant:
            config_json = {
                "schema": "v1",
                "panels": []
            }

            config = DashboardConfig(
                device=device,
                template_version=0,
                json=config_json
            )

            # Deve falhar na validação
            with pytest.raises(ValidationError) as exc_info:
                config.full_clean()

            assert 'json' in exc_info.value.message_dict
            assert "'layout' is a required property" in str(exc_info.value)

    def test_invalid_panels_missing(self, tenant, device):
        """Teste: JSON sem campo 'panels' (obrigatório)"""
        with tenant:
            config_json = {
                "schema": "v1",
                "layout": "cards-2col"
            }

            config = DashboardConfig(
                device=device,
                template_version=0,
                json=config_json
            )

            # Deve falhar na validação
            with pytest.raises(ValidationError) as exc_info:
                config.full_clean()

            assert 'json' in exc_info.value.message_dict
            assert "'panels' is a required property" in str(exc_info.value)

    def test_invalid_panel_missing_type(self, tenant, device):
        """Teste: Painel sem campo 'type' (obrigatório)"""
        with tenant:
            config_json = {
                "schema": "v1",
                "layout": "cards-2col",
                "panels": [
                    {
                        "title": "Temperatura"  # Falta 'type'
                    }
                ]
            }

            config = DashboardConfig(
                device=device,
                template_version=0,
                json=config_json
            )

            # Deve falhar na validação
            with pytest.raises(ValidationError) as exc_info:
                config.full_clean()

            assert 'json' in exc_info.value.message_dict
            assert "'type' is a required property" in str(exc_info.value)

    def test_invalid_panel_missing_title(self, tenant, device):
        """Teste: Painel sem campo 'title' (obrigatório)"""
        with tenant:
            config_json = {
                "schema": "v1",
                "layout": "cards-2col",
                "panels": [
                    {
                        "type": "kpi"  # Falta 'title'
                    }
                ]
            }

            config = DashboardConfig(
                device=device,
                template_version=0,
                json=config_json
            )

            # Deve falhar na validação
            with pytest.raises(ValidationError) as exc_info:
                config.full_clean()

            assert 'json' in exc_info.value.message_dict
            assert "'title' is a required property" in str(exc_info.value)

    def test_invalid_panel_type_unsupported(self, tenant, device):
        """Teste: Painel com tipo não suportado"""
        with tenant:
            config_json = {
                "schema": "v1",
                "layout": "cards-2col",
                "panels": [
                    {
                        "type": "invalid_type",  # Tipo não existe no enum
                        "title": "Teste"
                    }
                ]
            }

            config = DashboardConfig(
                device=device,
                template_version=0,
                json=config_json
            )

            # Deve falhar na validação
            with pytest.raises(ValidationError) as exc_info:
                config.full_clean()

            assert 'json' in exc_info.value.message_dict
            assert "is not one of" in str(exc_info.value) or "is not valid under any" in str(exc_info.value)

    def test_invalid_agg_value(self, tenant, device):
        """Teste: Painel timeseries com valor de 'agg' inválido"""
        with tenant:
            config_json = {
                "schema": "v1",
                "layout": "cards-2col",
                "panels": [
                    {
                        "type": "timeseries",
                        "title": "Temperatura",
                        "point": "temperature",
                        "agg": "invalid_agg",  # Deve ser: raw, 1m, 5m, 1h
                        "yUnit": "°C"
                    }
                ]
            }

            config = DashboardConfig(
                device=device,
                template_version=0,
                json=config_json
            )

            # Deve falhar na validação
            with pytest.raises(ValidationError) as exc_info:
                config.full_clean()

            assert 'json' in exc_info.value.message_dict
            assert "is not one of" in str(exc_info.value) or "is not valid under any" in str(exc_info.value)

    def test_additional_properties_allowed_in_panels(self, tenant, device):
        """Teste: Painéis podem ter propriedades adicionais (additionalProperties: true)"""
        with tenant:
            config_json = {
                "schema": "v1",
                "layout": "cards-2col",
                "panels": [
                    {
                        "type": "kpi",
                        "title": "Temperatura",
                        "point": "temperature",
                        "custom_field": "allowed"  # Propriedade extra permitida
                    }
                ]
            }

            config = DashboardConfig(
                device=device,
                template_version=0,
                json=config_json
            )

            # Deve validar sem erros (additionalProperties: true nos panels)
            config.full_clean()
            config.save()

            assert config.json['panels'][0]['custom_field'] == 'allowed'

    def test_additional_properties_not_allowed_in_root(self, tenant, device):
        """Teste: Root do JSON NÃO permite propriedades adicionais (additionalProperties: false)"""
        with tenant:
            config_json = {
                "schema": "v1",
                "layout": "cards-2col",
                "panels": [],
                "extra_field": "not_allowed"  # Propriedade extra NÃO permitida no root
            }

            config = DashboardConfig(
                device=device,
                template_version=0,
                json=config_json
            )

            # Deve falhar na validação
            with pytest.raises(ValidationError) as exc_info:
                config.full_clean()

            assert 'json' in exc_info.value.message_dict
            assert "Additional properties are not allowed" in str(exc_info.value)

