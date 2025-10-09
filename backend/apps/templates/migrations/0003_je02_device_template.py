"""
Migration: Adicionar DeviceTemplate e PointTemplates para JE02

Cria template de dispositivo inverter_je02_v1 com 8 pontos de telemetria:
- status (ENUM: RUN, STOP, FAULT)
- fault (BOOL)
- rssi (NUM: dBm)
- uptime (NUM: s)
- cntserr (NUM)
- var0 (NUM: temperatura dividida por 10)
- var1 (NUM: umidade dividida por 10)
- rele (BOOL: estado do relé)

Autor: TrakSense Team
Data: 2025-10-08 (Fase D - JE02)
"""

from django.db import migrations
import uuid


def create_je02_templates(apps, schema_editor):
    """
    Cria DeviceTemplate e PointTemplates para JE02.
    """
    DeviceTemplate = apps.get_model('templates', 'DeviceTemplate')
    PointTemplate = apps.get_model('templates', 'PointTemplate')
    
    # ==================================================================
    # 1. DeviceTemplate: inverter_je02_v1
    # ==================================================================
    
    device_template = DeviceTemplate.objects.create(
        id=uuid.uuid4(),
        code='inverter_je02_v1',
        name='Inversor JE02 v1',
        version=1,
        description='''
Template para inversores JE02 (modelo IO2AI2RO1).

Características:
- 2 entradas digitais (INPUT1: RUN/STOP, INPUT2: FALHA)
- 1 saída relé (RELE: comando ON/OFF)
- 2 entradas analógicas (VAR0: temperatura, VAR1: umidade)
- Monitoramento WiFi (RSSI)
- Contadores de erro e uptime

Payloads suportados:
- DATA: telemetria em tempo real
- INFO: metadados do device (devname, devip, devmac, etc.)

Adapter: je02_v1
        '''.strip(),
        is_global=True,
        tenant_override=None
    )
    
    # ==================================================================
    # 2. PointTemplates (8 pontos)
    # ==================================================================
    
    # 2.1 status (ENUM: RUN, STOP, FAULT)
    PointTemplate.objects.create(
        id=uuid.uuid4(),
        device_template=device_template,
        name='status',
        ptype='enum',
        enum_values=['RUN', 'STOP', 'FAULT'],
        unit=None,
        polarity='normal',
        hysteresis=None,
        default_limits=None
    )
    
    # 2.2 fault (BOOL)
    PointTemplate.objects.create(
        id=uuid.uuid4(),
        device_template=device_template,
        name='fault',
        ptype='bool',
        enum_values=None,
        unit=None,
        polarity='normal',
        hysteresis=None,
        default_limits=None
    )
    
    # 2.3 rssi (NUM: dBm)
    PointTemplate.objects.create(
        id=uuid.uuid4(),
        device_template=device_template,
        name='rssi',
        ptype='num',
        enum_values=None,
        unit='dBm',
        polarity='inverted',  # Valor baixo (muito negativo) = problema
        hysteresis=5.0,
        default_limits={
            'warn_low': -75,    # Sinal fraco
            'crit_low': -85,    # Sinal crítico
            'warn_high': None,
            'crit_high': None
        }
    )
    
    # 2.4 uptime (NUM: s)
    PointTemplate.objects.create(
        id=uuid.uuid4(),
        device_template=device_template,
        name='uptime',
        ptype='num',
        enum_values=None,
        unit='s',
        polarity='normal',
        hysteresis=None,
        default_limits=None
    )
    
    # 2.5 cntserr (NUM: contador de erros)
    PointTemplate.objects.create(
        id=uuid.uuid4(),
        device_template=device_template,
        name='cntserr',
        ptype='num',
        enum_values=None,
        unit=None,
        polarity='normal',
        hysteresis=None,
        default_limits={
            'warn_low': None,
            'crit_low': None,
            'warn_high': 10,    # Muitos erros = problema
            'crit_high': 50
        }
    )
    
    # 2.6 var0 (NUM: temperatura após divisão por 10)
    PointTemplate.objects.create(
        id=uuid.uuid4(),
        device_template=device_template,
        name='var0',
        ptype='num',
        enum_values=None,
        unit='°C',
        polarity='normal',
        hysteresis=1.0,
        default_limits={
            'warn_low': 15.0,
            'crit_low': 10.0,
            'warn_high': 30.0,
            'crit_high': 35.0
        }
    )
    
    # 2.7 var1 (NUM: umidade após divisão por 10)
    PointTemplate.objects.create(
        id=uuid.uuid4(),
        device_template=device_template,
        name='var1',
        ptype='num',
        enum_values=None,
        unit='%',
        polarity='normal',
        hysteresis=5.0,
        default_limits={
            'warn_low': 30.0,
            'crit_low': 20.0,
            'warn_high': 70.0,
            'crit_high': 80.0
        }
    )
    
    # 2.8 rele (BOOL: estado do relé)
    PointTemplate.objects.create(
        id=uuid.uuid4(),
        device_template=device_template,
        name='rele',
        ptype='bool',
        enum_values=None,
        unit=None,
        polarity='normal',
        hysteresis=None,
        default_limits=None
    )
    
    print(f"✅ DeviceTemplate 'inverter_je02_v1' criado com 8 PointTemplates")


def reverse_je02_templates(apps, schema_editor):
    """
    Remove DeviceTemplate e PointTemplates do JE02.
    """
    DeviceTemplate = apps.get_model('templates', 'DeviceTemplate')
    
    # Deletar DeviceTemplate (cascata remove PointTemplates)
    DeviceTemplate.objects.filter(code='inverter_je02_v1').delete()
    
    print("🔄 DeviceTemplate 'inverter_je02_v1' removido")


class Migration(migrations.Migration):

    dependencies = [
        ('templates', '0002_add_check_constraints'),
    ]

    operations = [
        migrations.RunPython(
            create_je02_templates,
            reverse_code=reverse_je02_templates
        ),
    ]
