# 🔍 Validação Manual - EMQX Rule Engine

## 📋 Status Atual

### ✅ Componentes Funcionando
- **Endpoint `/ingest`**: Aceita requisições HTTP POST (Status 202)
- **TimescaleDB Hypertable**: Salvando dados corretamente
- **Multi-tenant Routing**: PUBLIC_SCHEMA_URLCONF funcionando
- **Tenant Schema Switching**: View consegue alternar esquemas

### ❌ Problema Identificado
**MQTT → Django**: Mensagens publicadas via MQTT não chegam no endpoint `/ingest`

### 📊 Evidências
```bash
# Teste HTTP Direto: ✅ FUNCIONA
$ docker exec traksense-api python -c "import requests; ..."
Status: 202 Accepted
DB: 5 registros salvos

# Teste MQTT: ❌ NÃO FUNCIONA
$ docker run --rm --network docker_traksense eclipse-mosquitto mosquitto_pub \
  -h traksense-emqx -p 1883 \
  -t "tenants/umc/devices/device-001/sensors/temperature" \
  -m '{"value": 26.5, "unit": "celsius"}'
✅ Mensagem publicada no broker
❌ Nenhum registro novo no banco
❌ Nenhum log no container API
```

---

## 🔧 Checklist de Validação

### 1. Acessar EMQX Dashboard

```
URL: http://localhost:18083
Usuário: admin
Senha: Tr@kS3ns3!
```

### 2. Verificar Connector HTTP

**Navegação**: Integration → Connectors

**Procurar por**: `http_ingest_umc` ou tipo **HTTP Server**

**Checklist**:
- [ ] Status: **Connected** (bolinha verde)
- [ ] Base URL: `http://api:8000`
- [ ] Connection Test: Deve passar

**Se Status = Disconnected**:
1. Click no connector para abrir detalhes
2. Click em "Test Connection" ou "Reconnect"
3. Verificar logs do EMQX: `docker logs traksense-emqx --tail 50`
4. Verificar se container `traksense-api` está rodando: `docker ps`

**Se connector não existir**:
- Precisa ser criado via script `provision-emqx.sh` ou manualmente no Dashboard

---

### 3. Verificar Rule com HTTP Sink

**Navegação**: Integration → Rules

**Procurar por**: `r_umc_ingest` ou criar nova

**Checklist**:
- [ ] Status: **Enabled** (toggle verde)
- [ ] SQL configurado:
  ```sql
  SELECT
    clientid as client_id,
    topic,
    payload,
    timestamp as ts
  FROM
    "tenants/umc/#"
  ```
- [ ] **Actions** (seção inferior da Rule):
  - [ ] Tem uma action do tipo **HTTP Server** ou **Webhook**
  - [ ] Connector: `http_ingest_umc`
  - [ ] Path: `/ingest`
  - [ ] Method: **POST**
  - [ ] **CRITICAL**: Header `x-tenant: uberlandia-medical-center` (NÃO `umc`)
  - [ ] Body: `${.}` (envia payload completo da SQL)

**🚨 PROBLEMA CONHECIDO**: 
Header `x-tenant` pode estar configurado com `umc`, mas o slug correto do tenant é `uberlandia-medical-center`

**Correção**:
1. Click na Rule `r_umc_ingest`
2. Na seção **Actions**, click no ícone de **Edit** (lápis) da action HTTP
3. Scroll até **Headers**
4. Alterar:
   ```
   ❌ x-tenant: umc
   ✅ x-tenant: uberlandia-medical-center
   ```
5. Click em **Update** ou **Save**
6. Verificar se Rule continua **Enabled**

**Métricas da Rule** (após correção e teste):
- **Matched**: > 0 (rule capturou mensagens do tópico)
- **Passed/Success**: > 0 (rule executou ação com sucesso)
- **Failed**: = 0 (nenhum erro na execução)

**Se Status = Disabled**:
1. Click no toggle para **Enable**
2. Aguardar 2 segundos
3. Publicar mensagem de teste

---

---

## 💡 Entendendo a Arquitetura EMQX v6

No EMQX v6.0, a integração HTTP funciona assim:

```
MQTT Publish → Rule Engine → HTTP Sink (via Connector) → Django API
```

**Componentes**:

1. **Connector** (Integration → Connectors)
   - Define a conexão HTTP base: `http://api:8000`
   - Gerencia connection pool, retries, timeouts
   - Status: Connected/Disconnected

2. **Rule** (Integration → Rules)
   - Processa mensagens MQTT via SQL
   - Define tópicos a monitorar: `FROM "tenants/umc/#"`
   - Extrai/transforma dados: `SELECT clientid as client_id, topic, payload, timestamp as ts`

3. **Action** (dentro da Rule)
   - Tipo: **HTTP Server Sink**
   - Usa o Connector configurado
   - Define:
     - Path: `/ingest`
     - Method: POST
     - Headers: `x-tenant: uberlandia-medical-center`
     - Body: `${.}` (payload da SQL)

**Não existe mais "Actions" como menu separado** - Actions são configuradas dentro de cada Rule.

**Webhook** é uma feature simplificada separada para eventos/mensagens sem precisar criar Rules manualmente.

---

### 5. Teste End-to-End via MQTT

#### Passo 1: Limpar logs da API
```powershell
# Parar monitoramento de logs (se estiver rodando)
docker logs traksense-api --tail 0 --follow
```

#### Passo 2: Publicar mensagem MQTT
```powershell
docker run --rm --network docker_traksense eclipse-mosquitto mosquitto_pub `
  -h traksense-emqx `
  -p 1883 `
  -t "tenants/umc/devices/device-test-001/sensors/temperature" `
  -m '{"value": 99.9, "unit": "celsius"}'
```

#### Passo 3: Verificar logs da API (nova janela)
```powershell
docker logs traksense-api --tail 20 | Select-String -Pattern "ingest|Telemetry saved"
```

**Resultado Esperado**:
```
INFO views Telemetry saved: tenant=uberlandia-medical-center, device=device-test-001, topic=tenants/umc/devices/device-test-001/sensors/temperature
```

#### Passo 4: Verificar banco de dados
```powershell
docker exec traksense-postgres psql -U app -d app -c "
  SET search_path TO uberlandia_medical_center;
  SELECT id, device_id, payload->>'value' as temp, created_at
  FROM telemetry
  ORDER BY created_at DESC
  LIMIT 1;
"
```

**Resultado Esperado**:
```
 id |    device_id     | temp |          created_at
----+------------------+------+------------------------------
  6 | device-test-001  | 99.9 | 2025-10-17 23:00:00.123456+00
```

#### Passo 5: Verificar métricas no EMQX Dashboard

**Navegação**: Integration → Rules → `r_umc_ingest`

**Scroll até seção "Metrics" ou "Statistics"**:

```
Matched:  1+  ← Rule capturou a mensagem
Success:  1+  ← Action HTTP executou com sucesso  
Failed:   0   ← Nenhum erro
```

**Se Failed > 0**:
1. Click na Rule para abrir detalhes
2. Scroll até a seção **Actions**
3. Verificar métricas específicas da Action HTTP
4. Click em **View Logs** ou **Error Details** se disponível
5. Possíveis causas:
   - Header `x-tenant` incorreto → retorna 404 "Tenant not found"
   - Formato de payload incorreto → retorna 400 "Bad Request"
   - Connector offline → retorna erro de conexão
   - Path incorreto → retorna 404

**Métricas da Action** (dentro da Rule):
- **Success**: Requisições HTTP com status 2xx
- **Failed**: Requisições com erro de rede ou status >= 400
- **Inflight**: Requisições em andamento
- **Queuing**: Mensagens aguardando envio (se buffer habilitado)

---

## 🐛 Troubleshooting

### Problema: Matched = 0
**Causa**: Rule não está capturando mensagens do tópico

**Solução**:
1. Verificar se Rule está **Enabled**
2. Verificar pattern do tópico: `tenants/umc/#`
3. Publicar em tópico que corresponda: `tenants/umc/devices/*/sensors/*`

---

### Problema: Matched > 0, Success = 0, Failed > 0
**Causa**: Rule capturou mas HTTP Sink falhou

**Checklist**:
1. **Connector Status**: Navegue para Integration → Connectors → `http_ingest_umc`
   - Se Disconnected → verificar rede Docker: `docker network inspect docker_traksense`
   - Verificar se API responde: `docker exec traksense-api curl -v http://api:8000/health`
   - Click em "Test Connection" no Connector

2. **Header x-tenant** (na Action da Rule): Deve ser `uberlandia-medical-center`
   - Logs da API mostrarão: `WARNING: Tenant 'umc' not found` se estiver errado
   - Verificar: Integration → Rules → `r_umc_ingest` → seção **Actions** → Edit → Headers

3. **Path correto** (na Action da Rule): Deve ser `/ingest`
   - Verificar na mesma seção de Headers
   - Connector tem base URL `http://api:8000`, Action adiciona path `/ingest`
   - URL final: `http://api:8000/ingest`

4. **Formato do Payload**: SQL deve retornar `client_id`, `topic`, `payload`, `ts`
   - Body template deve ser `${.}` (envia JSON completo)
   - Verificar SQL da Rule

---

### Problema: Passed > 0 mas nenhum registro no banco
**Causa**: API retornou 2xx mas não salvou (improvável, mas possível)

**Debug**:
```powershell
# Ver logs completos da API
docker logs traksense-api --tail 100 | Select-String -Pattern "ERROR|WARNING|Telemetry"

# Verificar se há erros de conexão com o banco
docker logs traksense-api --tail 100 | Select-String -Pattern "database|connection"

# Verificar response da API nos logs do EMQX
docker logs traksense-emqx --tail 50 | Select-String -Pattern "ingest|202|404|500"
```

**Verificar status code retornado**:
- Status 202 Accepted: API recebeu e processou
- Status 404: Tenant não encontrado ou path errado
- Status 400: Payload malformado
- Status 500: Erro interno do Django

---

### Problema: "No configuration file provided" ao executar docker compose
**Causa**: Comando não está sendo executado na pasta correta

**Solução**:
```powershell
# Sempre executar comandos na raiz do projeto
cd "c:\Users\Rafael Ribeiro\TrakSense\traksense-backend"

# Usar comandos sem o parâmetro -f
docker compose exec api <comando>
docker compose logs emqx
```

---

## ✅ Validação Completa

Quando tudo estiver funcionando:

```powershell
# Publicar 3 mensagens de teste
for ($i=1; $i -le 3; $i++) {
    docker run --rm --network docker_traksense eclipse-mosquitto mosquitto_pub `
      -h traksense-emqx `
      -p 1883 `
      -t "tenants/umc/devices/device-$i/sensors/temperature" `
      -m "{\"value\": $($20 + $i), \"unit\": \"celsius\"}"
    Start-Sleep -Seconds 1
}

# Verificar resultados
docker exec traksense-postgres psql -U app -d app -c "
  SET search_path TO uberlandia_medical_center;
  SELECT COUNT(*) as total, MAX(created_at) as ultima
  FROM telemetry;
"
```

**Resultado Esperado**: `total` deve aumentar em 3

---

## 📝 Próximos Passos

Após validação completa:

1. **Documentar configuração correta** em `EMQX_PROVISIONING.md`
2. **Atualizar script `provision-emqx.sh`** para usar `uberlandia-medical-center`
3. **Criar monitoring/alertas** para Rule Engine
4. **Implementar autenticação MQTT** (credenciais por dispositivo)
5. **Implementar rate limiting** no endpoint `/ingest`

---

## 📊 Logs e Comandos Úteis

### Monitorar logs em tempo real
```powershell
# EMQX
docker logs traksense-emqx --follow

# API Django
docker logs traksense-api --follow | Select-String -Pattern "ingest"

# PostgreSQL (queries lentas)
docker exec traksense-postgres psql -U app -d app -c "
  SELECT query, state, wait_event, query_start
  FROM pg_stat_activity
  WHERE datname = 'app' AND state != 'idle';
"
```

### Resetar dados de teste
```powershell
docker exec traksense-postgres psql -U app -d app -c "
  SET search_path TO uberlandia_medical_center;
  TRUNCATE TABLE telemetry;
"
```

### Verificar conectividade API ↔ EMQX
```powershell
# Da API para EMQX
docker exec traksense-api curl -v http://emqx:18083

# Do EMQX para API
docker exec traksense-emqx curl -v http://api:8000/health
```

---

**Data**: 2025-10-17  
**Status**: 🟡 Endpoint funcionando, integração MQTT pendente  
**Próxima Ação**: Verificar EMQX Dashboard e corrigir header `x-tenant`
