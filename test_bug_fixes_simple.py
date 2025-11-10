"""
Testes simples para validar as correções dos 5 bugs críticos.
Não requer Django para executar validações básicas.
"""

import os
import re


def test_schema_context_fixes():
    """BUG FIX #2: Verifica que tasks.py usam tenant.schema_name"""
    print("\n🔍 Teste 1: Schema Context com tenant.schema_name")
    print("-" * 60)
    
    files_to_check = [
        ('apps/assets/tasks.py', 2),  # Espera 2 ocorrências
        ('apps/alerts/tasks.py', 1),  # Espera 1 ocorrência
        ('apps/ops/tasks.py', 1),     # Espera 1 ocorrência
    ]
    
    all_passed = True
    for filepath, expected_count in files_to_check:
        full_path = os.path.join(os.path.dirname(__file__), filepath)
        if os.path.exists(full_path):
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Contar ocorrências de schema_context(tenant.schema_name)
            count = content.count('schema_context(tenant.schema_name)')
            
            if count == expected_count:
                print(f"✅ {filepath}: {count} ocorrência(s) de tenant.schema_name")
            else:
                print(f"❌ {filepath}: esperado {expected_count}, encontrado {count}")
                all_passed = False
            
            # Verificar que NÃO usa tenant.slug
            if 'schema_context(tenant.slug)' in content:
                print(f"❌ {filepath}: ainda usa tenant.slug (INCORRETO)")
                all_passed = False
        else:
            print(f"⚠️  {filepath}: arquivo não encontrado")
    
    return all_passed


def test_reading_model_import():
    """BUG FIX #3: Verifica que ops/tasks.py importa Reading"""
    print("\n🔍 Teste 2: Import do modelo Reading")
    print("-" * 60)
    
    filepath = 'apps/ops/tasks.py'
    full_path = os.path.join(os.path.dirname(__file__), filepath)
    
    if os.path.exists(full_path):
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verificar import correto
        has_reading_import = 'from apps.ingest.models import Reading' in content
        uses_reading = 'Reading.objects' in content
        
        # Verificar se usa TelemetryReading (ignorando comentários)
        has_telemetry_code = False
        for line in content.split('\n'):
            # Ignorar comentários
            if 'TelemetryReading' in line and not line.strip().startswith('#'):
                # Verificar se não é parte de comentário inline
                code_part = line.split('#')[0]
                if 'TelemetryReading' in code_part:
                    has_telemetry_code = True
                    break
        
        if has_reading_import and uses_reading and not has_telemetry_code:
            print(f"✅ {filepath}: importa e usa Reading corretamente")
            print(f"✅ {filepath}: não usa TelemetryReading no código")
            return True
        else:
            if not has_reading_import:
                print(f"❌ {filepath}: não importa Reading")
            if not uses_reading:
                print(f"❌ {filepath}: não usa Reading.objects")
            if has_telemetry_code:
                print(f"❌ {filepath}: ainda referencia TelemetryReading no código")
            return False
    else:
        print(f"⚠️  {filepath}: arquivo não encontrado")
        return False


def test_cursor_management():
    """BUG FIX #4: Verifica que cursor não é usado fora do contexto"""
    print("\n🔍 Teste 3: Cursor Management no DeviceSummaryView")
    print("-" * 60)
    
    filepath = 'apps/ingest/api_views_extended.py'
    full_path = os.path.join(os.path.dirname(__file__), filepath)
    
    if os.path.exists(full_path):
        with open(full_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Procurar padrões problemáticos
        issues = []
        in_with_block = False
        with_indent = 0
        
        for i, line in enumerate(lines, 1):
            # Detectar início do with
            if 'with connection.cursor() as cursor:' in line:
                in_with_block = True
                with_indent = len(line) - len(line.lstrip())
                continue
            
            # Detectar fim do with (linha com indentação menor ou igual)
            if in_with_block:
                current_indent = len(line) - len(line.lstrip())
                if line.strip() and current_indent <= with_indent:
                    in_with_block = False
            
            # Verificar uso de cursor fora do with
            if 'cursor.execute' in line and not in_with_block:
                if 'with connection.cursor() as cursor:' not in line:
                    issues.append((i, line.strip()))
        
        if not issues:
            print(f"✅ {filepath}: todas as queries estão dentro do contexto")
            return True
        else:
            print(f"❌ {filepath}: {len(issues)} uso(s) de cursor fora do contexto:")
            for line_num, line_content in issues:
                print(f"   Linha {line_num}: {line_content[:60]}")
            return False
    else:
        print(f"⚠️  {filepath}: arquivo não encontrado")
        return False


def test_tenant_storage_no_circular_import():
    """BUG FIX #1: Verifica que tenantStorage não importa getTenantConfig"""
    print("\n🔍 Teste 4: tenantStorage sem dependência circular")
    print("-" * 60)
    
    filepath = '../traksense-hvac-monit/src/lib/tenantStorage.ts'
    full_path = os.path.join(os.path.dirname(__file__), filepath)
    
    if os.path.exists(full_path):
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verificar que NÃO importa getTenantConfig (ignorando comentários)
        has_import = False
        for line in content.split('\n'):
            # Ignorar comentários
            if 'getTenantConfig' in line and 'import' in line:
                if not line.strip().startswith('//') and not line.strip().startswith('*'):
                    has_import = True
                    break
        
        has_cache = 'cachedTenantSlug' in content
        has_detect = 'detectTenantSlug' in content
        has_update = 'updateTenantSlugCache' in content
        
        if not has_import and has_cache and has_detect and has_update:
            print(f"✅ tenantStorage.ts: não importa getTenantConfig")
            print(f"✅ tenantStorage.ts: implementa cache (cachedTenantSlug)")
            print(f"✅ tenantStorage.ts: implementa detectTenantSlug()")
            print(f"✅ tenantStorage.ts: exporta updateTenantSlugCache()")
            return True
        else:
            if has_import:
                print(f"❌ tenantStorage.ts: ainda importa getTenantConfig")
            if not has_cache:
                print(f"❌ tenantStorage.ts: não tem cachedTenantSlug")
            if not has_detect:
                print(f"❌ tenantStorage.ts: não tem detectTenantSlug")
            if not has_update:
                print(f"❌ tenantStorage.ts: não exporta updateTenantSlugCache")
            return False
    else:
        print(f"⚠️  {filepath}: arquivo não encontrado")
        return False


def test_base64url_jwt_decoding():
    """BUG FIX #5: Verifica que JWT decodifica base64url corretamente"""
    print("\n🔍 Teste 5: JWT Base64url Decoding")
    print("-" * 60)
    
    filepath = '../traksense-hvac-monit/src/services/tenantAuthService.ts'
    full_path = os.path.join(os.path.dirname(__file__), filepath)
    
    if os.path.exists(full_path):
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verificar normalização base64url
        has_normalize = "replace(/-/g, '+')" in content and "replace(/_/g, '/')" in content
        has_padding = "'='.repeat(" in content
        
        if has_normalize and has_padding:
            print(f"✅ tenantAuthService.ts: normaliza base64url → base64")
            print(f"✅ tenantAuthService.ts: adiciona padding correto")
            return True
        else:
            if not has_normalize:
                print(f"❌ tenantAuthService.ts: não normaliza base64url")
            if not has_padding:
                print(f"❌ tenantAuthService.ts: não adiciona padding")
            return False
    else:
        print(f"⚠️  {filepath}: arquivo não encontrado")
        return False


def main():
    """Executa todos os testes"""
    print("\n" + "=" * 70)
    print("🧪 TESTES DE VALIDAÇÃO DAS CORREÇÕES DE BUGS")
    print("=" * 70)
    
    results = []
    
    # Executar testes
    results.append(("Schema Context (tenant.schema_name)", test_schema_context_fixes()))
    results.append(("Import Reading Model", test_reading_model_import()))
    results.append(("Cursor Management", test_cursor_management()))
    results.append(("tenantStorage sem circular import", test_tenant_storage_no_circular_import()))
    results.append(("JWT Base64url Decoding", test_base64url_jwt_decoding()))
    
    # Resumo
    print("\n" + "=" * 70)
    print("📊 RESUMO DOS TESTES")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{status}: {test_name}")
    
    print("-" * 70)
    print(f"Total: {passed}/{total} testes passaram ({passed/total*100:.0f}%)")
    print("=" * 70 + "\n")
    
    return 0 if passed == total else 1


if __name__ == '__main__':
    exit(main())
