"""
Script para testar view de histórico de telemetria diretamente no Django
Testa a lógica da view sem precisar de autenticação HTTP
"""

import os
import django
from datetime import datetime, timedelta
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'traksense.settings')
django.setup()

from django_tenants.utils import schema_context
from apps.ingest.models import Reading
from django.db.models import Avg, Min, Max, Count
from django.db.models.functions import TruncMinute, TruncHour

TENANT_SCHEMA = "umc"
DEVICE_ID = "4b686f6d70107115"

print("=" * 60)
print("🔍 TESTE: Dados de Telemetria no Banco")
print("=" * 60)

with schema_context(TENANT_SCHEMA):
    # 1. Verificar se existem readings para o device
    print(f"\n1️⃣ Verificando readings para device: {DEVICE_ID}")
    
    total_readings = Reading.objects.filter(
        device_id=DEVICE_ID
    ).count()
    
    print(f"   Total de readings: {total_readings}")
    
    if total_readings == 0:
        print("   ⚠️  Nenhuma reading encontrada!")
        print("   Verifique se o device está publicando dados")
        exit(1)
    
    # 2. Verificar readings nas últimas 24h
    print(f"\n2️⃣ Verificando readings nas últimas 24 horas")
    
    end = timezone.now()
    start = end - timedelta(hours=24)
    
    print(f"   Período: {start} até {end}")
    
    readings_24h = Reading.objects.filter(
        device_id=DEVICE_ID,
        ts__gte=start,
        ts__lte=end
    )
    
    count_24h = readings_24h.count()
    print(f"   Readings nas últimas 24h: {count_24h}")
    
    if count_24h == 0:
        print("   ⚠️  Nenhuma reading nas últimas 24h!")
        print("   Vamos verificar as readings mais recentes...")
        
        recent = Reading.objects.filter(
            device_id=DEVICE_ID
        ).order_by('-ts')[:5]
        
        print(f"\n   📊 Últimas 5 readings:")
        for r in recent:
            print(f"      {r.ts} | Sensor: {r.sensor_id} | Valor: {r.value}")
        
        # Ajustar período para incluir dados mais antigos
        if recent.exists():
            oldest_recent = recent.last()
            start = oldest_recent.ts - timedelta(hours=1)
            end = timezone.now()
            
            print(f"\n   Ajustando período para: {start} até {end}")
            
            readings_24h = Reading.objects.filter(
                device_id=DEVICE_ID,
                ts__gte=start,
                ts__lte=end
            )
            count_24h = readings_24h.count()
            print(f"   Readings no novo período: {count_24h}")
    
    # 3. Agrupar por sensor
    print(f"\n3️⃣ Agrupando por sensor")
    
    sensors = readings_24h.values('sensor_id').annotate(
        count=Count('id')
    ).order_by('-count')
    
    for sensor in sensors:
        print(f"   Sensor: {sensor['sensor_id']} -> {sensor['count']} readings")
    
    # 4. Simular agregação por sensor (como a view faria)
    print(f"\n4️⃣ Simulando agregação temporal (5 minutos)")
    
    # Calcular intervalo de agregação
    duration_hours = (end - start).total_seconds() / 3600
    
    if duration_hours <= 1:
        bucket = 'raw'
        trunc_func = None
    elif duration_hours <= 6:
        bucket = '1m'
        trunc_func = TruncMinute
    elif duration_hours <= 24:
        bucket = '5m'
        # Para 5 minutos, vamos usar TruncMinute e depois filtrar
        trunc_func = TruncMinute
    else:
        bucket = '1h'
        trunc_func = TruncHour
    
    print(f"   Duração: {duration_hours:.1f} horas")
    print(f"   Bucket escolhido: {bucket}")
    
    series_data = {}
    
    for sensor in sensors:
        sensor_id = sensor['sensor_id']
        
        sensor_readings = readings_24h.filter(sensor_id=sensor_id)
        
        # Obter labels do primeiro reading
        first_reading = sensor_readings.first()
        labels = first_reading.labels if first_reading else {}
        
        sensor_type = labels.get('metric_type', '')
        sensor_name = labels.get('sensor_name', sensor_id)
        unit = labels.get('unit', '')
        
        print(f"\n   📈 Série: {sensor_id}")
        print(f"      Sensor Type: {sensor_type}")
        print(f"      Sensor Name: {sensor_name}")
        print(f"      Unit: {unit}")
        
        if bucket == 'raw':
            # Retornar dados brutos
            data_points = list(sensor_readings.order_by('ts').values(
                'ts', 'value'
            )[:100])  # Limitar a 100 pontos
            
            print(f"      Pontos (raw): {len(data_points)}")
        else:
            # Agregar dados
            if trunc_func:
                aggregated = sensor_readings.annotate(
                    bucket_time=trunc_func('ts')
                ).values('bucket_time').annotate(
                    avg=Avg('value'),
                    min=Min('value'),
                    max=Max('value'),
                    count=Count('id')
                ).order_by('bucket_time')
                
                data_points = list(aggregated)
                print(f"      Pontos (agregados): {len(data_points)}")
                
                if len(data_points) > 0:
                    print(f"      Primeiro ponto:")
                    first = data_points[0]
                    print(f"         ts: {first['bucket_time']}")
                    print(f"         Avg: {first['avg']}")
                    print(f"         Min: {first['min']}")
                    print(f"         Max: {first['max']}")
                    print(f"         Count: {first['count']}")
                    
                    print(f"      Último ponto:")
                    last = data_points[-1]
                    print(f"         ts: {last['bucket_time']}")
                    print(f"         Avg: {last['avg']}")
                    print(f"         Min: {last['min']}")
                    print(f"         Max: {last['max']}")
                    print(f"         Count: {last['count']}")
        
        series_data[sensor_id] = {
            'sensorId': sensor_id,
            'sensorName': sensor_name,
            'sensorType': sensor_type,
            'unit': unit,
            'data': data_points
        }
    
    # 5. Resultado final
    print(f"\n5️⃣ Resultado Final")
    print(f"   Total de séries: {len(series_data)}")
    
    for sensor_id, series in series_data.items():
        print(f"   • {sensor_id}: {len(series['data'])} pontos")
    
    print("\n" + "="*60)
    print("✅ Teste concluído!")
    print("="*60)
    
    # Verificações finais
    print(f"\n🎯 Verificações:")
    
    if count_24h > 0:
        print(f"   ✅ Existem {count_24h} readings nas últimas 24h")
    else:
        print(f"   ❌ Não há readings nas últimas 24h")
    
    if len(series_data) > 0:
        print(f"   ✅ {len(series_data)} séries foram criadas")
    else:
        print(f"   ❌ Nenhuma série foi criada")
    
    all_have_data = all(len(s['data']) > 0 for s in series_data.values())
    if all_have_data:
        print(f"   ✅ Todas as séries têm pontos de dados")
    else:
        print(f"   ❌ Algumas séries estão vazias")
    
    all_have_type = all(s['sensorType'] for s in series_data.values())
    if all_have_type:
        print(f"   ✅ Todas as séries têm sensorType definido")
    else:
        print(f"   ⚠️  Algumas séries não têm sensorType")
        for sensor_id, series in series_data.items():
            if not series['sensorType']:
                print(f"      - {sensor_id}: sensorType vazio!")
