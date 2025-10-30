"""
Script para testar acesso aos Assets e Sites via ORM
"""
import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.tenants.models import Tenant
from apps.assets.models import Site, Asset
from django.db import connection

def test_assets_access():
    print("\n" + "="*70)
    print("TESTE DE ACESSO AOS ASSETS E SITES")
    print("="*70)
    
    # Obter tenant umc
    tenant = Tenant.objects.get(schema_name='umc')
    print(f"\n✅ Tenant: {tenant.name} (schema: {tenant.schema_name})")
    
    # Ativar o schema do tenant
    connection.set_tenant(tenant)
    print(f"✅ Schema ativado: {tenant.schema_name}")
    
    # Testar Sites
    print("\n" + "-"*70)
    print("SITES:")
    print("-"*70)
    sites = Site.objects.all()
    print(f"Total de sites: {sites.count()}")
    
    for site in sites[:5]:  # Mostrar apenas os primeiros 5
        print(f"  - {site.name} (is_active: {site.is_active})")
    
    # Testar Assets
    print("\n" + "-"*70)
    print("ASSETS:")
    print("-"*70)
    assets = Asset.objects.all()
    print(f"Total de assets: {assets.count()}")
    
    for asset in assets[:5]:  # Mostrar apenas os primeiros 5
        try:
            site_info = f"Site: {asset.site.name}" if asset.site else "Site: N/A"
            print(f"  - {asset.tag} ({asset.asset_type}) - {site_info} - is_active: {asset.is_active}")
        except Exception as e:
            print(f"  - {asset.tag} - ERRO: {e}")
    
    # Testar query que está falhando no admin
    print("\n" + "-"*70)
    print("TESTANDO QUERY DO ADMIN (Asset.objects.select_related('site')):")
    print("-"*70)
    
    try:
        assets_with_site = Asset.objects.select_related('site').all()
        print(f"✅ Query executada com sucesso!")
        print(f"   Total: {assets_with_site.count()} assets")
        
        for asset in assets_with_site[:3]:
            print(f"   - {asset.tag}: Site={asset.site.name}, is_active={asset.is_active}")
    except Exception as e:
        print(f"❌ ERRO na query: {e}")
        import traceback
        traceback.print_exc()
    
    # Testar filtro com is_active
    print("\n" + "-"*70)
    print("TESTANDO FILTRO is_active:")
    print("-"*70)
    
    try:
        active_sites = Site.objects.filter(is_active=True)
        print(f"✅ Sites ativos: {active_sites.count()}")
        
        active_assets = Asset.objects.filter(is_active=True)
        print(f"✅ Assets ativos: {active_assets.count()}")
        
        # Query complexa com join e filtro
        assets_with_active_sites = Asset.objects.filter(
            site__is_active=True
        ).select_related('site')
        print(f"✅ Assets com sites ativos: {assets_with_active_sites.count()}")
        
    except Exception as e:
        print(f"❌ ERRO no filtro: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    test_assets_access()
