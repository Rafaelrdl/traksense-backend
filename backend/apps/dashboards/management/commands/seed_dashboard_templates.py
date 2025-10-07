"""
Management Command - Seed Dashboard Templates

Cria templates iniciais de dashboards para os device templates.

Templates criados:
-----------------
1. Dashboard para inverter_v1_parsec
   - Painel de status (ENUM)
   - Timeline de histórico
   - KPI de falhas (24h)
   - Gráfico de RSSI

2. Dashboard para chiller_v1
   - Gráfico de temperatura
   - Status da unidade
   - KPI de compressor

Uso:
----
    python manage.py seed_dashboard_templates

Pré-requisito:
-------------
    python manage.py seed_device_templates (deve ser executado antes)

Idempotência:
------------
Se os templates já existem, não duplica (usa get_or_create).

Autor: TrakSense Team
Data: 2025-10-07 (Fase 2)
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from apps.dashboards.models import DashboardTemplate
from apps.devices.models import DeviceTemplate


class Command(BaseCommand):
    help = 'Cria templates iniciais de dashboards para device templates'
    
    @transaction.atomic
    def handle(self, *args, **options):
        """Executa seed de dashboard templates"""
        
        self.stdout.write(self.style.SUCCESS('🌱 Iniciando seed de Dashboard Templates...'))
        
        # ======================================================================
        # DASHBOARD TEMPLATE 1: Inversor Parsec v1
        # ======================================================================
        
        self.stdout.write('\n📊 Criando dashboard para: inverter_v1_parsec...')
        
        try:
            inverter_template = DeviceTemplate.objects.get(
                code='inverter_v1_parsec',
                version=1
            )
        except DeviceTemplate.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(
                    '  ✗ DeviceTemplate inverter_v1_parsec não encontrado!\n'
                    '  Execute primeiro: python manage.py seed_device_templates'
                )
            )
            return
        
        inverter_dashboard_json = {
            "schema": "v1",
            "layout": "cards-2col",
            "panels": [
                {
                    "type": "status",
                    "title": "Estado do inversor",
                    "point": "status",
                    "mappings": {
                        "RUN": "Em operação",
                        "STOP": "Parado",
                        "FAULT": "Falha"
                    }
                },
                {
                    "type": "timeline",
                    "title": "Histórico de estado",
                    "points": ["status"]
                },
                {
                    "type": "kpi",
                    "title": "Falhas (24h)",
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
        
        inverter_dashboard, created = DashboardTemplate.objects.get_or_create(
            device_template=inverter_template,
            version=1,
            defaults={
                'schema': 'v1',
                'json': inverter_dashboard_json
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('  ✓ DashboardTemplate criado'))
        else:
            self.stdout.write(self.style.WARNING('  ⚠ DashboardTemplate já existe'))
        
        # ======================================================================
        # DASHBOARD TEMPLATE 2: Chiller v1
        # ======================================================================
        
        self.stdout.write('\n📊 Criando dashboard para: chiller_v1...')
        
        try:
            chiller_template = DeviceTemplate.objects.get(
                code='chiller_v1',
                version=1
            )
        except DeviceTemplate.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(
                    '  ✗ DeviceTemplate chiller_v1 não encontrado!\n'
                    '  Execute primeiro: python manage.py seed_device_templates'
                )
            )
            return
        
        chiller_dashboard_json = {
            "schema": "v1",
            "layout": "cards-2col",
            "panels": [
                {
                    "type": "timeseries",
                    "title": "Temperatura da água",
                    "point": "temp_agua",
                    "agg": "1m",
                    "yUnit": "°C"
                },
                {
                    "type": "status",
                    "title": "Estado da unidade",
                    "point": "unit_state",
                    "mappings": {
                        "ON": "Ligado",
                        "OFF": "Desligado",
                        "FAULT": "Falha"
                    }
                },
                {
                    "type": "kpi",
                    "title": "Compressor 1",
                    "point": "compressor_1_on"
                },
                {
                    "type": "timeline",
                    "title": "Histórico de estado",
                    "points": ["unit_state"]
                }
            ]
        }
        
        chiller_dashboard, created = DashboardTemplate.objects.get_or_create(
            device_template=chiller_template,
            version=1,
            defaults={
                'schema': 'v1',
                'json': chiller_dashboard_json
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('  ✓ DashboardTemplate criado'))
        else:
            self.stdout.write(self.style.WARNING('  ⚠ DashboardTemplate já existe'))
        
        # ======================================================================
        # RESUMO
        # ======================================================================
        
        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.SUCCESS('✅ Seed de Dashboard Templates concluído!'))
        self.stdout.write('\nDashboards disponíveis:')
        self.stdout.write(f'  • inverter_v1_parsec (v1) - {len(inverter_dashboard_json["panels"])} painéis')
        self.stdout.write(f'  • chiller_v1 (v1) - {len(chiller_dashboard_json["panels"])} painéis')
        self.stdout.write('\nPróximo passo:')
        self.stdout.write('  Criar Devices pelo Django Admin e ver provisionamento automático!')
        self.stdout.write('='*70 + '\n')
