#!/usr/bin/env python
"""
Script para testar avaliação da regra do CHILLER-001
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django_tenants.utils import schema_context
from apps.alerts.models import Rule, Alert
from apps.alerts.tasks import evaluate_rules_task
from apps.ingest.models import Reading
from django.utils import timezone

schema = 'umc'

print("=" * 80)
print("🧪 TESTE: Avaliação de Regra CHILLER-001")
print("=" * 80)

with schema_context(schema):
    # Buscar a regra
    rule = Rule.objects.filter(name__icontains='CHILLER').first()
    
    if not rule:
        print("\n❌ Regra do CHILLER não encontrada!")
        print("\nRegras disponíveis:")
        for r in Rule.objects.all():
            print(f"   - {r.name} (ID: {r.id})")
        exit(1)
    
    print(f"\n📋 Regra encontrada: {rule.name}")
    print(f"   Equipamento: {rule.equipment.name} ({rule.equipment.tag})")
    print(f"   Habilitada: {rule.enabled}")
    
    # Verificar parâmetros
    params = rule.parameters.all()
    print(f"\n🔍 Parâmetros da regra ({params.count()}):")
    
    for i, param in enumerate(params, 1):
        print(f"\n   Parâmetro {i}:")
        print(f"      Sensor: {param.parameter_key}")
        print(f"      Condição: {param.operator} {param.threshold}")
        print(f"      Severidade: {param.severity}")
        print(f"      Duração: {param.duration} min")
        print(f"      Template: {param.message_template}")
        
        # Buscar última leitura
        device = rule.equipment.devices.first()
        if device:
            latest_reading = Reading.objects.filter(
                device_id=device.mqtt_client_id,
                sensor_id=param.parameter_key
            ).order_by('-ts').first()
            
            if latest_reading:
                age_minutes = (timezone.now() - latest_reading.ts).total_seconds() / 60
                print(f"\n      📊 Última leitura:")
                print(f"         Valor: {latest_reading.value}")
                print(f"         Timestamp: {latest_reading.ts}")
                print(f"         Idade: {age_minutes:.1f} minutos")
                
                # Avaliar condição
                value = latest_reading.value
                threshold = param.threshold
                
                if param.operator == '>':
                    condition_met = value > threshold
                elif param.operator == '<':
                    condition_met = value < threshold
                elif param.operator == '>=':
                    condition_met = value >= threshold
                elif param.operator == '<=':
                    condition_met = value <= threshold
                elif param.operator == '==':
                    condition_met = value == threshold
                else:
                    condition_met = False
                
                print(f"\n      🎯 Avaliação: {value} {param.operator} {threshold}")
                if condition_met:
                    print(f"      ✅ CONDIÇÃO ATENDIDA!")
                else:
                    print(f"      ❌ Condição NÃO atendida")
            else:
                print(f"\n      ⚠️ Nenhuma leitura encontrada para {param.parameter_key}")
        else:
            print(f"\n      ⚠️ Nenhum device associado ao equipamento")
    
    # Verificar alertas existentes
    recent_alerts = Alert.objects.filter(
        rule=rule,
        triggered_at__gte=timezone.now() - timezone.timedelta(hours=1)
    ).order_by('-triggered_at')
    
    print(f"\n📢 Alertas recentes (última hora): {recent_alerts.count()}")
    for alert in recent_alerts[:5]:
        print(f"   - {alert.triggered_at}: {alert.message}")
    
    # Executar avaliação de regras
    print(f"\n🔄 Executando avaliação de regras...")
    try:
        evaluate_rules_task()
        print(f"✅ Avaliação concluída!")
        
        # Verificar novos alertas
        new_alerts = Alert.objects.filter(
            rule=rule,
            triggered_at__gte=timezone.now() - timezone.timedelta(minutes=1)
        ).order_by('-triggered_at')
        
        if new_alerts.exists():
            print(f"\n🎉 Novos alertas criados: {new_alerts.count()}")
            for alert in new_alerts:
                print(f"   - {alert.message}")
        else:
            print(f"\n⚠️ Nenhum novo alerta criado")
            print(f"\nPossíveis motivos:")
            print(f"   1. Condições não foram atendidas")
            print(f"   2. Cooldown ainda ativo (última alerta muito recente)")
            print(f"   3. Leituras de telemetria muito antigas (>15 min)")
            
    except Exception as e:
        print(f"❌ Erro ao avaliar regras: {str(e)}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 80)
