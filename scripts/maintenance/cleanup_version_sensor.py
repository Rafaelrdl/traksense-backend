"""
Script para remover sensores informativos inválidos (version, model, gateway, etc.)
que foram criados por engano no banco de dados.
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection
from django_tenants.utils import schema_context
from apps.assets.models import Sensor, Device

# Lista de tags de sensores que devem ser removidos (elementos informativos, não sensores reais)
INVALID_SENSOR_NAMES = {'model', 'gateway', 'version', 'firmware', 'hardware', 'serial'}


def cleanup_invalid_sensors():
    """Remove sensores informativos que não são sensores reais."""
    
    print("🔍 Buscando sensores inválidos...")
    
    # Para cada tenant schema
    with schema_context('uberlandia_medical_center'):
        print(f"\n📊 Schema: uberlandia_medical_center")
        
        # Buscar sensores com tags contendo nomes informativos
        invalid_sensors = []
        for sensor in Sensor.objects.all():
            # Verificar se o tag termina com algum nome informativo
            tag_parts = sensor.tag.split('_')
            if len(tag_parts) > 0 and tag_parts[-1] in INVALID_SENSOR_NAMES:
                invalid_sensors.append(sensor)
        
        invalid_sensors_qs = Sensor.objects.filter(
            id__in=[s.id for s in invalid_sensors]
        )
        
        print(f"   Encontrados: {len(invalid_sensors)} sensores inválidos")
        
        if len(invalid_sensors) == 0:
            print("   ✅ Nenhum sensor inválido encontrado!")
            return
        
        # Listar os sensores que serão removidos
        print("\n   📋 Sensores que serão removidos:")
        for sensor in invalid_sensors:
            print(f"      - ID: {sensor.id}, Tag: {sensor.tag}, Device: {sensor.device.mqtt_client_id}")
        
        # Confirmar remoção
        confirm = input("\n❓ Confirma a remoção destes sensores? (sim/nao): ").strip().lower()
        
        if confirm in ['sim', 's', 'yes', 'y']:
            deleted_count = invalid_sensors_qs.count()
            invalid_sensors_qs.delete()
            print(f"   ✅ {deleted_count} sensores removidos com sucesso!")
        else:
            print("   ❌ Remoção cancelada pelo usuário.")


if __name__ == '__main__':
    print("=" * 60)
    print("🧹 CLEANUP: Removendo Sensores Informativos Inválidos")
    print("=" * 60)
    
    try:
        cleanup_invalid_sensors()
        print("\n✅ Script concluído com sucesso!")
    except Exception as e:
        print(f"\n❌ Erro ao executar script: {e}")
        import traceback
        traceback.print_exc()
