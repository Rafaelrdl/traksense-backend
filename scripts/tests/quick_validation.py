#!/usr/bin/env python
"""
Validação Rápida - Correções de Integração & Performance

Executa validações rápidas para confirmar que todas as 13 correções
foram implementadas corretamente.

Uso:
    python scripts/tests/quick_validation.py
"""

import os
import sys
import subprocess

# Setup paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

import django
django.setup()

from django.conf import settings
from django.db import connection
from apps.accounts.models import User, TenantMembership
from apps.assets.models import Site, Asset
from apps.tenants.models import Tenant


def print_header(title, emoji="📋"):
    """Print formatted header"""
    print("\n" + "="*70)
    print(f"  {emoji} {title}")
    print("="*70)


def check_mark(condition, true_msg, false_msg):
    """Print check mark based on condition"""
    if condition:
        print(f"   ✅ {true_msg}")
        return True
    else:
        print(f"   ❌ {false_msg}")
        return False


def validate_backend():
    """Validate backend corrections"""
    print_header("BACKEND - 7 Correções", "🔧")
    
    results = []
    
    # 1. TenantMembership Import
    print("\n1️⃣  TenantMembership Import")
    try:
        from apps.accounts.models import TenantMembership
        # Check if model is accessible
        fields = [f.name for f in TenantMembership._meta.fields]
        has_required = 'user' in fields and 'tenant' in fields and 'role' in fields
        results.append(check_mark(
            has_required,
            "TenantMembership model importável e correto",
            "TenantMembership com campos faltando"
        ))
    except ImportError as e:
        results.append(check_mark(False, "", f"TenantMembership não importável: {e}"))
    
    # 2. last_login Update
    print("\n2️⃣  last_login Update")
    # Check if LoginView updates last_login
    from apps.accounts import views
    import inspect
    login_view_source = inspect.getsource(views.LoginView.post)
    has_last_login = 'last_login' in login_view_source and 'timezone.now()' in login_view_source
    results.append(check_mark(
        has_last_login,
        "LoginView atualiza last_login explicitamente",
        "LoginView não atualiza last_login"
    ))
    
    # 3. FRONTEND_URL Configuration
    print("\n3️⃣  FRONTEND_URL Configuration")
    has_frontend_url = hasattr(settings, 'FRONTEND_URL')
    if has_frontend_url:
        results.append(check_mark(
            True,
            f"FRONTEND_URL configurado: {settings.FRONTEND_URL}",
            "FRONTEND_URL não configurado"
        ))
    else:
        results.append(check_mark(False, "", "FRONTEND_URL não encontrado em settings"))
    
    # 4. SiteViewSet.stats Optimization
    print("\n4️⃣  SiteViewSet.stats Optimization")
    from apps.assets import views as asset_views
    stats_source = inspect.getsource(asset_views.SiteViewSet.stats)
    uses_aggregate = 'annotate' in stats_source and 'aggregate' in stats_source
    results.append(check_mark(
        uses_aggregate,
        "SiteViewSet.stats usa queries agregadas (annotate/aggregate)",
        "SiteViewSet.stats não usa agregação"
    ))
    
    # 5. Sensor Bulk Create
    print("\n5️⃣  Sensor Bulk Create")
    from apps.assets import serializers
    bulk_source = inspect.getsource(serializers.SensorBulkCreateSerializer.create)
    uses_atomic = 'transaction.atomic' in bulk_source
    uses_bulk = 'bulk_create' in bulk_source
    results.append(check_mark(
        uses_atomic and uses_bulk,
        "Sensor bulk create usa transaction.atomic + bulk_create",
        "Sensor bulk create não otimizado"
    ))
    
    # 6. Readings Insert Count
    print("\n6️⃣  Readings Insert Count")
    from apps.ingest import views as ingest_views
    ingest_source = inspect.getsource(ingest_views.IngestView.post)
    counts_inserts = 'count_before' in ingest_source or 'count_after' in ingest_source
    results.append(check_mark(
        counts_inserts,
        "Ingest captura contagem real de inserts",
        "Ingest não captura contagem real"
    ))
    
    # 7. Rules Evaluation N+1
    print("\n7️⃣  Rules Evaluation N+1")
    from apps.alerts import tasks
    eval_source = inspect.getsource(tasks.evaluate_single_rule)
    uses_prefetch = 'select_related' in eval_source or 'sensors_dict' in eval_source
    results.append(check_mark(
        uses_prefetch,
        "Rule evaluation usa prefetch/select_related",
        "Rule evaluation tem N+1 queries"
    ))
    
    return results


def validate_frontend():
    """Validate frontend corrections"""
    print_header("FRONTEND - 6 Correções", "🎨")
    
    results = []
    
    frontend_path = os.path.join(os.path.dirname(__file__), '../../..', 'traksense-hvac-monit')
    
    # 1. API Interceptor Documentation
    print("\n1️⃣  API Interceptor Documentation")
    api_file = os.path.join(frontend_path, 'src/lib/api.ts')
    if os.path.exists(api_file):
        with open(api_file, 'r', encoding='utf-8') as f:
            content = f.read()
        has_docs = 'AUTHENTICATION STRATEGY' in content and 'HttpOnly cookies' in content
        results.append(check_mark(
            has_docs,
            "api.ts tem documentação sobre estratégia HttpOnly",
            "api.ts sem documentação de autenticação"
        ))
    else:
        results.append(check_mark(False, "", "api.ts não encontrado"))
    
    # 2. Registration API URL
    print("\n2️⃣  Registration API URL")
    auth_file = os.path.join(frontend_path, 'src/services/tenantAuthService.ts')
    if os.path.exists(auth_file):
        with open(auth_file, 'r', encoding='utf-8') as f:
            content = f.read()
        uses_full_url = 'reconfigureApiForTenant(apiBaseUrl)' in content
        results.append(check_mark(
            uses_full_url,
            "tenantAuthService usa api_base_url completo",
            "tenantAuthService usa apenas slug"
        ))
    else:
        results.append(check_mark(False, "", "tenantAuthService.ts não encontrado"))
    
    # 3. Token Storage Removal
    print("\n3️⃣  Token Storage Removal (Registration)")
    if os.path.exists(auth_file):
        # Check if token storage is commented/removed in register
        lines = content.split('\n')
        in_register = False
        token_storage_commented = False
        for line in lines:
            if 'async register' in line:
                in_register = True
            if in_register and ('tenantStorage.set(\'access_token\'' in line or 'localStorage.setItem(\'access_token\'' in line):
                if line.strip().startswith('//'):
                    token_storage_commented = True
                    break
        results.append(check_mark(
            token_storage_commented,
            "Tokens não são duplicados em registro",
            "Tokens ainda duplicados em registro"
        ))
    else:
        results.append(check_mark(False, "", "Não foi possível verificar"))
    
    # 4. Pagination Helper
    print("\n4️⃣  Pagination Helper Extraction")
    pagination_file = os.path.join(frontend_path, 'src/lib/pagination.ts')
    pagination_exists = os.path.exists(pagination_file)
    if pagination_exists:
        with open(pagination_file, 'r', encoding='utf-8') as f:
            content = f.read()
        has_helper = 'fetchAllPages' in content
        results.append(check_mark(
            has_helper,
            "src/lib/pagination.ts criado com fetchAllPages",
            "pagination.ts sem helper"
        ))
    else:
        results.append(check_mark(False, "", "src/lib/pagination.ts não existe"))
    
    # 5. SECURITY.md Deduplication
    print("\n5️⃣  SECURITY.md Deduplication")
    root_security = os.path.join(frontend_path, 'SECURITY.md')
    docs_security = os.path.join(frontend_path, 'docs/SECURITY.md')
    root_exists = os.path.exists(root_security)
    docs_exists = os.path.exists(docs_security)
    results.append(check_mark(
        root_exists and not docs_exists,
        "SECURITY.md apenas na raiz (docs/ removido)",
        f"Duplicação: root={root_exists}, docs={docs_exists}"
    ))
    
    # 6. Empty Files Removed
    print("\n6️⃣  Empty Files Cleanup")
    empty_files = [
        'src/store/abtest.ts',
        'src/components/brand/TrakSenseWordmark.tsx',
        'src/components/notifications/NotificationBell.tsx',
        'src/components/assets/TrakNorCTAPro.tsx',
        'src/modules/assets/AssetStatusFilter.tsx'
    ]
    all_removed = all(not os.path.exists(os.path.join(frontend_path, f)) for f in empty_files)
    results.append(check_mark(
        all_removed,
        "Todos os 5 arquivos vazios foram removidos",
        "Alguns arquivos vazios ainda existem"
    ))
    
    return results


def check_environment():
    """Check environment configuration"""
    print_header("ENVIRONMENT - Configuração", "⚙️")
    
    results = []
    
    # Check .env.example
    print("\n📝 Verificando .env.example")
    env_example = os.path.join(os.path.dirname(__file__), '../..', '.env.example')
    if os.path.exists(env_example):
        with open(env_example, 'r', encoding='utf-8') as f:
            content = f.read()
        
        has_frontend_url = 'FRONTEND_URL' in content
        has_ingestion = 'INGESTION_SECRET' in content
        
        results.append(check_mark(
            has_frontend_url,
            "FRONTEND_URL documentado em .env.example",
            "FRONTEND_URL não em .env.example"
        ))
        
        results.append(check_mark(
            has_ingestion,
            "INGESTION_SECRET documentado em .env.example",
            "INGESTION_SECRET não em .env.example"
        ))
    else:
        results.append(check_mark(False, "", ".env.example não encontrado"))
    
    return results


def print_summary(backend_results, frontend_results, env_results):
    """Print validation summary"""
    print_header("RESUMO", "📊")
    
    total = len(backend_results) + len(frontend_results) + len(env_results)
    passed = sum(backend_results + frontend_results + env_results)
    
    print(f"\n   Backend: {sum(backend_results)}/{len(backend_results)} ✅")
    print(f"   Frontend: {sum(frontend_results)}/{len(frontend_results)} ✅")
    print(f"   Environment: {sum(env_results)}/{len(env_results)} ✅")
    print(f"\n   TOTAL: {passed}/{total} correções validadas")
    
    percentage = (passed / total * 100) if total > 0 else 0
    
    if percentage == 100:
        print("\n   🎉 TODAS AS CORREÇÕES VALIDADAS!")
        return True
    elif percentage >= 80:
        print(f"\n   ⚠️  {100-percentage:.0f}% pendente - revisar itens falhados")
        return False
    else:
        print(f"\n   ❌ {100-percentage:.0f}% pendente - várias correções falharam")
        return False


if __name__ == '__main__':
    print_header("VALIDAÇÃO RÁPIDA - Correções de Integração", "🚀")
    print("\nValidando 13 correções implementadas...")
    
    try:
        # Run validations
        backend_results = validate_backend()
        frontend_results = validate_frontend()
        env_results = check_environment()
        
        # Print summary
        success = print_summary(backend_results, frontend_results, env_results)
        
        print("\n" + "="*70)
        if success:
            print("  ✅ VALIDAÇÃO COMPLETA - Pronto para deploy")
        else:
            print("  ⚠️  VALIDAÇÃO PARCIAL - Revisar itens falhados")
        print("="*70 + "\n")
        
        sys.exit(0 if success else 1)
        
    except Exception as e:
        print(f"\n❌ ERRO NA VALIDAÇÃO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
