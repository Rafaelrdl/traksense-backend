# 🎯 Guia Passo a Passo - Criar Rule EMQX Manualmente

> Como o script provision-emqx.sh não criou os recursos, vamos fazer manualmente pelo Dashboard

**URL**: http://localhost:18083  
**Login**: admin / Tr@kS3ns3!

---

## Passo 1: Criar Connector HTTP 🔌

### 1.1. Acessar Connectors
1. Menu lateral esquerdo: **Integration**
2. Submenu: **Connectors**
3. Botão superior direito: **+ Create**

### 1.2. Selecionar Tipo
- Busque por: **HTTP Server**
- Click em **HTTP Server**

### 1.3. Configurar Connector

**Nome**: `http_ingest_umc`

**Connection Settings**:
```
Base URL: http://api:8000
```

**Advanced Settings** (pode deixar padrão ou ajustar):
```
Connect Timeout: 15s
Max Retries: 2
Pool Size: 8
```

**Headers** (opcional, pode deixar vazio aqui):
```
(vazio - vamos configurar na Action)
```

### 1.4. Testar Conexão
1. Scroll para baixo
2. Click em **Test Connection** ou **Test Connectivity**
3. Aguardar resultado: **Connected** ✅

### 1.5. Salvar
- Click em **Create** ou **Save**
- Verificar na lista: Status = **Connected** (bolinha verde)

✅ **Connector criado com sucesso!**

---

## Passo 2: Criar Rule com Action HTTP 📋

### 2.1. Acessar Rules
1. Menu lateral esquerdo: **Integration**
2. Submenu: **Rules**
3. Botão superior direito: **+ Create**

### 2.2. Configurar Rule

**ID/Name**: `r_umc_ingest`

**Notes/Description** (opcional):
```
Ingest telemetry from MQTT to Django API
```

**SQL**:
```sql
SELECT
  clientid as client_id,
  topic,
  payload,
  timestamp as ts
FROM
  "tenants/umc/#"
```

**Explicação do SQL**:
- `FROM "tenants/umc/#"`: Escuta todos os tópicos que começam com `tenants/umc/`
- `SELECT clientid as client_id`: Renomeia `clientid` para `client_id`
- `payload`: Payload da mensagem MQTT (já vem como JSON)
- `timestamp as ts`: Timestamp em milissegundos

### 2.3. Adicionar Action HTTP

**Scroll para baixo** até a seção **Actions**

Click em **+ Add Action** ou **Add**

**Selecionar Tipo**:
- Type: **HTTP Server** (ou **Forwarding with HTTP Server**)
- Click em **Next** ou **Configure**

**Configuração da Action**:

```yaml
# Nome (opcional)
Name: forward_to_django

# Connector
Connector: http_ingest_umc  # (dropdown - selecionar o que criamos)

# Request
Method: POST
Path: /ingest
Body: ${.}  # Envia payload completo da SQL
```

**Headers** (IMPORTANTE):
```
Content-Type: application/json
x-tenant: uberlandia-medical-center
```

**Como adicionar Headers**:
1. Procurar seção "Headers" ou "Request Headers"
2. Click em **+ Add** ou campo de input
3. Adicionar:
   - Key: `Content-Type` → Value: `application/json`
   - Key: `x-tenant` → Value: `uberlandia-medical-center`

**Advanced Settings** (pode deixar padrão):
```
Request Timeout: 30s
Max Retries: 2
```

### 2.4. Salvar Action
- Click em **Confirm** ou **Add**
- Verificar que a action aparece na lista de actions da Rule

### 2.5. Salvar Rule
- Scroll para cima ou baixo até encontrar botão **Create** ou **Save**
- Click para salvar
- Verificar: Status da Rule = **Enabled** (toggle verde)

✅ **Rule criada com sucesso!**

---

## Passo 3: Verificar Configuração ✅

### 3.1. Verificar Connector
```
Integration → Connectors → http_ingest_umc
Status: Connected ✅
```

### 3.2. Verificar Rule
```
Integration → Rules → r_umc_ingest
Status: Enabled ✅
SQL: SELECT clientid as client_id, topic, payload, timestamp as ts FROM "tenants/umc/#"
Actions: 1 action (HTTP Server)
```

### 3.3. Verificar Action (dentro da Rule)
```
Click na Rule r_umc_ingest
Scroll até seção Actions
Verificar:
  ✅ Connector: http_ingest_umc
  ✅ Path: /ingest
  ✅ Method: POST
  ✅ Header x-tenant: uberlandia-medical-center
  ✅ Body: ${.}
```

---

## Passo 4: Testar 🧪

### 4.1. Publicar Mensagem MQTT

**Terminal (PowerShell)**:
```powershell
docker run --rm --network docker_traksense eclipse-mosquitto mosquitto_pub `
  -h traksense-emqx `
  -p 1883 `
  -t "tenants/umc/devices/test-manual-001/sensors/temperature" `
  -m '{"value": 77.7, "unit": "celsius"}'
```

**Aguardar**: 2 segundos

### 4.2. Verificar Métricas no Dashboard

**Navegação**: Integration → Rules → r_umc_ingest

**Scroll** até seção **Metrics** ou **Statistics**

**Verificar**:
```
Matched: 1  ← Rule capturou a mensagem ✅
Success: 1  ← HTTP request retornou 2xx ✅
Failed: 0   ← Sem erros ✅
```

### 4.3. Verificar Logs da API

```powershell
docker logs traksense-api --tail 10 | Select-String "Telemetry saved"
```

**Resultado Esperado**:
```
INFO views Telemetry saved: tenant=uberlandia-medical-center, device=test-manual-001, topic=tenants/umc/devices/test-manual-001/sensors/temperature
```

### 4.4. Verificar Banco de Dados

```powershell
docker exec traksense-postgres psql -U app -d app -c "
  SET search_path TO uberlandia_medical_center;
  SELECT id, device_id, payload, created_at 
  FROM telemetry 
  WHERE device_id = 'test-manual-001';
"
```

**Resultado Esperado**:
```
 id |     device_id      |             payload              |          created_at
----+--------------------+----------------------------------+------------------------------
  6 | test-manual-001    | {"unit": "celsius", "value": 77.7} | 2025-10-17 23:XX:XX+00
```

---

## 🎉 Validação Completa

Se todos os passos acima retornaram ✅:

```
✅ Connector: Connected
✅ Rule: Enabled
✅ Action: Configurada corretamente
✅ Metrics: Matched=1, Success=1, Failed=0
✅ Logs API: "Telemetry saved"
✅ Banco: Registro inserido

🚀 FLUXO MQTT → EMQX → DJANGO → TIMESCALEDB FUNCIONANDO!
```

---

## 🐛 Troubleshooting

### Problema: Test Connection falha no Connector

**Erro**: "Connection refused" ou "Timeout"

**Solução**:
```powershell
# 1. Verificar se API está rodando
docker ps | Select-String "traksense-api"

# 2. Verificar rede Docker
docker network inspect docker_traksense | Select-String "traksense-api|traksense-emqx"

# 3. Testar conectividade do EMQX para API
docker exec traksense-emqx curl -v http://api:8000/health
```

---

### Problema: Matched > 0, Success = 0, Failed > 0

**Causa**: HTTP request falhando

**Debug**:
1. Click na Rule
2. Seção Actions → Click na action
3. Verificar **Error Details** ou **Logs**
4. Possíveis erros:
   - Status 404: Header `x-tenant` incorreto ou path errado
   - Status 400: Body malformado
   - Status 500: Erro no Django

**Verificar logs da API**:
```powershell
docker logs traksense-api --tail 50 | Select-String "ERROR|WARNING"
```

---

### Problema: Matched = 0

**Causa**: Rule não está capturando mensagens

**Solução**:
1. Verificar se Rule está **Enabled**
2. Verificar tópico MQTT publicado:
   - ❌ `devices/001/sensors/temperature` (não corresponde)
   - ✅ `tenants/umc/devices/001/sensors/temperature` (corresponde)
3. Verificar SQL da Rule: `FROM "tenants/umc/#"`

---

## 📸 Checklist Visual

Antes de testar, tire screenshots de:
- [ ] Connector list mostrando `http_ingest_umc` com status Connected
- [ ] Rule list mostrando `r_umc_ingest` com status Enabled
- [ ] Rule detail mostrando SQL completo
- [ ] Action configuration mostrando headers (x-tenant)

Depois do teste:
- [ ] Rule metrics mostrando Matched/Success
- [ ] Logs da API mostrando "Telemetry saved"
- [ ] Query do banco mostrando registro inserido

---

**Data**: 2025-10-17  
**Próximo Passo**: Executar Passo 1 - Criar Connector HTTP
