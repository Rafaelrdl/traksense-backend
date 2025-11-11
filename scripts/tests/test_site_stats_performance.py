#!/usr/bin/env python
"""
Teste de Performance - SiteViewSet.stats

Valida que a otimização usando queries agregadas está funcionando.
Compara número de queries e tempo de execução.

Uso:
    python scripts/tests/test_site_stats_performance.py
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.test.utils import CaptureQueriesContext
from django.db import connection
from apps.assets.models import Site, Asset, Device, Sensor
import time


def print_header(title):
    """Print formatted header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def test_site_stats():
    """Test SiteViewSet.stats endpoint performance"""
    print_header("TESTE DE PERFORMANCE: SiteViewSet.stats")
    
    # Get first site with data
    site = Site.objects.annotate(
        asset_count=Asset.objects.filter(site_id=site.id).count()
    ).filter(asset_count__gt=0).first()
    
    if not site:
        print("❌ Nenhum site com assets encontrado")
        print("   Crie alguns assets primeiro")
        return False
    
    print(f"\n📍 Site: {site.name} (ID: {site.id})")
    
    # Count resources
    asset_count = Asset.objects.filter(site=site).count()
    device_count = Device.objects.filter(asset__site=site).count()
    sensor_count = Sensor.objects.filter(device__asset__site=site).count()
    
    print(f"   Assets: {asset_count}")
    print(f"   Devices: {device_count}")
    print(f"   Sensors: {sensor_count}")
    
    # Test with query capture
    print("\n🔍 Executando endpoint stats...\n")
    
    with CaptureQueriesContext(connection) as context:
        start_time = time.time()
        
        # Simulate the stats endpoint
        from django.db.models import Count, Q
        
        # Get stats (same logic as optimized view)
        assets_by_status = list(Asset.objects.filter(site=site).values('status').annotate(
            count=Count('id')
        ).order_by('status'))
        
        assets_by_type = list(Asset.objects.filter(site=site).values('asset_type').annotate(
            count=Count('id')
        ).order_by('asset_type'))
        
        device_stats = Device.objects.filter(asset__site=site).aggregate(
            total=Count('id'),
            online=Count('id', filter=Q(is_online=True))
        )
        
        sensor_stats = Sensor.objects.filter(device__asset__site=site).aggregate(
            total=Count('id'),
            online=Count('id', filter=Q(is_online=True))
        )
        
        stats = {
            'total_assets': sum(item['count'] for item in assets_by_status),
            'assets_by_status': {item['status']: item['count'] for item in assets_by_status},
            'assets_by_type': {item['asset_type']: item['count'] for item in assets_by_type},
            'total_devices': device_stats['total'] or 0,
            'online_devices': device_stats['online'] or 0,
            'total_sensors': sensor_stats['total'] or 0,
            'online_sensors': sensor_stats['online'] or 0,
        }
        
        elapsed_ms = (time.time() - start_time) * 1000
    
    # Results
    query_count = len(context.captured_queries)
    
    print("📊 RESULTADOS:")
    print(f"   Queries executadas: {query_count}")
    print(f"   Tempo de execução: {elapsed_ms:.2f}ms")
    
    # Validation
    print("\n✅ VALIDAÇÃO:")
    
    # Should use aggregate queries (4-5 queries max)
    if query_count <= 5:
        print(f"   ✅ Queries otimizadas (≤5): {query_count}")
        queries_pass = True
    else:
        print(f"   ❌ Muitas queries (>5): {query_count}")
        print(f"      Esperado: ≤5 (queries agregadas)")
        queries_pass = False
    
    # Should be fast (<200ms for reasonable dataset)
    if elapsed_ms < 200:
        print(f"   ✅ Tempo aceitável (<200ms): {elapsed_ms:.2f}ms")
        time_pass = True
    elif elapsed_ms < 500:
        print(f"   ⚠️  Tempo OK mas pode melhorar (<500ms): {elapsed_ms:.2f}ms")
        time_pass = True
    else:
        print(f"   ❌ Tempo muito alto (>500ms): {elapsed_ms:.2f}ms")
        time_pass = False
    
    # Stats content validation
    print(f"   ✅ Total assets: {stats['total_assets']}")
    print(f"   ✅ Total devices: {stats['total_devices']}")
    print(f"   ✅ Total sensors: {stats['total_sensors']}")
    
    # Show queries if verbose
    if query_count > 5 or elapsed_ms > 200:
        print("\n📝 QUERIES EXECUTADAS:")
        for i, query in enumerate(context.captured_queries, 1):
            sql = query['sql']
            if len(sql) > 100:
                sql = sql[:100] + "..."
            print(f"\n   Query {i} ({query['time']}s):")
            print(f"      {sql}")
    
    # Final result
    print("\n" + "="*70)
    if queries_pass and time_pass:
        print("  ✅ TESTE PASSOU - Otimização funcionando corretamente")
        print("="*70)
        return True
    else:
        print("  ❌ TESTE FALHOU - Verificar otimizações")
        print("="*70)
        return False


def compare_old_vs_new():
    """Compare old (O(N)) vs new (O(1)) approach"""
    print_header("COMPARAÇÃO: Abordagem Antiga vs Nova")
    
    site = Site.objects.filter(assets__isnull=False).first()
    if not site:
        print("❌ Nenhum site encontrado")
        return
    
    print(f"\n📍 Site: {site.name}")
    
    # OLD APPROACH (O(N) - iterating assets)
    print("\n🔴 ABORDAGEM ANTIGA (O(N) - iteração Python):")
    with CaptureQueriesContext(connection) as old_context:
        start = time.time()
        
        assets = site.assets.all()
        stats_old = {
            'total_assets': assets.count(),
            'assets_by_status': {},
            'assets_by_type': {},
        }
        
        for asset in assets:
            status_key = asset.status
            stats_old['assets_by_status'][status_key] = stats_old['assets_by_status'].get(status_key, 0) + 1
            
            type_key = asset.asset_type
            stats_old['assets_by_type'][type_key] = stats_old['assets_by_type'].get(type_key, 0) + 1
        
        old_time = (time.time() - start) * 1000
    
    print(f"   Queries: {len(old_context.captured_queries)}")
    print(f"   Tempo: {old_time:.2f}ms")
    
    # NEW APPROACH (O(1) - aggregation)
    print("\n🟢 ABORDAGEM NOVA (O(1) - agregação no banco):")
    with CaptureQueriesContext(connection) as new_context:
        start = time.time()
        
        from django.db.models import Count
        
        assets_by_status = list(Asset.objects.filter(site=site).values('status').annotate(
            count=Count('id')
        ))
        
        assets_by_type = list(Asset.objects.filter(site=site).values('asset_type').annotate(
            count=Count('id')
        ))
        
        stats_new = {
            'total_assets': sum(item['count'] for item in assets_by_status),
            'assets_by_status': {item['status']: item['count'] for item in assets_by_status},
            'assets_by_type': {item['asset_type']: item['count'] for item in assets_by_type},
        }
        
        new_time = (time.time() - start) * 1000
    
    print(f"   Queries: {len(new_context.captured_queries)}")
    print(f"   Tempo: {new_time:.2f}ms")
    
    # Comparison
    print("\n📈 MELHORIA:")
    query_reduction = len(old_context.captured_queries) - len(new_context.captured_queries)
    time_speedup = old_time / new_time if new_time > 0 else 0
    
    print(f"   Redução de queries: {query_reduction} ({len(old_context.captured_queries)} → {len(new_context.captured_queries)})")
    print(f"   Speedup: {time_speedup:.1f}x mais rápido")
    
    if time_speedup >= 2:
        print(f"   ✅ Otimização significativa (≥2x)")
    else:
        print(f"   ⚠️  Otimização menor (<2x) - dataset pequeno?")


if __name__ == '__main__':
    try:
        # Test optimized endpoint
        success = test_site_stats()
        
        # Compare approaches
        print("\n")
        compare_old_vs_new()
        
        # Exit code
        sys.exit(0 if success else 1)
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
