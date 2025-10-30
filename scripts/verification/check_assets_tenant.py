"""
Testa o endpoint /api/assets/ no tenant UMC
"""
import os
import sys
import django

sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django_tenants.utils import tenant_context
from apps.tenants.models import Tenant
from apps.assets.models import Asset, Site

# Pegar o tenant UMC
tenant = Tenant.objects.get(schema_name='umc')

print(f"=== VERIFICANDO ASSETS NO TENANT: {tenant.name} ===\n")

with tenant_context(tenant):
    # Listar sites
    sites = Site.objects.all()
    print(f"📍 Sites encontrados: {sites.count()}")
    for site in sites:
        print(f"   - {site.name} (ID: {site.id})")
    
    print()
    
    # Listar assets
    assets = Asset.objects.all()
    print(f"🏭 Assets encontrados: {assets.count()}")
    for asset in assets:
        print(f"   - {asset.tag} | {asset.name} | Tipo: {asset.asset_type}")
        print(f"     Site: {asset.site.name if asset.site else 'N/A'}")
        print(f"     ID: {asset.id}")
        print()
