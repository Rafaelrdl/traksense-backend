"""
Management Command - Seed Device Templates

Cria templates iniciais de dispositivos e pontos de telemetria.

Templates criados:
-----------------
1. inverter_v1_parsec (Inversor Parsec v1)
   - status (ENUM: RUN|STOP|FAULT)
   - fault (BOOL)
   - rssi (NUMERIC dBm)

2. chiller_v1 (Chiller v1)
   - temp_agua (NUMERIC °C)
   - unit_state (ENUM: ON|OFF|FAULT)
   - compressor_1_on (BOOL)

Uso:
----
    python manage.py seed_device_templates

Idempotência:
------------
Se os templates já existem, não duplica (usa get_or_create).

Autor: TrakSense Team
Data: 2025-10-07 (Fase 2)
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from apps.devices.models import DeviceTemplate, PointTemplate, PointType, Polarity


class Command(BaseCommand):
    help = 'Cria templates iniciais de dispositivos (inverter_v1_parsec, chiller_v1)'
    
    @transaction.atomic
    def handle(self, *args, **options):
        """Executa seed de templates"""
        
        self.stdout.write(self.style.SUCCESS('🌱 Iniciando seed de Device Templates...'))
        
        # ======================================================================
        # TEMPLATE 1: Inversor Parsec v1
        # ======================================================================
        
        self.stdout.write('\n📦 Criando template: inverter_v1_parsec...')
        
        inverter_template, created = DeviceTemplate.objects.get_or_create(
            code='inverter_v1_parsec',
            version=1,
            defaults={
                'name': 'Inversor Parsec v1',
                'description': (
                    'Inversor de frequência Parsec v1.\n'
                    'Monitoramento via DI1 (status) e DI2 (fault).\n'
                    'Comando de reset via relé.'
                )
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('  ✓ DeviceTemplate criado'))
        else:
            self.stdout.write(self.style.WARNING('  ⚠ DeviceTemplate já existe'))
        
        # Point Templates do inversor
        inverter_points = [
            {
                'name': 'status',
                'label': 'Estado do inversor',
                'ptype': PointType.ENUM,
                'enum_values': ['RUN', 'STOP', 'FAULT'],
                'polarity': Polarity.NORMAL,
                'default_limits': {},
            },
            {
                'name': 'fault',
                'label': 'Falha',
                'ptype': PointType.BOOL,
                'polarity': Polarity.INVERTED,  # Invertida: fault=true é problema
                'default_limits': {},
            },
            {
                'name': 'rssi',
                'label': 'Intensidade do sinal',
                'ptype': PointType.NUMERIC,
                'unit': 'dBm',
                'polarity': Polarity.NORMAL,
                'hysteresis': 0.0,
                'default_limits': {'min': -90, 'max': -30},
            },
        ]
        
        for pt_data in inverter_points:
            pt, created = PointTemplate.objects.get_or_create(
                device_template=inverter_template,
                name=pt_data['name'],
                defaults=pt_data
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'    ✓ PointTemplate criado: {pt_data["name"]}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'    ⚠ PointTemplate já existe: {pt_data["name"]}')
                )
        
        # ======================================================================
        # TEMPLATE 2: Chiller v1
        # ======================================================================
        
        self.stdout.write('\n📦 Criando template: chiller_v1...')
        
        chiller_template, created = DeviceTemplate.objects.get_or_create(
            code='chiller_v1',
            version=1,
            defaults={
                'name': 'Chiller v1',
                'description': (
                    'Chiller de água gelada v1.\n'
                    'Monitoramento de temperatura, estado da unidade e compressor.'
                )
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('  ✓ DeviceTemplate criado'))
        else:
            self.stdout.write(self.style.WARNING('  ⚠ DeviceTemplate já existe'))
        
        # Point Templates do chiller
        chiller_points = [
            {
                'name': 'temp_agua',
                'label': 'Temperatura da água',
                'ptype': PointType.NUMERIC,
                'unit': '°C',
                'polarity': Polarity.NORMAL,
                'hysteresis': 0.5,
                'default_limits': {'min': 5.0, 'max': 12.0},
            },
            {
                'name': 'unit_state',
                'label': 'Estado da unidade',
                'ptype': PointType.ENUM,
                'enum_values': ['ON', 'OFF', 'FAULT'],
                'polarity': Polarity.NORMAL,
                'default_limits': {},
            },
            {
                'name': 'compressor_1_on',
                'label': 'Compressor 1 ligado',
                'ptype': PointType.BOOL,
                'polarity': Polarity.NORMAL,
                'default_limits': {},
            },
        ]
        
        for pt_data in chiller_points:
            pt, created = PointTemplate.objects.get_or_create(
                device_template=chiller_template,
                name=pt_data['name'],
                defaults=pt_data
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'    ✓ PointTemplate criado: {pt_data["name"]}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'    ⚠ PointTemplate já existe: {pt_data["name"]}')
                )
        
        # ======================================================================
        # RESUMO
        # ======================================================================
        
        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.SUCCESS('✅ Seed de Device Templates concluído!'))
        self.stdout.write('\nTemplates disponíveis:')
        self.stdout.write(f'  • inverter_v1_parsec (v1) - {inverter_template.point_templates.count()} pontos')
        self.stdout.write(f'  • chiller_v1 (v1) - {chiller_template.point_templates.count()} pontos')
        self.stdout.write('\nPróximo passo:')
        self.stdout.write('  python manage.py seed_dashboard_templates')
        self.stdout.write('='*70 + '\n')
