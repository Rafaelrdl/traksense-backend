# 📡 Provisionamento EMQX - Windows PowerShell

## ✅ Pré-requisitos

### Opção 1: Git Bash (Recomendado)

```powershell
# Verificar se Git Bash está instalado
where.exe bash

# Se não estiver instalado, baixe:
# https://git-scm.com/download/win
```

### Opção 2: WSL (Windows Subsystem for Linux)

```powershell
# Instalar WSL
wsl --install

# Instalar curl e jq no WSL
wsl sudo apt update
wsl sudo apt install curl jq
```

---

## 🚀 Executar Provisionamento

### Método 1: Via Git Bash (Mais simples)

```powershell
# Executar o script
bash docker/scripts/provision-emqx.sh
```

### Método 2: Via WSL

```powershell
# Converter path Windows para WSL
wsl bash /mnt/c/Users/"Rafael Ribeiro"/TrakSense/traksense-backend/docker/scripts/provision-emqx.sh
```

### Método 3: De dentro do container API

```powershell
# Executar de dentro do container (curl e jq já instalados)
docker compose -f docker/docker-compose.yml exec api bash /app/docker/scripts/provision-emqx.sh
```

### Método 4: Com variáveis customizadas

```powershell
# Definir variáveis
$env:TENANT_SLUG="umc"
$env:EMQX_API_KEY="dev-provisioner"
$env:EMQX_API_SECRET="change-me"

# Executar
bash docker/scripts/provision-emqx.sh
```

---

## ✅ Validação

### 1. Verificar no Dashboard

```powershell
# Abrir EMQX Dashboard
Start-Process "http://localhost:18083"

# Login: admin / public
```

**No Dashboard:**
1. Navegue até **Integration → Connectors**
   - Deve aparecer `http_ingest_umc` com status **Connected** ✅
2. Navegue até **Integration → Rules**
   - Deve aparecer `r_umc_ingest` com status **Enabled** ✅

### 2. Testar com MQTT Client

```powershell
# Instalar mosquitto-clients (via Chocolatey)
choco install mosquitto

# Publicar mensagem de teste
mosquitto_pub -h localhost -p 1883 `
  -t "tenants/umc/devices/test-device/sensors/temperature" `
  -m '{"value": 23.5, "unit": "celsius", "timestamp": "2025-10-17T10:30:00Z"}'
```

### 3. Verificar Logs do Backend

```powershell
# Ver logs do API (deve aparecer POST /ingest)
docker compose -f docker/docker-compose.yml logs api --tail=20 | Select-String "ingest"
```

---

## 🐛 Troubleshooting

### Erro: "bash: command not found"

**Causa**: Git Bash não está instalado ou não está no PATH.

**Solução**:
```powershell
# Instalar Git for Windows (inclui Git Bash)
winget install Git.Git

# Ou baixar manualmente:
# https://git-scm.com/download/win

# Após instalar, reiniciar PowerShell
```

---

### Erro: "curl: command not found" (dentro do bash)

**Causa**: Script rodando fora de um ambiente Unix adequado.

**Solução**:
```powershell
# Use o método 3 (de dentro do container)
docker compose -f docker/docker-compose.yml exec api bash /app/docker/scripts/provision-emqx.sh
```

---

### Erro: "Não consegui falar com http://localhost:18083"

**Causa**: EMQX ainda não inicializou completamente.

**Solução**:
```powershell
# Verificar status do EMQX
docker compose -f docker/docker-compose.yml ps emqx

# Se não estiver "healthy", aguardar mais
Start-Sleep -Seconds 10

# Ver logs
docker compose -f docker/docker-compose.yml logs emqx --tail=30

# Tentar novamente
bash docker/scripts/provision-emqx.sh
```

---

### Erro: "Falha no login do dashboard"

**Causa**: Credenciais incorretas ou API Key bootstrap não configurada.

**Solução 1 - Usar API Key**:
```powershell
# Adicionar ao .env
@"
EMQX_API_KEY=dev-provisioner
EMQX_API_SECRET=change-me
"@ | Add-Content .env

# Executar novamente (variáveis serão carregadas)
bash docker/scripts/provision-emqx.sh
```

**Solução 2 - Verificar senha padrão**:
```powershell
# Consultar logs do EMQX para ver credenciais
docker compose -f docker/docker-compose.yml logs emqx | Select-String "password"
```

---

### Mensagens não chegam ao backend

**Diagnóstico**:
```powershell
# 1. Verificar se rule está habilitada (via API)
Invoke-RestMethod -Uri "http://localhost:18083/api/v5/rules/r_umc_ingest" `
  -Headers @{"Authorization"="Basic ZGV2LXByb3Zpc2lvbmVyOmNoYW5nZS1tZQ=="} | ConvertTo-Json

# 2. Publicar mensagem de teste novamente
mosquitto_pub -h localhost -p 1883 `
  -t "tenants/umc/test" `
  -m '{"test": true}'

# 3. Ver logs do API
docker compose -f docker/docker-compose.yml logs api --tail=30

# 4. Ver métricas no Dashboard EMQX
Start-Process "http://localhost:18083"
# Integration → Rules → r_umc_ingest → Metrics
```

---

## 📝 Workflow Completo

```powershell
# ========================================
# SCRIPT COMPLETO - FRESH START
# ========================================

# 1. Limpar ambiente anterior
docker compose -f docker/docker-compose.yml down -v

# 2. Subir serviços
docker compose -f docker/docker-compose.yml up -d

# 3. Aguardar healthchecks
Write-Host "Aguardando healthchecks (45 segundos)..." -ForegroundColor Yellow
Start-Sleep -Seconds 45

# 4. Migrações
docker compose -f docker/docker-compose.yml exec api python manage.py migrate_schemas --noinput

# 5. Seed
docker compose -f docker/docker-compose.yml exec api python manage.py seed_dev

# 6. Provisionar EMQX
bash docker/scripts/provision-emqx.sh

# 7. Validar
Write-Host "`n✅ Validando setup..." -ForegroundColor Green
$health = Invoke-WebRequest -Uri "http://localhost/health" -Headers @{"Host"="umc.localhost"} -UseBasicParsing
if ($health.StatusCode -eq 200) {
    Write-Host "   - Health check: OK" -ForegroundColor Green
} else {
    Write-Host "   - Health check: FALHOU" -ForegroundColor Red
}

# 8. Abrir interfaces
Write-Host "`n🌐 Abrindo interfaces..." -ForegroundColor Cyan
Start-Process "http://localhost/api/docs/"
Start-Process "http://localhost:18083"

# 9. Resumo
Write-Host "`n========================================" -ForegroundColor Magenta
Write-Host "  FASE 0 - SETUP COMPLETO" -ForegroundColor Magenta
Write-Host "========================================" -ForegroundColor Magenta
Write-Host "`n📡 Serviços:" -ForegroundColor White
Write-Host "   - API:       http://localhost" -ForegroundColor Cyan
Write-Host "   - Swagger:   http://localhost/api/docs/" -ForegroundColor Cyan
Write-Host "   - Admin:     http://localhost/admin (owner/Dev@123456)" -ForegroundColor Cyan
Write-Host "   - EMQX:      http://localhost:18083 (admin/public)" -ForegroundColor Cyan
Write-Host "   - MinIO:     http://localhost:9001 (minioadmin/minioadmin123)" -ForegroundColor Cyan
Write-Host "   - Mailpit:   http://localhost:8025" -ForegroundColor Cyan

Write-Host "`n📊 MQTT:" -ForegroundColor White
Write-Host "   - Broker:    mqtt://localhost:1883" -ForegroundColor Cyan
Write-Host "   - Tópicos:   tenants/umc/#" -ForegroundColor Cyan
Write-Host "   - Rule:      r_umc_ingest -> POST /ingest" -ForegroundColor Cyan

Write-Host "`n🧪 Testar ingestão:" -ForegroundColor White
Write-Host '   mosquitto_pub -h localhost -p 1883 \' -ForegroundColor Gray
Write-Host '     -t "tenants/umc/devices/test/sensors/temp" \' -ForegroundColor Gray
Write-Host '     -m ''{"value": 23.5}''' -ForegroundColor Gray

Write-Host "`n" -NoNewline
```

---

## 🔒 Segurança (Produção)

### Gerar API Key Forte

```powershell
# Gerar chave de 32 bytes
$apiSecret = [Convert]::ToBase64String((1..32 | ForEach-Object { Get-Random -Maximum 256 }))
Write-Host "API Secret: $apiSecret"

# Criar arquivo de API Key (NÃO versionar)
@"
prod-provisioner:$apiSecret:administrator
"@ | Out-File -FilePath docker/emqx/prod_api_key.conf -Encoding UTF8 -NoNewline

# Adicionar ao .env
@"
EMQX_API_KEY=prod-provisioner
EMQX_API_SECRET=$apiSecret
"@ | Add-Content .env.production
```

---

## 📚 Referências

- **Documentação EMQX**: https://docs.emqx.com/
- **EMQX API v5**: https://docs.emqx.com/en/emqx/latest/admin/api.html
- **EMQX Rule Engine**: https://docs.emqx.com/en/emqx/latest/data-integration/rules.html
- **Guia Completo**: Ver `EMQX_PROVISIONING.md` no repositório

---

**Última atualização**: 17 de outubro de 2025  
**Versão**: 1.0.0 (Fase 0)
