"""
Script para gerar dados de telemetria fake para testes.

Cria leituras de sensores para os devices/sensores existentes no banco,
populando a tabela `reading` com dados realistas das últimas 24 horas.

Usage:
    python test_generate_telemetry.py [--hours 24] [--interval 60]
"""
import os
import django
import sys
from datetime import datetime, timedelta
from random import uniform, choice, randint

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.utils import timezone
from apps.ingest.models import Reading
from apps.assets.models import Device, Sensor
from django_tenants.utils import schema_context


def generate_sensor_value(sensor_type, base_value=None):
    """
    Gera valor realista baseado no tipo de sensor.
    
    Args:
        sensor_type: Tipo do sensor (temperature, humidity, power, etc.)
        base_value: Valor base para adicionar variação (opcional)
    
    Returns:
        float: Valor gerado
    """
    if sensor_type == 'TEMPERATURE':
        base = base_value if base_value else uniform(18.0, 26.0)
        variation = uniform(-0.5, 0.5)
        return round(base + variation, 2)
    
    elif sensor_type == 'HUMIDITY':
        base = base_value if base_value else uniform(40.0, 70.0)
        variation = uniform(-2.0, 2.0)
        return round(max(0, min(100, base + variation)), 2)
    
    elif sensor_type == 'PRESSURE':
        base = base_value if base_value else uniform(980.0, 1020.0)
        variation = uniform(-5.0, 5.0)
        return round(base + variation, 2)
    
    elif sensor_type == 'POWER':
        base = base_value if base_value else uniform(1000.0, 5000.0)
        variation = uniform(-100.0, 100.0)
        return round(max(0, base + variation), 2)
    
    elif sensor_type == 'FLOW':
        base = base_value if base_value else uniform(10.0, 100.0)
        variation = uniform(-5.0, 5.0)
        return round(max(0, base + variation), 2)
    
    elif sensor_type == 'CURRENT':
        base = base_value if base_value else uniform(5.0, 20.0)
        variation = uniform(-0.5, 0.5)
        return round(max(0, base + variation), 2)
    
    elif sensor_type == 'VOLTAGE':
        base = base_value if base_value else uniform(200.0, 240.0)
        variation = uniform(-5.0, 5.0)
        return round(base + variation, 2)
    
    else:
        # Generic sensor
        base = base_value if base_value else uniform(0.0, 100.0)
        variation = uniform(-5.0, 5.0)
        return round(max(0, base + variation), 2)


def get_unit_for_sensor_type(sensor_type):
    """Retorna unidade apropriada para o tipo de sensor."""
    units = {
        'TEMPERATURE': '°C',
        'HUMIDITY': '%',
        'PRESSURE': 'Pa',
        'POWER': 'W',
        'FLOW': 'L/min',
        'CURRENT': 'A',
        'VOLTAGE': 'V',
    }
    return units.get(sensor_type, 'unit')


def generate_telemetry(tenant_schema='umc', hours=24, interval_seconds=60):
    """
    Gera dados de telemetria fake.
    
    Args:
        tenant_schema: Schema do tenant (default: 'umc')
        hours: Quantas horas no passado gerar dados (default: 24)
        interval_seconds: Intervalo entre leituras em segundos (default: 60)
    
    Returns:
        int: Quantidade de readings criados
    """
    print(f"🚀 Gerando telemetria fake para tenant '{tenant_schema}'...")
    print(f"   Período: últimas {hours} horas")
    print(f"   Intervalo: {interval_seconds} segundos")
    print()
    
    with schema_context(tenant_schema):
        # Buscar devices com sensores
        devices = Device.objects.filter(sensors__isnull=False).distinct()
        
        if not devices.exists():
            print("❌ Nenhum device com sensores encontrado!")
            print("   Dica: Crie devices e sensores primeiro usando o Django Admin")
            return 0
        
        print(f"📱 Encontrados {devices.count()} devices com sensores:")
        for device in devices:
            sensor_count = device.sensors.count()
            print(f"   - {device.name} ({device.serial_number}): {sensor_count} sensores")
        print()
        
        # Calcular timestamps
        now = timezone.now()
        start_time = now - timedelta(hours=hours)
        total_points = int(hours * 3600 / interval_seconds)
        
        print(f"⏱️  Gerando {total_points} pontos por sensor...")
        print()
        
        readings_created = 0
        sensor_last_values = {}  # Cache para continuidade
        
        # Para cada device
        for device in devices:
            device_readings = 0
            
            # Para cada sensor do device
            for sensor in device.sensors.all():
                sensor_key = f"{device.serial_number}_{sensor.id}"
                
                # Inicializar valor base
                if sensor_key not in sensor_last_values:
                    sensor_last_values[sensor_key] = generate_sensor_value(sensor.metric_type)
                
                # Gerar série temporal
                current_time = start_time
                sensor_readings = []
                
                for i in range(total_points):
                    # Gerar valor com continuidade
                    value = generate_sensor_value(
                        sensor.metric_type,
                        base_value=sensor_last_values[sensor_key]
                    )
                    sensor_last_values[sensor_key] = value
                    
                    # Labels
                    labels = {
                        'sensor_name': sensor.tag,
                        'sensor_type': sensor.metric_type,
                        'unit': get_unit_for_sensor_type(sensor.metric_type),
                        'asset_id': str(sensor.device.asset_id) if sensor.device.asset_id else None
                    }
                    
                    # Criar reading
                    reading = Reading(
                        device_id=device.serial_number,
                        sensor_id=f"{sensor.metric_type}_{sensor.id}",
                        value=value,
                        labels=labels,
                        ts=current_time,
                        created_at=timezone.now()
                    )
                    sensor_readings.append(reading)
                    
                    # Avançar tempo
                    current_time += timedelta(seconds=interval_seconds)
                
                # Bulk create (mais eficiente)
                Reading.objects.bulk_create(sensor_readings, batch_size=500)
                device_readings += len(sensor_readings)
                
                print(f"   ✅ {sensor.tag} ({sensor.metric_type}): {len(sensor_readings)} readings")
            
            readings_created += device_readings
            print(f"      Total device {device.name}: {device_readings} readings")
            print()
        
        print(f"🎉 Total: {readings_created} readings criados com sucesso!")
        print(f"   Tenant: {tenant_schema}")
        print(f"   Período: {start_time.strftime('%Y-%m-%d %H:%M')} até {now.strftime('%Y-%m-%d %H:%M')}")
        
        return readings_created


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Gera dados de telemetria fake para testes'
    )
    parser.add_argument(
        '--tenant',
        type=str,
        default='umc',
        help='Schema do tenant (default: umc)'
    )
    parser.add_argument(
        '--hours',
        type=int,
        default=24,
        help='Quantas horas no passado gerar dados (default: 24)'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=60,
        help='Intervalo entre leituras em segundos (default: 60)'
    )
    parser.add_argument(
        '--clear',
        action='store_true',
        help='Limpar readings existentes antes de gerar novos'
    )
    
    args = parser.parse_args()
    
    # Clear existing data if requested
    if args.clear:
        print(f"🗑️  Limpando readings existentes do tenant '{args.tenant}'...")
        with schema_context(args.tenant):
            count = Reading.objects.count()
            Reading.objects.all().delete()
            print(f"   ✅ {count} readings deletados")
            print()
    
    # Generate telemetry
    try:
        readings_created = generate_telemetry(
            tenant_schema=args.tenant,
            hours=args.hours,
            interval_seconds=args.interval
        )
        
        if readings_created > 0:
            print()
            print("✅ SUCESSO! Telemetria gerada.")
            print()
            print("📊 Próximos passos:")
            print("   1. Acesse a API: http://umc.localhost:8000/api/telemetry/readings/")
            print("   2. Teste agregações: http://umc.localhost:8000/api/telemetry/series/?bucket=5m")
            print("   3. Veja no frontend: http://localhost:5173 (página Sensors)")
            
            sys.exit(0)
        else:
            print()
            print("⚠️  Nenhum reading criado. Verifique se existem devices e sensores.")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Erro ao gerar telemetria: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
