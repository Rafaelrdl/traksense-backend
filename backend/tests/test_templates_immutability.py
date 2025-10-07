"""
Tests - Device Template Immutability

Testa as regras de imutabilidade de templates (version + superseded_by).

Cenários testados:
-----------------
1. Criar DeviceTemplate e verificar versionamento
2. Criar nova versão e marcar antiga como supersedida
3. Tentar alterar template depreciado

Autor: TrakSense Team
Data: 2025-10-07 (Fase 2)
"""

import pytest
from django.core.exceptions import ValidationError
from apps.devices.models import DeviceTemplate, PointTemplate, PointType, Polarity


@pytest.mark.django_db(transaction=True)
class TestTemplateImmutability:
    """Testes de imutabilidade de templates"""
    
    def test_create_device_template_v1(self):
        """Teste: Criar DeviceTemplate versão 1"""
        
        template = DeviceTemplate.objects.create(
            code='test_device',
            name='Test Device v1',
            version=1,
            description='Template de teste'
        )
        
        assert template.code == 'test_device'
        assert template.version == 1
        assert not template.is_deprecated
        assert template.superseded_by is None
    
    def test_create_new_version_and_deprecate_old(self):
        """Teste: Criar nova versão e depreciar antiga"""
        
        # Criar versão 1
        v1 = DeviceTemplate.objects.create(
            code='test_device',
            name='Test Device v1',
            version=1
        )
        
        # Criar versão 2
        v2 = DeviceTemplate.objects.create(
            code='test_device',
            name='Test Device v2',
            version=2
        )
        
        # Marcar v1 como supersedida por v2
        v1.superseded_by = v2
        v1.save()
        
        v1.refresh_from_db()
        
        assert v1.is_deprecated
        assert v1.superseded_by == v2
        assert not v2.is_deprecated
    
    def test_unique_constraint_code_version(self):
        """Teste: Constraint (code, version) é único"""
        
        DeviceTemplate.objects.create(
            code='test_device',
            name='Test Device v1',
            version=1
        )
        
        # Tentar criar outro com mesmo (code, version) deve falhar
        with pytest.raises(Exception):  # IntegrityError
            DeviceTemplate.objects.create(
                code='test_device',
                name='Test Device v1 duplicate',
                version=1
            )
    
    def test_point_template_validation_unit_only_numeric(self):
        """Teste: unit só permitido quando ptype=NUMERIC"""
        
        template = DeviceTemplate.objects.create(
            code='test_device',
            name='Test Device',
            version=1
        )
        
        # BOOL com unit deve falhar na validação
        pt = PointTemplate(
            device_template=template,
            name='test_point',
            label='Test Point',
            ptype=PointType.BOOL,
            unit='°C'  # INVÁLIDO: unit não permitido para BOOL
        )
        
        with pytest.raises(ValidationError) as exc_info:
            pt.full_clean()
        
        assert 'unit' in exc_info.value.message_dict
    
    def test_point_template_validation_enum_requires_values(self):
        """Teste: enum_values obrigatório quando ptype=ENUM"""
        
        template = DeviceTemplate.objects.create(
            code='test_device',
            name='Test Device',
            version=1
        )
        
        # ENUM sem enum_values deve falhar na validação
        pt = PointTemplate(
            device_template=template,
            name='test_point',
            label='Test Point',
            ptype=PointType.ENUM
            # enum_values faltando!
        )
        
        with pytest.raises(ValidationError) as exc_info:
            pt.full_clean()
        
        assert 'enum_values' in exc_info.value.message_dict
    
    def test_point_template_validation_hysteresis_non_negative(self):
        """Teste: hysteresis deve ser ≥ 0"""
        
        template = DeviceTemplate.objects.create(
            code='test_device',
            name='Test Device',
            version=1
        )
        
        # hysteresis negativo deve falhar na validação
        pt = PointTemplate(
            device_template=template,
            name='test_point',
            label='Test Point',
            ptype=PointType.NUMERIC,
            unit='°C',
            hysteresis=-1.0  # INVÁLIDO: negativo
        )
        
        with pytest.raises(ValidationError) as exc_info:
            pt.full_clean()
        
        assert 'hysteresis' in exc_info.value.message_dict
