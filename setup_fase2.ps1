# ============================================================================
# Setup Fase 2 - TrakSense Backend
# ============================================================================
# Script PowerShell para configurar a Fase 2 (Modelos de Domínio)
#
# Uso:
#   .\setup_fase2.ps1
#
# Pré-requisitos:
#   - Python ambiente virtual ativado
#   - PostgreSQL rodando
#   - .env.api configurado
# ============================================================================

Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "🚀 SETUP FASE 2 - MODELOS DE DOMÍNIO" -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""

# Verificar se está na pasta raiz do projeto
if (-not (Test-Path ".\backend\manage.py")) {
    Write-Host "❌ Erro: Execute este script da pasta raiz do projeto!" -ForegroundColor Red
    exit 1
}

# Navegar para pasta backend
Set-Location .\backend

# ============================================================================
# STEP 1: Instalar dependências
# ============================================================================
Write-Host ""
Write-Host "============================================================================" -ForegroundColor Yellow
Write-Host "📦 Step 1: Instalando dependências..." -ForegroundColor Yellow
Write-Host "============================================================================" -ForegroundColor Yellow
Write-Host ""

pip install jsonschema>=4.22

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Erro ao instalar dependências!" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Dependências instaladas com sucesso!" -ForegroundColor Green

# ============================================================================
# STEP 2: Criar migrations
# ============================================================================
Write-Host ""
Write-Host "============================================================================" -ForegroundColor Yellow
Write-Host "🔧 Step 2: Criando migrations..." -ForegroundColor Yellow
Write-Host "============================================================================" -ForegroundColor Yellow
Write-Host ""

python manage.py makemigrations devices
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️ Aviso: Erro ao criar migrations para devices" -ForegroundColor Yellow
}

python manage.py makemigrations dashboards
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️ Aviso: Erro ao criar migrations para dashboards" -ForegroundColor Yellow
}

Write-Host "✅ Migrations criadas!" -ForegroundColor Green

# ============================================================================
# STEP 3: Aplicar migrations (shared)
# ============================================================================
Write-Host ""
Write-Host "============================================================================" -ForegroundColor Yellow
Write-Host "🗄️  Step 3: Aplicando migrations (shared apps)..." -ForegroundColor Yellow
Write-Host "============================================================================" -ForegroundColor Yellow
Write-Host ""

python manage.py migrate_schemas --shared
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️ Aviso: Erro ao aplicar migrations (shared)" -ForegroundColor Yellow
}

Write-Host "✅ Migrations aplicadas (shared)!" -ForegroundColor Green

# ============================================================================
# STEP 4: Aplicar migrations (tenants)
# ============================================================================
Write-Host ""
Write-Host "============================================================================" -ForegroundColor Yellow
Write-Host "🗄️  Step 4: Aplicando migrations (tenant apps)..." -ForegroundColor Yellow
Write-Host "============================================================================" -ForegroundColor Yellow
Write-Host ""

python manage.py migrate_schemas
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️ Aviso: Erro ao aplicar migrations (tenants)" -ForegroundColor Yellow
}

Write-Host "✅ Migrations aplicadas (todos os schemas)!" -ForegroundColor Green

# ============================================================================
# STEP 5: Seed device templates
# ============================================================================
Write-Host ""
Write-Host "============================================================================" -ForegroundColor Yellow
Write-Host "🌱 Step 5: Criando templates de devices..." -ForegroundColor Yellow
Write-Host "============================================================================" -ForegroundColor Yellow
Write-Host ""

python manage.py seed_device_templates
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Erro ao criar device templates!" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Device templates criados!" -ForegroundColor Green

# ============================================================================
# STEP 6: Seed dashboard templates
# ============================================================================
Write-Host ""
Write-Host "============================================================================" -ForegroundColor Yellow
Write-Host "🌱 Step 6: Criando templates de dashboards..." -ForegroundColor Yellow
Write-Host "============================================================================" -ForegroundColor Yellow
Write-Host ""

python manage.py seed_dashboard_templates
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Erro ao criar dashboard templates!" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Dashboard templates criados!" -ForegroundColor Green

# ============================================================================
# RESUMO
# ============================================================================
Write-Host ""
Write-Host "============================================================================" -ForegroundColor Green
Write-Host "✅ SETUP FASE 2 CONCLUÍDO COM SUCESSO!" -ForegroundColor Green
Write-Host "============================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Próximos passos:" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Criar superusuário (se ainda não existe):" -ForegroundColor White
Write-Host "   python manage.py createsuperuser" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Adicionar usuário ao grupo internal_ops:" -ForegroundColor White
Write-Host "   python manage.py shell" -ForegroundColor Gray
Write-Host "   >>> from django.contrib.auth.models import User, Group" -ForegroundColor Gray
Write-Host "   >>> user = User.objects.get(username='seu_usuario')" -ForegroundColor Gray
Write-Host "   >>> group = Group.objects.get(name='internal_ops')" -ForegroundColor Gray
Write-Host "   >>> user.groups.add(group)" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Acessar Django Admin:" -ForegroundColor White
Write-Host "   python manage.py runserver" -ForegroundColor Gray
Write-Host "   Abrir: http://localhost:8000/admin/" -ForegroundColor Gray
Write-Host ""
Write-Host "4. Criar um Device e ver o provisionamento automático!" -ForegroundColor White
Write-Host ""
Write-Host "📖 Para mais informações, consulte: backend/apps/README_FASE2.md" -ForegroundColor Cyan
Write-Host ""

# Voltar para pasta raiz
Set-Location ..
