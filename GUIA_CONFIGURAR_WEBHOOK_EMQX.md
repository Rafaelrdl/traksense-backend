# 🔧 Guia: Configurar Webhook EMQX para Telemetria

**Data:** 20/10/2025 00:30  
**Objetivo:** Configurar regra EMQX para enviar telemetria ao backend via HTTP webhook

---

## 📋 Resumo

**Problema Detectado:**
- ✅ Mensagem MQTT publicada com sucesso
- ❌ Webhook EMQX com erro: `nxdomain` (não resolve DNS `traksense-api`)
- ❌ Telemetria não chega no backend

**Solução:**
Configurar webhook manualmente via Dashboard EMQX

---

## 🌐 Acessar Dashboard EMQX

### Passo 1: Abrir Dashboard

```
URL: http://localhost:18083
Usuário: admin
Senha: public
```

---

## 🔌 Configurar Conector HTTP

### Passo 2: Criar Conector

1. **Menu lateral:** Integration → Connectors
2. **Botão:** `+ Create`
3. **Tipo:** HTTP Server
4. **Nome:** `http_ingest_backend`

### Passo 3: Configurar Conector

**URL do Backend:**
```
http://traksense-api:8000/ingest
```

⚠️ **IMPORTANTE:** 
- Use `traksense-api` (nome do container)
- **NÃO** use `localhost` ou `umc.localhost`
- Porta: `8000` (porta interna do container)

**Método HTTP:**
```
POST
```

**Headers:**
```json
{
  "Content-Type": "application/json",
  "X-Tenant": "umc"
}
```

**Body Template:**
```json
{
  "client_id": "${clientid}",
  "username": "${username}",
  "topic": "${topic}",
  "qos": ${qos},
  "payload": ${payload},
  "ts": ${timestamp}
}
```

**Resource Options:**
- Request Timeout: `30s`
- Max Retry: `3`
- Health Check Interval: `15s`

**Clique:** `Create`

---

## 📝 Criar Regra (Rule)

### Passo 4: Criar Regra

1. **Menu lateral:** Integration → Rules
2. **Botão:** `+ Create`

### Passo 5: Configurar SQL da Regra

**Nome:**
```
telemetry_ingest_rule
```

**SQL Statement:**
```sql
SELECT
  clientid,
  username,
  topic,
  qos,
  payload,
  timestamp
FROM
  "traksense/#"
WHERE
  topic =~ 'traksense/*/telemetry'
```

**Descrição:**
```
Captura todas as mensagens publicadas em traksense/{device_id}/telemetry
e envia para o backend via HTTP webhook.
```

### Passo 6: Adicionar Action

1. **Section:** Actions
2. **Botão:** `+ Add Action`
3. **Tipo:** `Connector`
4. **Selecionar:** `http_ingest_backend` (criado no Passo 3)

**Clique:** `Create`

---

## ✅ Testar Configuração

### Passo 7: Publicar Mensagem Teste

Execute o script Python novamente:

```powershell
cd "c:\Users\Rafael Ribeiro\TrakSense\traksense-backend"
python publish_test_telemetry.py
```

### Passo 8: Verificar Logs

**EMQX Dashboard:**
1. Menu: `Monitoring` → `Rules`
2. Clicar na regra: `telemetry_ingest_rule`
3. Ver estatísticas: `Matched`, `Passed`, `Failed`

**Backend Logs:**
```powershell
docker logs traksense-api --tail 20
```

**Deve aparecer:**
```
✅ Telemetry received: device=GW-1760908415, sensors=4
✅ Saved 4 readings to database
```

---

## 🔍 Troubleshooting

### Problema: Webhook continua com erro `nxdomain`

**Causa:** EMQX não resolve nome do container

**Solução 1 - Usar IP do Container:**
```bash
# Descobrir IP do container
docker inspect traksense-api | Select-String "IPAddress"

# Usar IP na URL do webhook
# Exemplo: http://172.20.0.5:8000/ingest
```

**Solução 2 - Verificar Network:**
```bash
# Verificar se EMQX e API estão na mesma rede Docker
docker network inspect traksense-network

# Deve mostrar ambos os containers
```

---

### Problema: Webhook retorna erro 404

**Causa:** URL incorreta

**Verificar:**
- ✅ URL: `http://traksense-api:8000/ingest` (correto)
- ❌ URL: `http://traksense-api:8000/api/ingest` (errado - `/api` a mais)

---

### Problema: Webhook retorna erro 403 Forbidden

**Causa:** CSRF validation

**Solução:** Endpoint `/ingest` já tem `@csrf_exempt` - não deveria dar 403

---

### Problema: Telemetria não aparece na UI

**Causa:** Dados gravados mas não mapeados corretamente

**Verificar:**
1. Abrir: `http://umc.localhost:5000/sensors`
2. DevTools → Console
3. Ver log: `🔍 Processando sensor X/Y`
4. Verificar se `sensorId` não é `undefined`

---

## 📊 Estrutura Esperada do Payload

O EMQX deve enviar:

```json
{
  "client_id": "test_publisher_1729391233",
  "username": "traksense",
  "topic": "traksense/GW-1760908415/telemetry",
  "qos": 1,
  "payload": {
    "device_id": "GW-1760908415",
    "timestamp": "2025-10-20T03:27:33.474563Z",
    "sensors": [
      {
        "sensor_id": "TEMP-AMB-001",
        "type": "temperature",
        "value": 23.5,
        "unit": "°C",
        "labels": {
          "location": "Sala de Máquinas",
          "type": "temperature",
          "description": "Temperatura Ambiente"
        }
      }
    ]
  },
  "ts": 1729391253474
}
```

O backend vai extrair `payload` e processar os sensores.

---

## 🎯 Validação Final

### Checklist:

- [ ] Dashboard EMQX acessível (http://localhost:18083)
- [ ] Conector HTTP criado e Status = `Connected` (verde)
- [ ] Regra criada e Status = `Enabled` (verde)
- [ ] Script Python executado sem erros
- [ ] EMQX Rule mostra `Matched > 0`
- [ ] Backend logs mostram `✅ Telemetry received`
- [ ] Banco de dados tem novos registros
- [ ] UI mostra sensores: TEMP-AMB-001, HUM-001, etc.

---

## 📝 Alternativa: Chamada Direta HTTP

Se o webhook continuar com problemas, você pode testar chamando o endpoint diretamente:

```powershell
$payload = @{
  client_id = "test-direct"
  topic = "traksense/GW-1760908415/telemetry"
  payload = @{
    device_id = "GW-1760908415"
    timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ss.fffZ")
    sensors = @(
      @{
        sensor_id = "TEMP-AMB-001"
        type = "temperature"
        value = 23.5
        unit = "°C"
        labels = @{
          type = "temperature"
          description = "Temperatura Ambiente"
        }
      }
    )
  }
  ts = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
} | ConvertTo-Json -Depth 10

$headers = @{
  "Content-Type" = "application/json"
  "X-Tenant" = "umc"
}

Invoke-RestMethod -Uri "http://localhost:8000/ingest" -Method POST -Body $payload -Headers $headers
```

---

**Criado:** 20/10/2025 00:30  
**Status:** 📘 Guia de Configuração  
**Próximo Passo:** Configurar webhook no Dashboard EMQX
