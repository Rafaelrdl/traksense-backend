"""
Services - Devices App

Serviços de lógica de negócio para dispositivos IoT.
Contém funções para provisionamento automático de Points e DashboardConfig.

IMPORTANTE: Sempre chamar provision_device_from_template() após criar um Device
            para gerar automaticamente Points e DashboardConfig.

Autor: TrakSense Team
Data: 2025-10-07 (Fase 2)
"""

from django.db import transaction
from .models import Point, PointTemplate, Device


@transaction.atomic
def provision_device_from_template(
    device: Device,
    contracted_points: list[str] | None = None
):
    """
    Provisiona um Device criando Points e DashboardConfig automaticamente.
    
    Esta função deve ser chamada após criar um Device para:
    1. Instanciar Points a partir dos PointTemplates do DeviceTemplate
    2. Gerar o DashboardConfig filtrado por pontos contratados
    
    Args:
        device: Instância de Device a ser provisionada
        contracted_points: Lista opcional de nomes de pontos contratados.
                          Se None, todos os pontos são contratados.
                          Se lista, apenas pontos nesta lista são marcados como contratados.
    
    Comportamento:
        - Busca todos os PointTemplates do DeviceTemplate do device
        - Filtra por contracted_points se fornecido
        - Cria Points (bulk_create com ignore_conflicts para idempotência)
        - Chama dashboards.services.instantiate_dashboard_config()
    
    Exemplo:
        from devices.models import Device, DeviceTemplate
        from devices.services import provision_device_from_template
        
        template = DeviceTemplate.objects.get(code='inverter_v1_parsec', version=1)
        device = Device.objects.create(
            template=template,
            name='Inversor 01 - Sala A'
        )
        
        # Provisionar todos os pontos
        provision_device_from_template(device)
        
        # Ou provisionar apenas alguns pontos
        provision_device_from_template(device, contracted_points=['status', 'fault'])
    """
    
    # 1) Criar Points a partir dos PointTemplates
    query = PointTemplate.objects.filter(device_template=device.template)
    
    if contracted_points is not None:
        query = query.filter(name__in=contracted_points)
    
    points_to_create = []
    for pt in query:
        # Determinar se o ponto está contratado
        is_contracted = (
            contracted_points is None or
            pt.name in contracted_points
        )
        
        points_to_create.append(Point(
            device=device,
            template=pt,
            name=pt.name,
            label=pt.label,
            unit=pt.unit,
            polarity=pt.polarity,
            limits=pt.default_limits or {},
            is_contracted=is_contracted,
        ))
    
    # Bulk create com ignore_conflicts para idempotência
    # (se rodar duas vezes, não duplica)
    Point.objects.bulk_create(points_to_create, ignore_conflicts=True)
    
    # 2) Gerar DashboardConfig
    from apps.dashboards.services import instantiate_dashboard_config
    instantiate_dashboard_config(device)
