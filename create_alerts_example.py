"""
Script para criar alertas de exemplo via Django shell
"""
from django.db import connection
from apps.alerts.models import Rule, Alert
from apps.assets.models import Asset
from django.utils import timezone
from datetime import timedelta

# Definir schema do tenant
connection.set_schema('uberlandia_medical_center')

# Buscar regra e asset existentes
rule = Rule.objects.first()
asset = Asset.objects.first()

if not rule:
    print("❌ Nenhuma regra encontrada")
    exit()

if not asset:
    print("❌ Nenhum asset encontrado")
    exit()

print(f"✅ Usando regra: {rule.name}")
print(f"✅ Usando asset: {asset.tag}")

# Criar 3 alertas de exemplo
alertas_criados = []

# Alerta 1: Crítico - Temperatura alta
alert1 = Alert.objects.create(
    rule=rule,
    message=f"Temperatura crítica detectada em {asset.tag}",
    severity='Critical',
    asset_tag=asset.tag,
    parameter_key='TEMPERATURE',
    parameter_value=28.5,
    threshold=25.0,
    triggered_at=timezone.now() - timedelta(hours=2),
    acknowledged=False,
    resolved=False
)
alertas_criados.append(alert1)
print(f"✅ Alerta 1 criado: {alert1.message}")

# Alerta 2: Alto - Temperatura alta (reconhecido)
alert2 = Alert.objects.create(
    rule=rule,
    message=f"Chiller 02 operando com temperatura de condensação acima do limite",
    severity='High',
    asset_tag=asset.tag,
    parameter_key='TEMPERATURE',
    parameter_value=26.8,
    threshold=25.0,
    triggered_at=timezone.now() - timedelta(days=1),
    acknowledged=True,
    acknowledged_at=timezone.now() - timedelta(hours=12),
    resolved=False
)
alertas_criados.append(alert2)
print(f"✅ Alerta 2 criado: {alert2.message}")

# Alerta 3: Médio - Resolvido
alert3 = Alert.objects.create(
    rule=rule,
    message=f"Consumo 18% acima da meta estabelecida",
    severity='Medium',
    asset_tag=asset.tag,
    parameter_key='CONSUMPTION',
    parameter_value=118.0,
    threshold=100.0,
    triggered_at=timezone.now() - timedelta(days=2),
    acknowledged=True,
    acknowledged_at=timezone.now() - timedelta(days=1, hours=12),
    resolved=True,
    resolved_at=timezone.now() - timedelta(days=1),
)
alertas_criados.append(alert3)
print(f"✅ Alerta 3 criado: {alert3.message}")

print(f"\n🎉 {len(alertas_criados)} alertas de exemplo criados com sucesso!")
print("\nPara ver os alertas, acesse: http://umc.localhost:5173/alertas")
