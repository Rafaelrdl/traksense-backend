#!/usr/bin/env python
"""
Script para limpar sites e assets de teste do tenant UMC.
Remove todos os sites criados durante a fase de testes.
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.db import connection
from django_tenants.utils import schema_context
from apps.tenants.models import Tenant
from apps.assets.models import Site, Asset, Device, Sensor


def cleanup_tenant_data(tenant_schema='umc', force=False):
    """Limpa todos os dados de teste do tenant especificado."""
    try:
        tenant = Tenant.objects.get(schema_name=tenant_schema)
        print(f"\n🔍 Limpando dados do tenant: {tenant.name} (schema: {tenant.schema_name})")
        
        with schema_context(tenant.schema_name):
            # Contar dados antes
            sensors_count = Sensor.objects.count()
            devices_count = Device.objects.count()
            assets_count = Asset.objects.count()
            sites_count = Site.objects.count()
            
            print(f"\n📊 Estado atual:")
            print(f"   • {sites_count} sites")
            print(f"   • {assets_count} assets")
            print(f"   • {devices_count} devices")
            print(f"   • {sensors_count} sensors")
            
            if sites_count == 0 and assets_count == 0:
                print(f"\n✅ Tenant já está limpo!")
                return
            
            # Confirmar exclusão
            if not force:
                print(f"\n⚠️  ATENÇÃO: Isso irá excluir TODOS os dados de teste!")
                print("Execute com --force para confirmar: python cleanup_test_sites.py --force")
                return
            
            # Excluir na ordem correta (devido às foreign keys)
            print(f"\n🗑️  Excluindo dados...")
            
            # 1. Sensores (dependem de devices)
            if sensors_count > 0:
                deleted_sensors = Sensor.objects.all().delete()
                print(f"   ✓ {deleted_sensors[0]} sensores excluídos")
            
            # 2. Devices (dependem de assets)
            if devices_count > 0:
                deleted_devices = Device.objects.all().delete()
                print(f"   ✓ {deleted_devices[0]} devices excluídos")
            
            # 3. Assets (dependem de sites)
            if assets_count > 0:
                deleted_assets = Asset.objects.all().delete()
                print(f"   ✓ {deleted_assets[0]} assets excluídos")
            
            # 4. Sites
            if sites_count > 0:
                deleted_sites = Site.objects.all().delete()
                print(f"   ✓ {deleted_sites[0]} sites excluídos")
            
            print(f"\n✅ Limpeza concluída! O tenant '{tenant.name}' está pronto para novos dados.")
            
    except Tenant.DoesNotExist:
        print(f"❌ Tenant com schema '{tenant_schema}' não encontrado!")
        print("\n📋 Tenants disponíveis:")
        for t in Tenant.objects.all():
            print(f"   • {t.name} (schema: {t.schema_name})")
    except Exception as e:
        print(f"❌ Erro durante a limpeza: {str(e)}")
        import traceback
        traceback.print_exc()


def list_tenant_sites(tenant_schema='umc'):
    """Lista todos os sites do tenant."""
    try:
        tenant = Tenant.objects.get(schema_name=tenant_schema)
        print(f"\n📍 Sites do tenant: {tenant.name} (schema: {tenant.schema_name})")
        
        with schema_context(tenant.schema_name):
            sites = Site.objects.all().order_by('created_at')
            
            if not sites:
                print("   (Nenhum site encontrado)")
                return
            
            for i, site in enumerate(sites, 1):
                assets_count = site.assets.count()
                print(f"\n   {i}. {site.name}")
                print(f"      ID: {site.id}")
                print(f"      Empresa: {site.company or '-'}")
                print(f"      Setor: {site.sector or '-'}")
                print(f"      Assets: {assets_count}")
                print(f"      Criado em: {site.created_at.strftime('%d/%m/%Y %H:%M')}")
                
                if assets_count > 0:
                    print(f"      Assets vinculados:")
                    for asset in site.assets.all()[:5]:
                        print(f"         - {asset.name} ({asset.get_asset_type_display()})")
                    if assets_count > 5:
                        print(f"         ... e mais {assets_count - 5} assets")
                        
    except Tenant.DoesNotExist:
        print(f"❌ Tenant com schema '{tenant_schema}' não encontrado!")


if __name__ == '__main__':
    import sys
    
    print("=" * 70)
    print("🧹 SCRIPT DE LIMPEZA DE DADOS DE TESTE - UMC")
    print("=" * 70)
    
    # Verificar se foi passado --force
    force = '--force' in sys.argv
    
    # Listar sites primeiro
    list_tenant_sites('umc')
    
    # Executar limpeza
    cleanup_tenant_data('umc', force=force)
    
    print("\n" + "=" * 70)
    print("✅ Script finalizado!")
    print("=" * 70)
