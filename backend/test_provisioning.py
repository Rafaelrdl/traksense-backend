"""
Script de teste de provisionamento automático
Valida que Device cria Points e DashboardConfig automaticamente
"""
from apps.devices.models import Device, DeviceTemplate, Point
from apps.devices.services import provision_device_from_template
from apps.dashboards.models import DashboardConfig

# Buscar template
template = DeviceTemplate.objects.get(code='inverter_v1_parsec', version=1)
print(f'📋 Template encontrado: {template.code} v{template.version}')

# Criar device
device = Device.objects.create(
    template=template,
    name='Inversor 01 - Teste Validação'
)
print(f'✅ Device criado: ID={device.pk} | Nome={device.name}')

# Provisionar
provision_device_from_template(device)
print('🔧 Provisionamento executado')

# Verificar Points
points = Point.objects.filter(device=device)
print(f'\n✅ Points criados: {points.count()}')
for p in points:
    template_name = p.template.name if p.template else p.name
    print(f'  - {template_name} (contracted={p.is_contracted})')

# Verificar DashboardConfig
try:
    config = DashboardConfig.objects.get(device=device)
    print(f'\n✅ DashboardConfig criado')
    panels = config.json.get('panels', [])
    print(f'  Total de painéis: {len(panels)}')
    for panel in panels:
        print(f'    - {panel.get("type")}: {panel.get("title")}')
except DashboardConfig.DoesNotExist:
    print('\n❌ DashboardConfig NÃO criado')

print('\n🎉 Teste de provisionamento concluído!')
