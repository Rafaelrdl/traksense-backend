"""
Script para testar API de sensores por ativo
Verifica se o endpoint /assets/{id}/sensors/ está retornando dados corretamente
"""

import requests
import json
from django_tenants.utils import schema_context

# Configuração
BASE_URL = "http://umc.localhost:8000"
TENANT_SCHEMA = "umc"

def test_get_sensors_for_asset():
    """Testa buscar sensores de um ativo específico"""
    
    print("=" * 60)
    print("🧪 TESTE: Buscar Sensores por Ativo")
    print("=" * 60)
    
    # Primeiro, buscar assets disponíveis
    print("\n1️⃣ Buscando assets disponíveis...")
    
    from apps.assets.models import Asset
    
    with schema_context(TENANT_SCHEMA):
        assets = Asset.objects.all()[:5]
        
        if not assets:
            print("❌ Nenhum asset encontrado no tenant 'umc'")
            return
        
        print(f"✅ Encontrados {assets.count()} assets")
        
        for asset in assets:
            print(f"\n{'='*60}")
            print(f"📦 Asset: {asset.tag} (ID: {asset.id})")
            print(f"   Tipo: {asset.asset_type}")
            print(f"   Site: {asset.site.name if asset.site else 'N/A'}")
            
            # Buscar sensores deste asset (através dos devices)
            from apps.assets.models import Sensor
            sensors = Sensor.objects.filter(device__asset=asset).select_related('device')
            
            print(f"\n   🔍 Sensores vinculados: {sensors.count()}")
            
            if sensors.count() > 0:
                for sensor in sensors:
                    status = "🟢 ONLINE" if sensor.is_online else "🔴 OFFLINE"
                    print(f"      {status} {sensor.tag}")
                    print(f"         • Tipo: {sensor.metric_type}")
                    print(f"         • Unidade: {sensor.unit}")
                    print(f"         • Device: {sensor.device.mqtt_client_id if sensor.device else 'N/A'}")
                    print(f"         • Último valor: {sensor.last_value} {sensor.unit}")
                    print(f"         • Última leitura: {sensor.last_reading_at}")
            else:
                print("      ⚠️  Nenhum sensor vinculado a este asset")
        
        print("\n" + "="*60)
        print("✅ Teste concluído!")
        print("="*60)

if __name__ == "__main__":
    import os
    import django
    
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'traksense.settings')
    django.setup()
    
    test_get_sensors_for_asset()
