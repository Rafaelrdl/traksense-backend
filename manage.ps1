# TrakSense - Scripts PowerShell para Gerenciamento
# Use estes comandos em vez do Makefile se não tiver Make instalado

param(
    [Parameter(Position=0)]
    [string]$Command
)

$ComposeFile = "infra/docker-compose.yml"

function Show-Help {
    Write-Host "TrakSense - Comandos disponíveis:" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  .\manage.ps1 up        " -NoNewline -ForegroundColor Green
    Write-Host "- Sobe todos os serviços"
    Write-Host "  .\manage.ps1 down      " -NoNewline -ForegroundColor Green
    Write-Host "- Derruba serviços e remove volumes"
    Write-Host "  .\manage.ps1 logs      " -NoNewline -ForegroundColor Green
    Write-Host "- Exibe logs em tempo real"
    Write-Host "  .\manage.ps1 ps        " -NoNewline -ForegroundColor Green
    Write-Host "- Lista status dos containers"
    Write-Host "  .\manage.ps1 migrate   " -NoNewline -ForegroundColor Green
    Write-Host "- Executa migrações Django"
    Write-Host "  .\manage.ps1 seed      " -NoNewline -ForegroundColor Green
    Write-Host "- Executa script de seed"
    Write-Host "  .\manage.ps1 frontend  " -NoNewline -ForegroundColor Green
    Write-Host "- Ativa serviço frontend"
    Write-Host "  .\manage.ps1 shell     " -NoNewline -ForegroundColor Green
    Write-Host "- Abre Django shell"
    Write-Host "  .\manage.ps1 bash      " -NoNewline -ForegroundColor Green
    Write-Host "- Abre bash no container API"
    Write-Host "  .\manage.ps1 health    " -NoNewline -ForegroundColor Green
    Write-Host "- Testa endpoint /health"
    Write-Host ""
}

function Invoke-Up {
    Write-Host "Subindo serviços TrakSense..." -ForegroundColor Cyan
    docker compose -f $ComposeFile up -d --build
    Write-Host "Serviços iniciados! Acesse:" -ForegroundColor Green
    Write-Host "  - API: http://localhost:8000/health" -ForegroundColor Yellow
    Write-Host "  - EMQX: http://localhost:18083" -ForegroundColor Yellow
}

function Invoke-Down {
    Write-Host "Derrubando serviços..." -ForegroundColor Cyan
    docker compose -f $ComposeFile down -v
}

function Invoke-Logs {
    docker compose -f $ComposeFile logs -f --tail=200
}

function Invoke-PS {
    docker compose -f $ComposeFile ps
}

function Invoke-Migrate {
    Write-Host "Executando migrações..." -ForegroundColor Cyan
    docker compose -f $ComposeFile exec api python manage.py migrate
}

function Invoke-Seed {
    Write-Host "Executando seed..." -ForegroundColor Cyan
    docker compose -f $ComposeFile exec api python scripts/seed_dev.py
}

function Invoke-Frontend {
    Write-Host "Ativando frontend (profile)..." -ForegroundColor Cyan
    docker compose -f $ComposeFile --profile frontend up -d --build
}

function Invoke-Shell {
    docker compose -f $ComposeFile exec api python manage.py shell
}

function Invoke-Bash {
    docker compose -f $ComposeFile exec api bash
}

function Invoke-Health {
    Write-Host "Testando endpoint /health..." -ForegroundColor Cyan
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing
        Write-Host "Status: $($response.StatusCode)" -ForegroundColor Green
        Write-Host "Response: $($response.Content)" -ForegroundColor Green
    }
    catch {
        Write-Host "Erro ao acessar /health: $_" -ForegroundColor Red
    }
}

# Main
switch ($Command) {
    "up"       { Invoke-Up }
    "down"     { Invoke-Down }
    "logs"     { Invoke-Logs }
    "ps"       { Invoke-PS }
    "migrate"  { Invoke-Migrate }
    "seed"     { Invoke-Seed }
    "frontend" { Invoke-Frontend }
    "shell"    { Invoke-Shell }
    "bash"     { Invoke-Bash }
    "health"   { Invoke-Health }
    default    { Show-Help }
}
