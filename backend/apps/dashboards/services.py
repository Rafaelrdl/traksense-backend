"""
Services - Dashboards App

Serviços de lógica de negócio para dashboards.
Contém funções para instanciar DashboardConfig a partir de DashboardTemplate.

IMPORTANTE: Esta função é chamada automaticamente por devices.services.provision_device_from_template()

Autor: TrakSense Team
Data: 2025-10-07 (Fase 2)
"""

from django.db import transaction
from .models import DashboardTemplate, DashboardConfig


@transaction.atomic
def instantiate_dashboard_config(device):
    """
    Instancia um DashboardConfig para um Device a partir de seu DashboardTemplate.
    
    Esta função:
    1. Busca o DashboardTemplate mais recente do DeviceTemplate do device
    2. Filtra os painéis para incluir apenas pontos contratados
    3. Cria ou atualiza o DashboardConfig do device
    
    Filtragem de Painéis:
        - Painéis com "point": mantém apenas se o ponto existe e está contratado
        - Painéis com "points": mantém apenas pontos contratados, remove painel se vazio
        - Painéis sem referência a pontos: sempre mantém
    
    Args:
        device: Instância de Device para o qual gerar o DashboardConfig
    
    Comportamento:
        - Se não há DashboardTemplate, cria config vazio mas válido
        - Se há template, filtra painéis por pontos contratados
        - Usa update_or_create para idempotência
    
    Exemplo:
        from devices.models import Device
        from dashboards.services import instantiate_dashboard_config
        
        device = Device.objects.get(name='Inversor 01')
        instantiate_dashboard_config(device)
        
        # Agora device.dashboard_config.json contém os painéis filtrados
    """
    
    # Buscar DashboardTemplate mais recente do DeviceTemplate do device
    dtpl = (DashboardTemplate.objects
            .filter(device_template=device.template)
            .order_by("-version")
            .first())
    
    if not dtpl:
        # Sem template de dashboard - criar config vazio mas válido
        cfg = {
            "schema": "v1",
            "layout": "cards-2col",
            "panels": []
        }
        template_version = 0
    else:
        # Copiar estrutura base do template
        base = dtpl.json
        
        # Buscar pontos contratados do device
        # Importar aqui para evitar importação circular
        from apps.devices.models import Point
        contracted = set(
            Point.objects
            .filter(device=device, is_contracted=True)
            .values_list("name", flat=True)
        )
        
        # Filtrar painéis por pontos contratados
        panels = []
        for panel in base.get("panels", []):
            # Caso 1: painel com campo "point" (ponto único)
            if "point" in panel:
                if panel["point"] not in contracted:
                    # Ponto não contratado - pular painel
                    continue
            
            # Caso 2: painel com campo "points" (lista de pontos)
            if "points" in panel:
                # Filtrar apenas pontos contratados
                contracted_panel_points = [
                    p for p in panel["points"]
                    if p in contracted
                ]
                
                if not contracted_panel_points:
                    # Nenhum ponto contratado - pular painel
                    continue
                
                # Atualizar painel com apenas pontos contratados
                panel = {**panel, "points": contracted_panel_points}
            
            # Adicionar painel (passou pelos filtros)
            panels.append(panel)
        
        # Montar config final
        cfg = {
            "schema": "v1",
            "layout": base.get("layout", "cards-2col"),
            "panels": panels
        }
        template_version = dtpl.version
    
    # Criar ou atualizar DashboardConfig (idempotente)
    DashboardConfig.objects.update_or_create(
        device=device,
        defaults={
            "template_version": template_version,
            "json": cfg
        }
    )
