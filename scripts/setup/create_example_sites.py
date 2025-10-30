#!/usr/bin/env python
"""
Script para criar sites de exemplo para teste do seletor de sites.
Cria 3 sites diferentes para o tenant UMC demonstrar a funcionalidade.
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django_tenants.utils import schema_context
from apps.tenants.models import Tenant
from apps.assets.models import Site


def create_example_sites(tenant_schema='umc', force=False):
    """Cria 3 sites de exemplo para teste."""
    try:
        tenant = Tenant.objects.get(schema_name=tenant_schema)
        print(f"\n🏢 Criando sites de exemplo para: {tenant.name}")
        
        with schema_context(tenant.schema_name):
            # Verificar sites existentes
            existing_sites = Site.objects.all()
            print(f"\n📊 Sites existentes: {existing_sites.count()}")
            
            if existing_sites.count() > 0:
                print("\n⚠️  Sites já existem:")
                for site in existing_sites:
                    print(f"   • {site.name}")
                
                if not force:
                    print("\n💡 Use --force para criar novos sites mesmo assim")
                    print("   Exemplo: python create_example_sites.py --force")
                    return
            
            # Sites de exemplo
            sites_data = [
                {
                    'name': 'Uberlândia Medical Center - Unidade Central',
                    'company': 'Uberlândia Medical Center',
                    'sector': 'Saúde',
                    'subsector': 'Hospital Geral',
                    'address': 'Av. João Naves de Ávila, 1234 - Santa Mônica, Uberlândia - MG',
                    'timezone': 'America/Sao_Paulo',
                    'latitude': -18.918521,
                    'longitude': -48.277843,
                    'is_active': True,
                },
                {
                    'name': 'UMC - UTI Unidade Norte',
                    'company': 'Uberlândia Medical Center',
                    'sector': 'Saúde',
                    'subsector': 'UTI',
                    'address': 'Av. Rondon Pacheco, 5678 - Tibery, Uberlândia - MG',
                    'timezone': 'America/Sao_Paulo',
                    'latitude': -18.905123,
                    'longitude': -48.265432,
                    'is_active': True,
                },
                {
                    'name': 'UMC - Laboratório de Análises Clínicas',
                    'company': 'Uberlândia Medical Center',
                    'sector': 'Diagnóstico',
                    'subsector': 'Laboratório',
                    'address': 'Rua Goiás, 910 - Centro, Uberlândia - MG',
                    'timezone': 'America/Sao_Paulo',
                    'latitude': -18.912345,
                    'longitude': -48.269876,
                    'is_active': True,
                },
            ]
            
            print(f"\n🏗️  Criando {len(sites_data)} sites...")
            created_sites = []
            
            for site_data in sites_data:
                site = Site.objects.create(**site_data)
                created_sites.append(site)
                print(f"   ✓ {site.name} (ID: {site.id})")
            
            print(f"\n✅ {len(created_sites)} sites criados com sucesso!")
            print(f"\n📋 Resumo:")
            for site in created_sites:
                print(f"\n   🏢 {site.name}")
                print(f"      ID: {site.id}")
                print(f"      Setor: {site.sector}")
                print(f"      Endereço: {site.address}")
                print(f"      Coordenadas: {site.latitude}, {site.longitude}")
            
            print(f"\n💡 Próximo passo:")
            print(f"   1. Acesse o frontend: http://localhost:5173/")
            print(f"   2. Faça login")
            print(f"   3. Observe o header - deve aparecer um dropdown de sites")
            print(f"   4. Teste alternando entre os sites")
            
    except Tenant.DoesNotExist:
        print(f"❌ Tenant com schema '{tenant_schema}' não encontrado!")
        print("\n📋 Tenants disponíveis:")
        for t in Tenant.objects.all():
            print(f"   • {t.name} (schema: {t.schema_name})")
    except Exception as e:
        print(f"❌ Erro ao criar sites: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    import sys
    
    print("=" * 70)
    print("🏗️  CRIAÇÃO DE SITES DE EXEMPLO - UMC")
    print("=" * 70)
    
    force = '--force' in sys.argv
    create_example_sites('umc', force=force)
    
    print("\n" + "=" * 70)
    print("✅ Script finalizado!")
    print("=" * 70)
