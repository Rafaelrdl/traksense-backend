"""
Script de teste de validações de modelo
Valida que as regras de negócio estão sendo aplicadas corretamente
"""
from apps.devices.models import PointTemplate, PointType, DeviceTemplate
from django.core.exceptions import ValidationError

print("=== TESTE 1: BOOL não pode ter unit ===")
template = DeviceTemplate.objects.first()

# Tentar criar BOOL com unit (INVÁLIDO)
pt = PointTemplate(
    device_template=template,
    name='test_invalid_bool',
    label='Test Invalid Bool',
    ptype=PointType.BOOL,
    unit='°C'  # ❌ INVÁLIDO
)

try:
    pt.full_clean()
    print("❌ Validação NÃO funcionou (deveria ter falhado)")
except ValidationError as e:
    print("✅ Validação funcionou!")
    print(f"   Erro: {e.message_dict.get('unit', e.message_dict)}")

print("\n=== TESTE 2: ENUM requer enum_values ===")
pt2 = PointTemplate(
    device_template=template,
    name='test_enum_no_values',
    label='Test Enum No Values',
    ptype=PointType.ENUM
    # ❌ Sem enum_values
)

try:
    pt2.full_clean()
    print("❌ Validação NÃO funcionou (deveria ter falhado)")
except ValidationError as e:
    print("✅ Validação funcionou!")
    print(f"   Erro: {e.message_dict.get('enum_values', e.message_dict)}")

print("\n=== TESTE 3: ENUM com enum_values válido ===")
pt3 = PointTemplate(
    device_template=template,
    name='test_enum_valid',
    label='Test Enum Valid',
    ptype=PointType.ENUM,
    enum_values=['OPTION1', 'OPTION2', 'OPTION3']
)

try:
    pt3.full_clean()
    print("✅ Validação passou (enum_values correto)")
except ValidationError as e:
    print(f"❌ Erro inesperado: {e.message_dict}")

print("\n🎉 Testes de validação concluídos!")
