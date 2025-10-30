"""
Testar endpoint /api/sites/{id}/devices/ para verificar se mqtt_client_id está sendo retornado
"""
import os
import sys
import django
import json

# Setup Django
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django_tenants.utils import schema_context
from apps.assets.models import Site
from apps.assets.serializers import DeviceListSerializer

TENANT_SCHEMA = 'umc'
SITE_NAME = "Uberlândia Medical Center"

print(f"\n{'='*80}")
print(f"TESTANDO ENDPOINT /api/sites/{{id}}/devices/")
print(f"{'='*80}\n")

with schema_context(TENANT_SCHEMA):
    # Buscar site
    try:
        site = Site.objects.get(name=SITE_NAME)
        print(f"✅ Site encontrado: {site.name} (ID: {site.id})")
        print()
    except Site.DoesNotExist:
        print(f"❌ Site '{SITE_NAME}' não encontrado!")
        sys.exit(1)
    
    # Buscar devices através dos assets
    from apps.assets.models import Device
    
    devices = Device.objects.filter(
        asset__site=site
    ).select_related('asset')
    
    print(f"📱 Devices encontrados: {devices.count()}")
    print()
    
    # Serializar com DeviceListSerializer
    serializer = DeviceListSerializer(devices, many=True)
    data = serializer.data
    
    print("Resposta do serializer:")
    print(json.dumps(data, indent=2, ensure_ascii=False, default=str))
    print()
    
    # Verificar se mqtt_client_id está presente
    print(f"\n{'='*80}")
    print("VERIFICAÇÃO DE CAMPOS")
    print(f"{'='*80}\n")
    
    if data:
        first_device = data[0]
        required_fields = ['id', 'mqtt_client_id', 'name', 'serial_number', 'device_type']
        
        missing_fields = []
        for field in required_fields:
            if field in first_device:
                value = first_device[field]
                print(f"✅ {field}: {value}")
            else:
                missing_fields.append(field)
                print(f"❌ {field}: AUSENTE")
        
        print()
        
        if missing_fields:
            print(f"⚠️  Campos ausentes: {', '.join(missing_fields)}")
        else:
            print("✅ Todos os campos obrigatórios estão presentes!")
            print()
            print("Frontend deveria funcionar corretamente com esta resposta.")
    else:
        print("❌ Nenhum device encontrado!")
