# 📡 Provisionamento EMQX - Guia Completo

> **Fase 0** - Configuração automatizada do EMQX Rule Engine para ingestão de telemetria MQTT

## 📋 Índice

- [Visão Geral](#visão-geral)
- [Pré-requisitos](#pré-requisitos)
- [Componentes Criados](#componentes-criados)
- [Como Executar](#como-executar)
- [Variáveis de Ambiente](#variáveis-de-ambiente)
- [Validação](#validação)
- [Troubleshooting](#troubleshooting)
- [Segurança em Produção](#segurança-em-produção)
- [Referências](#referências)

---

## 🎯 Visão Geral

O script `provision-emqx.sh` automatiza a configuração do EMQX v5+ para:

1. **Connector HTTP**: Canal de comunicação com o backend Django
2. **Action HTTP**: Ação que executa POST para `/ingest`
3. **Rule SQL**: Regra que captura mensagens de `tenants/{slug}/#` e dispara a action
4. **Authorization Rules** *(dev)*: Permite apenas tópicos do tenant configurado

### Fluxo de Dados

```
📱 IoT Device
    ↓ PUBLISH MQTT
🔄 EMQX Broker (porta 1883)
    ↓ Rule Engine Match: tenants/umc/#
📊 SQL Processor (extrai: client_id, topic, payload, timestamp)
    ↓ Trigger Action
🌐 HTTP Action (POST)
    ↓ Headers: x-tenant: umc
🎯 Django API: http://api:8000/ingest
```

---

## ✅ Pré-requisitos

### Software Necessário

- **curl**: Cliente HTTP para API calls
- **jq**: Processador JSON CLI
- **bash**: Shell Unix (no Windows use Git Bash ou WSL)

**Instalação:**

```bash
# Ubuntu/Debian
sudo apt install curl jq

# macOS
brew install curl jq

# Windows (via Chocolatey)
choco install curl jq

# Windows (via Git Bash)
# curl e jq já incluídos no Git for Windows
```

### Serviços Rodando

```bash
# Verificar status dos containers
docker compose -f docker/docker-compose.yml ps

# Devem estar "healthy" ou "running":
# - traksense-postgres
# - traksense-redis
# - traksense-emqx
# - traksense-api
```

---

## 🏗️ Componentes Criados

### 1. HTTP Connector

**Nome**: `http_ingest_umc` (por tenant)

**Configuração**:
```json
{
  "type": "http",
  "name": "http_ingest_umc",
  "description": "HTTP connector para backend ingest (dev)",
  "config": {
    "base_url": "http://api:8000",
    "pool_size": 16,
    "connect_timeout": "5s",
    "request_timeout": "10s",
    "enable_pipelining": false
  }
}
```

### 2. HTTP Action

**Nome**: `http_ingest_umc`

**Configuração**:
```json
{
  "type": "http",
  "name": "http_ingest_umc",
  "connector": "http:http_ingest_umc",
  "parameters": {
    "method": "POST",
    "path": "/ingest",
    "headers": {
      "content-type": "application/json",
      "x-tenant": "umc"
    },
    "body": "${payload}",
    "max_retries": 5,
    "retry_interval": "5s",
    "timeout": "10s"
  }
}
```

**Explicação dos campos**:
- `${payload}`: Template variable do EMQX que encaminha o payload MQTT original
- `x-tenant`: Header customizado para identificar o tenant no backend
- `max_retries: 5`: Tenta até 5 vezes em caso de falha
- `retry_interval: 5s`: Aguarda 5s entre tentativas

### 3. Rule SQL

**ID**: `r_umc_ingest`

**SQL**:
```sql
SELECT
  clientid as client_id,
  topic,
  payload,
  timestamp as ts
FROM "tenants/umc/#"
```

**Ação**: Dispara `http:http_ingest_umc`

**Explicação**:
- `clientid`: ID do dispositivo MQTT conectado
- `topic`: Tópico completo da mensagem (ex: `tenants/umc/devices/001/sensors/temp`)
- `payload`: Conteúdo da mensagem (encaminhado como `${payload}` na action)
- `timestamp`: Timestamp Unix em milissegundos do broker
- `FROM "tenants/umc/#"`: Wildcards MQTT (`#` = múltiplos níveis)

### 4. Authorization Rules *(opcional, dev)*

**Backend**: `built_in_database`

**Regras**:
1. **Deny** `$queue/#` (tópicos internos)
2. **Allow** `tenants/umc/#` (apenas tópicos do tenant)
3. **Deny** `#` (todo o resto)

---

## 🚀 Como Executar

### Opção 1: Após `docker compose up -d`

```bash
# 1. Subir a stack
docker compose -f docker/docker-compose.yml up -d

# 2. Aguardar EMQX inicializar (healthcheck)
sleep 10

# 3. Executar provisionamento
bash docker/scripts/provision-emqx.sh
```

### Opção 2: Com variáveis customizadas

```bash
# Provisionar para outro tenant
TENANT_SLUG=acme \
EMQX_API_KEY=my-key \
EMQX_API_SECRET=my-secret \
bash docker/scripts/provision-emqx.sh
```

### Opção 3: De dentro da rede Docker

```bash
# Se rodar de um container na mesma rede
docker compose exec api bash -c "
  export EMQX_BASE_URL=http://emqx:18083
  export INGEST_BASE_URL=http://api:8000
  bash /app/docker/scripts/provision-emqx.sh
"
```

---

## 🔧 Variáveis de Ambiente

| Variável               | Default                  | Descrição                                  |
|------------------------|--------------------------|--------------------------------------------|
| `TENANT_SLUG`          | `umc`                    | Slug do tenant (usado em tópicos e nomes)  |
| `EMQX_BASE_URL`        | `http://localhost:18083` | URL da API REST do EMQX                    |
| `EMQX_API_KEY`         | *(vazio)*                | API Key (Basic Auth) - **preferência 1**   |
| `EMQX_API_SECRET`      | *(vazio)*                | API Secret                                 |
| `EMQX_DASHBOARD_USER`  | `admin`                  | User do dashboard (fallback Bearer)        |
| `EMQX_DASHBOARD_PASS`  | `public`                 | Password do dashboard (fallback Bearer)    |
| `INGEST_BASE_URL`      | `http://api:8000`        | Base URL do backend Django                 |
| `INGEST_PATH`          | `/ingest`                | Path do endpoint de ingestão               |

### Ordem de Autenticação

1. **Se definidos** `EMQX_API_KEY` e `EMQX_API_SECRET` → usa **Basic Auth** (recomendado)
2. **Senão** → tenta `POST /api/v5/login` com `EMQX_DASHBOARD_USER/PASS` → **Bearer Token** (dev)

---

## ✅ Validação

### 1. Verificar Recursos Criados

```bash
# Via API (com API Key)
curl -u "dev-provisioner:change-me" http://localhost:18083/api/v5/connectors/http:http_ingest_umc | jq

# Via API (com Bearer)
TOKEN=$(curl -sS -X POST http://localhost:18083/api/v5/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"public"}' | jq -r .token)

curl -H "Authorization: Bearer $TOKEN" http://localhost:18083/api/v5/rules/r_umc_ingest | jq
```

### 2. Verificar no Dashboard

1. Acesse http://localhost:18083
2. Login: `admin` / `public`
3. Navegue até **Integration → Connectors**
   - Você deve ver `http_ingest_umc` com status **Connected** ✅
4. Navegue até **Integration → Rules**
   - Você deve ver `r_umc_ingest` com status **Enabled** ✅
   - Clique para ver detalhes do SQL e action

### 3. Testar Ingestão End-to-End

```bash
# Publicar mensagem MQTT
mosquitto_pub -h localhost -p 1883 \
  -t "tenants/umc/devices/test-device/sensors/temperature" \
  -m '{"value": 22.5, "unit": "celsius"}'

# Verificar logs do backend Django
docker compose -f docker/docker-compose.yml logs api --tail=20

# Deve aparecer:
# POST /ingest com body contendo o payload
```

### 4. Verificar Métricas da Rule

No Dashboard EMQX:
- **Integration → Rules → r_umc_ingest**
- Veja a aba **Metrics**:
  - `Matched`: Número de mensagens capturadas pela rule
  - `Passed`: Mensagens processadas com sucesso
  - `Failed`: Falhas (ex: backend offline)

---

## 🐛 Troubleshooting

### Erro: "Não consegui falar com http://localhost:18083"

**Causa**: EMQX não está no ar ou ainda inicializando.

**Solução**:
```bash
# Verificar status
docker compose -f docker/docker-compose.yml ps emqx

# Verificar logs
docker compose -f docker/docker-compose.yml logs emqx --tail=50

# Aguardar healthcheck
until docker compose -f docker/docker-compose.yml ps emqx | grep -q "healthy"; do
  echo "Aguardando EMQX..."
  sleep 2
done

# Tentar novamente
bash docker/scripts/provision-emqx.sh
```

---

### Erro: "Falha no login do dashboard"

**Causa**: Credenciais incorretas ou API Key bootstrap não configurada.

**Solução 1 - Usar API Key**:
```bash
# Adicionar ao .env
EMQX_API_KEY=dev-provisioner
EMQX_API_SECRET=change-me

# Rodar novamente
source .env
bash docker/scripts/provision-emqx.sh
```

**Solução 2 - Verificar senha do dashboard**:
```bash
# Consultar logs do EMQX para ver credenciais padrão
docker compose -f docker/docker-compose.yml logs emqx | grep -i password
```

---

### Erro: "Resource already exists" (409 Conflict)

**Causa**: Componente já foi criado anteriormente.

**Comportamento esperado**: O script é **idempotente** e detecta recursos existentes automaticamente.

**Output esperado**:
```
>> Criando/validando Connector HTTP: http_ingest_umc
   - Já existe.
>> Criando/validando Action HTTP: http_ingest_umc
   - Já existe.
>> Criando/validando Regra: r_umc_ingest
   - Já existe.
✅ Provisioning EMQX concluído
```

---

### Erro: Action mostra "Disconnected" no Dashboard

**Causa**: Backend Django não está acessível na URL configurada.

**Diagnóstico**:
```bash
# De dentro do container EMQX, testar conectividade
docker compose exec emqx curl -v http://api:8000/health

# Se falhar, verificar:
# 1. Container 'api' está rodando?
docker compose ps api

# 2. Rede Docker está correta?
docker compose exec emqx ping -c 3 api
```

**Solução**:
- Verificar `INGEST_BASE_URL` está correto (`http://api:8000` para compose)
- Certificar que `api` está na mesma rede Docker (`traksense`)

---

### Erro: Mensagens não chegam ao backend

**Diagnóstico passo a passo**:

```bash
# 1. Verificar se rule está habilitada
curl -u "dev-provisioner:change-me" http://localhost:18083/api/v5/rules/r_umc_ingest | jq '.enable'
# Deve retornar: true

# 2. Publicar mensagem de teste
mosquitto_pub -h localhost -p 1883 \
  -t "tenants/umc/test" \
  -m '{"test": true}'

# 3. Verificar métricas da rule no Dashboard
# Integration → Rules → r_umc_ingest → Metrics
# Se "Matched" aumentou mas "Passed" não → problema na action

# 4. Verificar métricas da action
# Integration → Actions → http_ingest_umc → Metrics
# Se "Failed" > 0 → clicar para ver detalhes do erro

# 5. Verificar logs do backend
docker compose logs api --tail=30 | grep -i ingest
```

---

## 🔒 Segurança em Produção

### 1. API Key Bootstrap Segura

**Gerar API Key forte**:
```bash
# Gerar chave de 32 bytes em base64
openssl rand -base64 32
# Exemplo output: X8kP3mN9vL2qR5tY7wA1sD4fG6hJ8kL0

# Criar arquivo (NÃO versionar)
echo "prod-provisioner:X8kP3mN9vL2qR5tY7wA1sD4fG6hJ8kL0:administrator" > docker/emqx/prod_api_key.conf
chmod 600 docker/emqx/prod_api_key.conf
```

**Configurar no docker-compose.yml** (produção):
```yaml
emqx:
  volumes:
    - ./emqx/prod_api_key.conf:/opt/emqx/etc/default_api_key.conf:ro
  environment:
    EMQX_API_KEY__BOOTSTRAP__FILE: /opt/emqx/etc/default_api_key.conf
```

**Adicionar ao .gitignore**:
```gitignore
docker/emqx/prod_api_key.conf
docker/emqx/*_api_key.conf
!docker/emqx/default_api_key.conf  # exemplo dev versionado
```

---

### 2. Desabilitar Anonymous e Erlang Cookie

```yaml
emqx:
  environment:
    EMQX_ALLOW_ANONYMOUS: "false"
    EMQX_NODE__COOKIE: "${EMQX_ERLANG_COOKIE}"  # via secrets
```

```bash
# Gerar cookie Erlang
openssl rand -base64 32 > .secrets/emqx_cookie
chmod 600 .secrets/emqx_cookie

# Adicionar ao .env (ou secrets manager)
EMQX_ERLANG_COOKIE=$(cat .secrets/emqx_cookie)
```

---

### 3. Authentication por JWT/HTTP

**Opção A - JWT (tokens assinados pelo backend)**:
```yaml
emqx:
  environment:
    EMQX_AUTH__JWT__SECRET: "${DJANGO_SECRET_KEY}"
    EMQX_AUTH__JWT__FROM: "username"
    EMQX_AUTH__JWT__VERIFY_CLAIMS__USERNAME: "%u"
```

**Opção B - HTTP Callback (validação no Django)**:
```yaml
emqx:
  environment:
    EMQX_AUTH__HTTP__AUTH_REQ__URL: "http://api:8000/mqtt/auth"
    EMQX_AUTH__HTTP__AUTH_REQ__METHOD: "POST"
    EMQX_AUTH__HTTP__AUTH_REQ__HEADERS: "Content-Type: application/json"
```

**Implementar no Django** (Fase futura):
```python
# apps/mqtt/views.py
@api_view(['POST'])
def mqtt_auth(request):
    clientid = request.data.get('clientid')
    username = request.data.get('username')
    password = request.data.get('password')
    
    # Validar credenciais do device
    if Device.objects.filter(mqtt_clientid=clientid, mqtt_token=password).exists():
        return Response({"result": "allow"}, status=200)
    return Response({"result": "deny"}, status=403)
```

---

### 4. TLS/SSL para MQTT

```yaml
emqx:
  volumes:
    - ./certs:/opt/emqx/etc/certs:ro
  environment:
    EMQX_LISTENER__SSL__EXTERNAL: "8883"
    EMQX_LISTENER__SSL__EXTERNAL__KEYFILE: "/opt/emqx/etc/certs/key.pem"
    EMQX_LISTENER__SSL__EXTERNAL__CERTFILE: "/opt/emqx/etc/certs/cert.pem"
    EMQX_LISTENER__SSL__EXTERNAL__CACERTFILE: "/opt/emqx/etc/certs/ca.pem"
```

**Gerar certificados (auto-assinado para staging)**:
```bash
mkdir -p docker/certs
cd docker/certs

# CA
openssl req -new -x509 -days 365 -keyout ca-key.pem -out ca.pem -subj "/CN=EMQX-CA"

# Server
openssl genrsa -out key.pem 2048
openssl req -new -key key.pem -out server.csr -subj "/CN=emqx.traksense.com"
openssl x509 -req -in server.csr -CA ca.pem -CAkey ca-key.pem -CAcreateserial -out cert.pem -days 365

chmod 600 *.pem
```

---

### 5. Rate Limiting & Quotas

```yaml
emqx:
  environment:
    EMQX_ZONE__EXTERNAL__RATE_LIMIT__CONN_MESSAGES: "1000/s"
    EMQX_ZONE__EXTERNAL__RATE_LIMIT__CONN_BYTES: "1MB/s"
    EMQX_ZONE__EXTERNAL__MAX_CLIENTID_LEN: 128
    EMQX_ZONE__EXTERNAL__MAX_PACKET_SIZE: "1MB"
```

---

### 6. Authorization por Device/Tenant

**Implementar no HTTP Callback**:
```python
# apps/mqtt/views.py
@api_view(['POST'])
def mqtt_acl(request):
    clientid = request.data.get('clientid')
    topic = request.data.get('topic')
    action = request.data.get('action')  # 'publish' ou 'subscribe'
    
    device = Device.objects.filter(mqtt_clientid=clientid).first()
    if not device:
        return Response({"result": "deny"}, status=403)
    
    # Validar se device pode publicar no tópico do seu tenant
    tenant_slug = device.tenant.slug
    if not topic.startswith(f"tenants/{tenant_slug}/devices/{device.slug}/"):
        return Response({"result": "deny"}, status=403)
    
    return Response({"result": "allow"}, status=200)
```

**Configurar no EMQX**:
```yaml
emqx:
  environment:
    EMQX_AUTH__HTTP__ACL_REQ__URL: "http://api:8000/mqtt/acl"
    EMQX_AUTH__HTTP__ACL_REQ__METHOD: "POST"
```

---

## 📚 Referências

### Documentação Oficial EMQX

- [**API REST v5**](https://docs.emqx.com/en/emqx/latest/admin/api.html): Autenticação e endpoints
- [**API Keys & Bootstrap**](https://docs.emqx.com/en/emqx/latest/dashboard/system.html#api-keys): Configuração de API Keys por arquivo
- [**Rule Engine**](https://docs.emqx.com/en/emqx/latest/data-integration/rules.html): Conceitos de Rules, SQL, Actions
- [**HTTP Server Action**](https://docs.emqx.com/en/emqx/latest/data-integration/data-bridge-webhook.html): Connector e Action HTTP
- [**Authorization**](https://docs.emqx.com/en/emqx/latest/access-control/authn/authn.html): AuthN e AuthZ por built_in_database, JWT, HTTP

### Recursos da Comunidade

- [EMQX GitHub](https://github.com/emqx/emqx): Issues e exemplos
- [EMQX Forum](https://forum.emqx.io/): Dúvidas e discussões
- [Awesome EMQX](https://github.com/emqx/awesome-emqx): Ferramentas e integrações

---

## 📝 Checklist de Implantação

### Desenvolvimento

- [x] EMQX rodando com API Key bootstrap
- [x] Script de provisionamento idempotente
- [x] Rule capturando `tenants/umc/#`
- [x] Action HTTP enviando para `/ingest`
- [x] Authorization rules básicas (allow tenant)
- [ ] Endpoint `/ingest` implementado no Django (Fase 1)
- [ ] Teste end-to-end com device real/simulado

### Staging

- [ ] API Key forte (32+ bytes)
- [ ] Erlang cookie único
- [ ] `ALLOW_ANONYMOUS=false`
- [ ] TLS/SSL habilitado (porta 8883)
- [ ] Authentication por JWT ou HTTP
- [ ] Authorization por device (HTTP callback)
- [ ] Rate limiting configurado
- [ ] Logs centralizados (Grafana Loki / ELK)

### Produção

- [ ] Certificados TLS válidos (Let's Encrypt / AWS ACM)
- [ ] API Keys via secrets manager (AWS Secrets / Vault)
- [ ] Cluster EMQX (3+ nodes)
- [ ] Persistent volumes (data + log)
- [ ] Backup de configuração (GitOps)
- [ ] Monitoring (Prometheus + Grafana)
- [ ] Alertas (PagerDuty / Opsgenie)
- [ ] Testes de carga (locust / k6)
- [ ] Documentação de runbook (on-call)

---

## 🎯 Próximos Passos

1. **Implementar endpoint `/ingest`** (Fase 1)
   - Validar `x-tenant` header
   - Parsear payload JSON
   - Salvar em TimescaleDB
   - Retornar 202 Accepted

2. **Device Management** (Fase futura)
   - Cadastro de dispositivos no Django
   - Geração de `mqtt_clientid` e `mqtt_token`
   - UI para credenciais MQTT

3. **Authentication/Authorization EMQX** (Fase 2)
   - HTTP callback para AuthN: `POST /mqtt/auth`
   - HTTP callback para AuthZ: `POST /mqtt/acl`
   - Validação por tenant/device

4. **Monitoring & Observability** (Fase 3)
   - Métricas do EMQX no Prometheus
   - Dashboard Grafana para MQTT
   - Alertas de latência/falhas

---

**Última atualização**: 17 de outubro de 2025  
**Versão**: 1.0.0 (Fase 0)  
**Autor**: TrakSense Development Team
