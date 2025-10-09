"""
Migration: Adicionar DashboardTemplate para JE02

Cria dashboard template para inverter_je02_v1 com painéis:
- StatusPanel: visualização de status (RUN/STOP/FAULT)
- TimelinePanel: linha do tempo de status
- KpiPanel: contagem de falhas nas últimas 24h
- TimeseriesPanel: gráficos de rssi, var0, var1 com agg=1m
- ButtonPanel: "Reset Falha" (funcional apenas na Fase 6)

Schema: v1 (compatível com frontend React)

Autor: TrakSense Team
Data: 2025-10-08 (Fase D - JE02)
"""

from django.db import migrations
import uuid


def create_je02_dashboard_template(apps, schema_editor):
    """
    Cria DashboardTemplate para inverter_je02_v1.
    """
    DeviceTemplate = apps.get_model('templates', 'DeviceTemplate')
    DashboardTemplate = apps.get_model('templates', 'DashboardTemplate')
    
    # Buscar DeviceTemplate
    try:
        device_template = DeviceTemplate.objects.get(code='inverter_je02_v1')
    except DeviceTemplate.DoesNotExist:
        print("❌ DeviceTemplate 'inverter_je02_v1' não encontrado!")
        return
    
    # ==================================================================
    # Dashboard JSON (Schema v1)
    # ==================================================================
    
    dashboard_json = {
        "schema": "v1",
        "layout": {
            "type": "grid",
            "columns": 12,
            "gap": 16
        },
        "panels": [
            # ==========================================
            # 1. StatusPanel - Estado atual do inversor
            # ==========================================
            {
                "id": "status-panel",
                "type": "StatusPanel",
                "title": "Status do Inversor",
                "position": {"row": 0, "col": 0, "colSpan": 3, "rowSpan": 2},
                "config": {
                    "pointName": "status",
                    "colorMap": {
                        "RUN": "#22c55e",      # verde
                        "STOP": "#f59e0b",     # laranja
                        "FAULT": "#ef4444"     # vermelho
                    },
                    "iconMap": {
                        "RUN": "play-circle",
                        "STOP": "pause-circle",
                        "FAULT": "alert-triangle"
                    },
                    "refreshInterval": 5000  # 5 segundos
                }
            },
            
            # ==========================================
            # 2. KpiPanel - Contagem de falhas (24h)
            # ==========================================
            {
                "id": "fault-count-24h",
                "type": "KpiPanel",
                "title": "Falhas (24h)",
                "position": {"row": 0, "col": 3, "colSpan": 3, "rowSpan": 2},
                "config": {
                    "query": {
                        "pointName": "fault",
                        "aggregation": "count",
                        "filter": {"value": True},
                        "timeRange": "24h"
                    },
                    "format": {
                        "type": "number",
                        "decimals": 0
                    },
                    "thresholds": [
                        {"value": 0, "color": "#22c55e"},    # 0 falhas = verde
                        {"value": 1, "color": "#f59e0b"},    # 1+ falhas = laranja
                        {"value": 10, "color": "#ef4444"}    # 10+ falhas = vermelho
                    ]
                }
            },
            
            # ==========================================
            # 3. KpiPanel - RSSI atual (WiFi)
            # ==========================================
            {
                "id": "rssi-current",
                "type": "KpiPanel",
                "title": "Sinal WiFi (RSSI)",
                "position": {"row": 0, "col": 6, "colSpan": 3, "rowSpan": 2},
                "config": {
                    "query": {
                        "pointName": "rssi",
                        "aggregation": "last",
                        "timeRange": "5m"
                    },
                    "format": {
                        "type": "number",
                        "decimals": 0,
                        "unit": "dBm"
                    },
                    "thresholds": [
                        {"value": -85, "color": "#ef4444"},    # Crítico
                        {"value": -75, "color": "#f59e0b"},    # Fraco
                        {"value": -65, "color": "#22c55e"}     # Bom
                    ]
                }
            },
            
            # ==========================================
            # 4. ButtonPanel - Reset Falha (Fase 6)
            # ==========================================
            {
                "id": "reset-fault-button",
                "type": "ButtonPanel",
                "title": "Ações",
                "position": {"row": 0, "col": 9, "colSpan": 3, "rowSpan": 2},
                "config": {
                    "buttons": [
                        {
                            "id": "reset-fault",
                            "label": "Reset Falha",
                            "icon": "refresh-cw",
                            "variant": "primary",
                            "action": {
                                "type": "command",
                                "topic": "${topic_base}/cmd",
                                "payload": {"RELE": 1, "pulse_ms": 500}
                            },
                            "confirmMessage": "Enviar comando de reset para o inversor?",
                            "disabled": False,
                            "tooltip": "Funcionalidade disponível na Fase 6"
                        }
                    ]
                }
            },
            
            # ==========================================
            # 5. TimelinePanel - Histórico de status
            # ==========================================
            {
                "id": "status-timeline",
                "type": "TimelinePanel",
                "title": "Histórico de Status (24h)",
                "position": {"row": 2, "col": 0, "colSpan": 12, "rowSpan": 3},
                "config": {
                    "pointName": "status",
                    "timeRange": "24h",
                    "colorMap": {
                        "RUN": "#22c55e",
                        "STOP": "#f59e0b",
                        "FAULT": "#ef4444"
                    },
                    "showLabels": True,
                    "showDuration": True
                }
            },
            
            # ==========================================
            # 6. TimeseriesPanel - Temperatura (var0)
            # ==========================================
            {
                "id": "var0-chart",
                "type": "TimeseriesPanel",
                "title": "Temperatura (var0)",
                "position": {"row": 5, "col": 0, "colSpan": 6, "rowSpan": 4},
                "config": {
                    "series": [
                        {
                            "pointName": "var0",
                            "label": "Temperatura",
                            "color": "#ef4444",
                            "unit": "°C",
                            "aggregation": "1m",
                            "yAxisSide": "left"
                        }
                    ],
                    "timeRange": "6h",
                    "yAxis": {
                        "left": {
                            "label": "Temperatura (°C)",
                            "min": "auto",
                            "max": "auto"
                        }
                    },
                    "legend": {
                        "show": True,
                        "position": "bottom"
                    },
                    "grid": True,
                    "tooltip": True,
                    "zoom": True
                }
            },
            
            # ==========================================
            # 7. TimeseriesPanel - Umidade (var1)
            # ==========================================
            {
                "id": "var1-chart",
                "type": "TimeseriesPanel",
                "title": "Umidade (var1)",
                "position": {"row": 5, "col": 6, "colSpan": 6, "rowSpan": 4},
                "config": {
                    "series": [
                        {
                            "pointName": "var1",
                            "label": "Umidade",
                            "color": "#3b82f6",
                            "unit": "%",
                            "aggregation": "1m",
                            "yAxisSide": "left"
                        }
                    ],
                    "timeRange": "6h",
                    "yAxis": {
                        "left": {
                            "label": "Umidade (%)",
                            "min": 0,
                            "max": 100
                        }
                    },
                    "legend": {
                        "show": True,
                        "position": "bottom"
                    },
                    "grid": True,
                    "tooltip": True,
                    "zoom": True
                }
            },
            
            # ==========================================
            # 8. TimeseriesPanel - RSSI (WiFi)
            # ==========================================
            {
                "id": "rssi-chart",
                "type": "TimeseriesPanel",
                "title": "Sinal WiFi (RSSI)",
                "position": {"row": 9, "col": 0, "colSpan": 12, "rowSpan": 4},
                "config": {
                    "series": [
                        {
                            "pointName": "rssi",
                            "label": "RSSI",
                            "color": "#8b5cf6",
                            "unit": "dBm",
                            "aggregation": "1m",
                            "yAxisSide": "left"
                        }
                    ],
                    "timeRange": "6h",
                    "yAxis": {
                        "left": {
                            "label": "RSSI (dBm)",
                            "min": -100,
                            "max": -40
                        }
                    },
                    "thresholds": [
                        {"value": -75, "color": "#f59e0b", "label": "Sinal Fraco"},
                        {"value": -85, "color": "#ef4444", "label": "Sinal Crítico"}
                    ],
                    "legend": {
                        "show": True,
                        "position": "bottom"
                    },
                    "grid": True,
                    "tooltip": True,
                    "zoom": True
                }
            }
        ],
        "metadata": {
            "createdBy": "TrakSense Fase D",
            "description": "Dashboard padrão para inversores JE02 com monitoramento de status, temperatura, umidade e sinal WiFi",
            "tags": ["je02", "inverter", "monitoring"]
        }
    }
    
    # Criar DashboardTemplate
    dashboard_template = DashboardTemplate.objects.create(
        id=uuid.uuid4(),
        device_template=device_template,
        schema='v1',
        version=1,
        json=dashboard_json,
        superseded_by=None
    )
    
    print(f"✅ DashboardTemplate criado para 'inverter_je02_v1' (8 painéis)")


def reverse_je02_dashboard_template(apps, schema_editor):
    """
    Remove DashboardTemplate do JE02.
    """
    DeviceTemplate = apps.get_model('templates', 'DeviceTemplate')
    DashboardTemplate = apps.get_model('templates', 'DashboardTemplate')
    
    try:
        device_template = DeviceTemplate.objects.get(code='inverter_je02_v1')
        DashboardTemplate.objects.filter(device_template=device_template).delete()
        print("🔄 DashboardTemplate 'inverter_je02_v1' removido")
    except DeviceTemplate.DoesNotExist:
        print("⚠️  DeviceTemplate 'inverter_je02_v1' não encontrado (já removido)")


class Migration(migrations.Migration):

    dependencies = [
        ('templates', '0003_je02_device_template'),
    ]

    operations = [
        migrations.RunPython(
            create_je02_dashboard_template,
            reverse_code=reverse_je02_dashboard_template
        ),
    ]
