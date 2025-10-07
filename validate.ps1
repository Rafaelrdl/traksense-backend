# Script de Validação Automatizada - TrakSense Fase 1
# Execute: .\validate.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "TrakSense - Validação Automática (Fase 1)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$ErrorCount = 0
$WarningCount = 0

function Test-Step {
    param(
        [string]$Description,
        [scriptblock]$Test,
        [bool]$Critical = $true
    )
    
    Write-Host "🔍 Testando: $Description" -NoNewline
    try {
        $result = & $Test
        if ($result) {
            Write-Host " ✅" -ForegroundColor Green
            return $true
        } else {
            Write-Host " ❌" -ForegroundColor Red
            if ($Critical) { $script:ErrorCount++ } else { $script:WarningCount++ }
            return $false
        }
    }
    catch {
        Write-Host " ❌" -ForegroundColor Red
        Write-Host "   Erro: $_" -ForegroundColor Red
        if ($Critical) { $script:ErrorCount++ } else { $script:WarningCount++ }
        return $false
    }
}

# 1. Verificar Docker
Write-Host "`n📦 Verificando Docker..." -ForegroundColor Yellow
Test-Step "Docker está rodando" {
    $null -ne (docker ps 2>$null)
}

# 2. Verificar estrutura de pastas
Write-Host "`n📁 Verificando estrutura de pastas..." -ForegroundColor Yellow
Test-Step "Pasta backend/ existe" {
    Test-Path "backend"
}
Test-Step "Pasta ingest/ existe" {
    Test-Path "ingest"
}
Test-Step "Pasta infra/ existe" {
    Test-Path "infra"
}
Test-Step "docker-compose.yml existe" {
    Test-Path "infra/docker-compose.yml"
}

# 3. Verificar arquivos .env
Write-Host "`n⚙️  Verificando arquivos de configuração..." -ForegroundColor Yellow
Test-Step "Arquivo .env.api existe" {
    Test-Path "infra/.env.api"
}
Test-Step "Arquivo .env.ingest existe" {
    Test-Path "infra/.env.ingest"
}

# 4. Verificar containers
Write-Host "`n🐳 Verificando containers..." -ForegroundColor Yellow
$containers = docker compose -f infra/docker-compose.yml ps --format json 2>$null | ConvertFrom-Json

Test-Step "Container 'api' está rodando" {
    ($containers | Where-Object { $_.Service -eq "api" -and $_.State -eq "running" }) -ne $null
}
Test-Step "Container 'db' está rodando" {
    ($containers | Where-Object { $_.Service -eq "db" -and $_.State -eq "running" }) -ne $null
}
Test-Step "Container 'redis' está rodando" {
    ($containers | Where-Object { $_.Service -eq "redis" -and $_.State -eq "running" }) -ne $null
}
Test-Step "Container 'emqx' está rodando" {
    ($containers | Where-Object { $_.Service -eq "emqx" -and $_.State -eq "running" }) -ne $null
}

# 5. Testar endpoints
Write-Host "`n🌐 Testando endpoints..." -ForegroundColor Yellow

Test-Step "API Health Check (http://localhost:8000/health)" {
    Start-Sleep -Seconds 2  # Aguardar API inicializar
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 5
        $response.StatusCode -eq 200 -and $response.Content -like '*"status"*"ok"*'
    }
    catch {
        $false
    }
}

Test-Step "EMQX Dashboard (http://localhost:18083)" {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:18083" -UseBasicParsing -TimeoutSec 5
        $response.StatusCode -eq 200
    }
    catch {
        $false
    }
} -Critical $false

# 6. Testar conectividade dos serviços
Write-Host "`n🔌 Testando conectividade..." -ForegroundColor Yellow

Test-Step "PostgreSQL aceita conexões" {
    $output = docker compose -f infra/docker-compose.yml exec -T db psql -U postgres -d traksense -c "\dt" 2>$null
    $LASTEXITCODE -eq 0
}

Test-Step "Redis responde ao PING" {
    $output = docker compose -f infra/docker-compose.yml exec -T redis redis-cli ping 2>$null
    $output -match "PONG"
}

# 7. Verificar logs de erros
Write-Host "`n📋 Verificando logs..." -ForegroundColor Yellow

Test-Step "API sem erros críticos nos logs" {
    $logs = docker compose -f infra/docker-compose.yml logs api --tail=50 2>$null
    -not ($logs -match "ERROR|CRITICAL|Exception" -and $logs -notmatch "django.request")
} -Critical $false

Test-Step "Ingest conectou ao MQTT" {
    $logs = docker compose -f infra/docker-compose.yml logs ingest --tail=50 2>$null
    $logs -match "connected ok"
} -Critical $false

# Resumo
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Resumo da Validação" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

if ($ErrorCount -eq 0 -and $WarningCount -eq 0) {
    Write-Host "✅ SUCESSO! Todos os testes passaram." -ForegroundColor Green
    Write-Host "`nFase 1 está completa e funcional! 🎉" -ForegroundColor Green
    Write-Host "`nPróximos passos:" -ForegroundColor Yellow
    Write-Host "  - Acesse a API: http://localhost:8000/health" -ForegroundColor Gray
    Write-Host "  - Acesse EMQX: http://localhost:18083" -ForegroundColor Gray
    Write-Host "  - Veja os logs: .\manage.ps1 logs" -ForegroundColor Gray
    exit 0
}
elseif ($ErrorCount -eq 0) {
    Write-Host "⚠️  Testes passaram com $WarningCount aviso(s)." -ForegroundColor Yellow
    Write-Host "`nSistema funcional, mas verifique os avisos acima." -ForegroundColor Yellow
    exit 0
}
else {
    Write-Host "❌ FALHOU! $ErrorCount erro(s) crítico(s) encontrado(s)." -ForegroundColor Red
    if ($WarningCount -gt 0) {
        Write-Host "⚠️  $WarningCount aviso(s) adicional(is)." -ForegroundColor Yellow
    }
    Write-Host "`nPor favor, corrija os erros acima." -ForegroundColor Red
    Write-Host "`nDicas:" -ForegroundColor Yellow
    Write-Host "  - Certifique-se de que os serviços estão rodando: .\manage.ps1 up" -ForegroundColor Gray
    Write-Host "  - Verifique os logs: .\manage.ps1 logs" -ForegroundColor Gray
    Write-Host "  - Reconstrua os containers: .\manage.ps1 down; .\manage.ps1 up" -ForegroundColor Gray
    exit 1
}
