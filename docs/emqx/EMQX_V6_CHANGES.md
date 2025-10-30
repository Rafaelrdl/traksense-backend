# 🔄 EMQX v5 → v6: Mudanças na Arquitetura

> Guia rápido das mudanças que afetam a implementação do Rule Engine

---

## 📋 Resumo das Mudanças

| Conceito | EMQX v5 | EMQX v6 | Status |
|----------|---------|---------|--------|
| **Data Bridge** | Menu separado | Removido | ❌ Não existe mais |
| **Actions** | Menu separado | Dentro de Rules | 🔄 Mudou localização |
| **Sink** | Termo novo v5.4+ | Termo oficial | ✅ Continua |
| **Connector** | Idem v5 | Idem v6 | ✅ Sem mudanças |
| **Webhook** | Via Rule Engine | Feature separada | 🔄 Simplificado |
| **Flow Designer** | Não existia | Novo recurso | ✨ Novidade v6 |

---

## 🏗️ Arquitetura v5 (antiga)

```
Integration
├── Data Bridges
│   ├── HTTP Server (tipo de bridge)
│   └── MQTT, Kafka, etc.
├── Actions (menu separado)
│   └── http_ingest_umc
├── Rules
│   └── r_umc_ingest (referencia Action)
└── Connectors
    └── http_ingest_umc
```

**Fluxo v5**:
1. Criar **Connector** (conexão HTTP base)
2. Criar **Action** no menu Actions (usa Connector)
3. Criar **Rule** (referencia Action pelo nome)

---

## 🏗️ Arquitetura v6 (nova)

```
Integration
├── Webhooks (simplificado, sem Rules)
│   └── my_webhook
├── Flow Designer (visual, drag-and-drop)
│   └── flow_001
├── Rules
│   └── r_umc_ingest
│       ├── SQL: SELECT ... FROM "tenants/umc/#"
│       └── Actions (definidas dentro da Rule)
│           └── HTTP Server Sink
│               ├── Connector: http_ingest_umc
│               ├── Path: /ingest
│               ├── Headers: x-tenant
│               └── Body: ${.}
└── Connectors
    └── http_ingest_umc
```

**Fluxo v6**:
1. Criar **Connector** (conexão HTTP base)
2. Criar **Rule** com SQL
3. Adicionar **Action** diretamente na Rule (inline)
   - Não existe mais menu separado de "Actions"

---

## 🔍 Onde Encontrar no Dashboard v6

### ❌ NÃO PROCURE POR:
- "Data Bridges" (não existe mais)
- Menu "Actions" separado (actions agora estão dentro de Rules)
- "HTTP Bridge" (agora é "HTTP Server Sink")

### ✅ PROCURE POR:

#### 1. Connectors
**Navegação**: `Integration → Connectors`

**O que é**: Connection pool HTTP/MQTT/Kafka base

**Configuração**:
- Base URL: `http://api:8000` (sem path)
- Connection settings: timeout, pool size, retry
- Health check

**Exemplo**:
```
Nome: http_ingest_umc
Tipo: HTTP Server
URL: http://api:8000
Status: Connected ✅
```

---

#### 2. Rules (com Actions inline)
**Navegação**: `Integration → Rules → r_umc_ingest`

**Estrutura da Rule**:

```yaml
# Seção SQL
FROM: "tenants/umc/#"
SELECT:
  - clientid as client_id
  - topic
  - payload
  - timestamp as ts

# Seção Actions (inline, não mais menu separado)
Actions:
  - Type: HTTP Server
    Connector: http_ingest_umc  # Referência ao connector
    Path: /ingest              # Path adicional à base URL
    Method: POST
    Headers:
      Content-Type: application/json
      x-tenant: uberlandia-medical-center
    Body: ${.}                  # Payload completo da SQL
```

**URL final**: `http://api:8000` (connector) + `/ingest` (action) = `http://api:8000/ingest`

---

#### 3. Webhooks (Feature Simplificada)
**Navegação**: `Integration → Webhooks`

**O que é**: Configuração rápida sem SQL customizado

**Quando usar**:
- Enviar TODOS os eventos/mensagens para HTTP endpoint
- Não precisa filtrar por tópico
- Não precisa transformar payload

**Diferença para Rules**:
- Webhook = Sem SQL, envia tudo automaticamente
- Rule = Com SQL, controle total sobre filtros e transformações

**Exemplo**:
```
Nome: my_webhook
Trigger: All messages and events
URL: http://localhost:5000
Method: POST
```

---

## 🔧 Como Criar HTTP Sink no v6

### Opção 1: Via Dashboard (Recomendado)

1. **Criar Connector**:
   ```
   Integration → Connectors → Create
   - Type: HTTP Server
   - Name: http_ingest_umc
   - Base URL: http://api:8000
   - Click "Create"
   ```

2. **Criar Rule com Action**:
   ```
   Integration → Rules → Create
   
   SQL:
     SELECT
       clientid as client_id,
       topic,
       payload,
       timestamp as ts
     FROM "tenants/umc/#"
   
   Click "Add Action" (botão inferior):
     - Type: HTTP Server
     - Connector: http_ingest_umc (dropdown)
     - Path: /ingest
     - Method: POST
     - Headers:
         Content-Type: application/json
         x-tenant: uberlandia-medical-center
     - Body: ${.}
   
   Click "Create"
   ```

---

### Opção 2: Via API REST

```bash
# 1. Criar Connector
curl -u 'admin:password' -X POST 'http://localhost:18083/api/v5/connectors' \
  -H 'Content-Type: application/json' \
  -d '{
    "type": "http",
    "name": "http_ingest_umc",
    "base_url": "http://api:8000",
    "connect_timeout": "15s"
  }'

# 2. Criar Rule com Action inline
curl -u 'admin:password' -X POST 'http://localhost:18083/api/v5/rules' \
  -H 'Content-Type: application/json' \
  -d '{
    "id": "r_umc_ingest",
    "sql": "SELECT clientid as client_id, topic, payload, timestamp as ts FROM \"tenants/umc/#\"",
    "actions": [
      {
        "function": "http",
        "args": {
          "connector": "http_ingest_umc",
          "path": "/ingest",
          "method": "post",
          "headers": {
            "Content-Type": "application/json",
            "x-tenant": "uberlandia-medical-center"
          },
          "body": "${.}"
        }
      }
    ]
  }'
```

---

### Opção 3: Via Configuração (emqx.conf)

```hocon
# Connector
connectors.http.http_ingest_umc {
  base_url = "http://api:8000"
  connect_timeout = "15s"
  pool_size = 8
}

# Rule com Action
rules.r_umc_ingest {
  sql = """
    SELECT
      clientid as client_id,
      topic,
      payload,
      timestamp as ts
    FROM "tenants/umc/#"
  """
  
  actions = [
    {
      function = http
      args = {
        connector = "http_ingest_umc"
        path = "/ingest"
        method = post
        headers = {
          "Content-Type" = "application/json"
          "x-tenant" = "uberlandia-medical-center"
        }
        body = "${.}"
      }
    }
  ]
}
```

---

## 📊 Comparação de Termos

| Conceito | v5 | v6 | Descrição |
|----------|----|----|-----------|
| **Enviar dados** | Data Bridge (Sink) | Rule + Action (HTTP Server Sink) | Enviar para sistema externo |
| **Receber dados** | Data Bridge (Source) | Source | Receber de sistema externo |
| **Conexão base** | Connector | Connector | Pool de conexões |
| **Ação HTTP** | HTTP Bridge / HTTP Action | HTTP Server Sink | POST/GET para endpoint |
| **Processamento** | Rule Engine | Rule Engine | SQL sobre MQTT |
| **Simples** | - | Webhook | Envio direto sem SQL |
| **Visual** | - | Flow Designer | Drag-and-drop |

---

## 🎯 Checklist de Migração v5 → v6

Se você tem script de provisionamento v5:

- [ ] Remover criação de "Data Bridge"
- [ ] Manter criação de Connector (igual)
- [ ] Remover criação de Action separada
- [ ] Mover configuração de Action para dentro da Rule
- [ ] Atualizar paths da API REST:
  - ❌ `/api/v5/actions` (não existe mais)
  - ✅ `/api/v5/rules` (actions inline no campo `actions[]`)
- [ ] Testar no Dashboard: Integration → Rules → (nome_rule) → Actions

---

## 🔗 Referências Oficiais

- [EMQX v6 Data Integration](https://docs.emqx.com/en/emqx/latest/data-integration/data-bridges.html)
- [EMQX v6 Rules](https://docs.emqx.com/en/emqx/latest/data-integration/rules.html)
- [EMQX v6 Webhook](https://docs.emqx.com/en/emqx/latest/data-integration/webhook.html)
- [EMQX v6 Connectors](https://docs.emqx.com/en/emqx/latest/data-integration/connector.html)
- [EMQX v6 Flow Designer](https://docs.emqx.com/en/emqx/latest/flow-designer/introduction.html)

---

**Última Atualização**: 2025-10-17 20:00 BRT  
**Versão Testada**: EMQX Enterprise 6.0.0
