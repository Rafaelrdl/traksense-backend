# Correção: EMQX Rule SQL para HMAC Funcionar

**Data:** 11 de novembro de 2025  
**Status:** 🟡 **EM PROGRESSO**

---

## 📋 Problema

A Rule SQL do EMQX está **adicionando campos extras** ao payload antes de enviar ao webhook `/ingest`:

```json
{
  "ts": 1762883583811,          // ❌ Adicionado pelo EMQX
  "topic": "...",
  "payload": "...",
  "client_id": "publisher_..."  // ❌ Adicionado pelo EMQX
}
```

Isso faz com que o **token HMAC calculado localmente não bata** com o body recebido pelo backend.

---

## ✅ Solução: Modificar a Rule SQL

### Opção 1: Enviar Payload Raw (Recomendado)

**Rule SQL Atual (que está causando o problema):**
```sql
SELECT
  clientid as client_id,
  topic,
  payload,
  timestamp as ts
FROM
  "tenants/umc/#"
```

**Rule SQL Corrigida (mantém topic, remove campos extras):**
```sql
SELECT
  topic,
  payload
FROM
  "tenants/umc/#"
```

**Por que funciona:**
- Mantém o `topic` (necessário para roteamento: tenant/site/asset)
- Mantém o `payload` (dados do sensor)
- Remove `timestamp` e `client_id` (campos extras que quebravam o HMAC)
- Body enviado será APENAS: `{"topic": "...", "payload": {...}}`
- Token HMAC pode ser calculado localmente desse body exato

---

### Opção 2: Enviar Payload String (se Opção 1 não funcionar)

```sql
SELECT
  payload as body
FROM
  "tenants/umc/#"
```

E no backend, ajustar para ler de `request.POST['body']` ou `request.data['body']`.

---

### Opção 3: Calcular HMAC no EMQX (Avançado)

O EMQX tem funções SQL para calcular hash. Podemos calcular o HMAC diretamente na Rule:

```sql
SELECT
  payload,
  topic,
  hmac('sha256', payload, '<INGESTION_SECRET>') as device_token
FROM
  "tenants/umc/#"
```

**Problema:** Precisaria hardcode do `INGESTION_SECRET` na Rule (não recomendado).

---

## 🔧 Como Aplicar no EMQX

### 1. Acessar Dashboard EMQX

```
URL: http://localhost:18083
User: admin
Pass: public
```

### 2. Ir em: Integration → Rules

Encontre a rule atual (provavelmente `forward_to_backend` ou similar).

### 3. Editar a SQL

**Substituir:**
```sql
SELECT
  clientid as client_id,
  topic,
  payload,
  timestamp as ts
FROM
  "tenants/umc/#"
```

**Por:**
```sql
SELECT
  payload
FROM
  "tenants/umc/#"
```

### 4. Salvar e Testar

---

## 🧪 Teste Completo

### 1. Publicar Mensagem MQTT Simples

Use MQTTX ou mosquitto_pub:

```bash
# Payload simples para teste
{"topic": "tenants/umc/sites/Site1/assets/ASSET-001/telemetry", "payload": {"temp": 25.5}}
```

### 2. Gerar Token HMAC

```powershell
cd "C:\Users\Rafael Ribeiro\TrakSense\traksense-backend"
python scripts/utils/generate_mqtt_token.py '{"topic": "tenants/umc/sites/Site1/assets/ASSET-001/telemetry", "payload": {"temp": 25.5}}'
```

**Output esperado:**
```
🔑 Token (x-device-token):
   f9ec9703f6951f228e90a7be5147ed397f0d9e339eb5593b3e7427e4d3a99f8e
```

### 3. Configurar Webhook no EMQX

Na action do webhook, adicionar headers:

```
Content-Type: application/json
x-tenant: umc
x-device-token: f9ec9703f6951f228e90a7be5147ed397f0d9e339eb5593b3e7427e4d3a99f8e
```

⚠️ **IMPORTANTE:** O token deve ser **fixo** porque o payload sempre será o mesmo (para teste).

### 4. Validar no Backend

Logs devem mostrar:
```
✅ Tokens batem: True
✅ [GUNICORN] post_request: Worker 7 respondeu 200 OK para /ingest
```

---

## 🎯 Solução Definitiva: Token Dinâmico

Para produção, o ideal é que **cada dispositivo tenha um token próprio** cadastrado no banco.

### Backend: Adicionar suporte a Device Token registrado

```python
# apps/ingest/views.py

# Tentar validar primeiro com HMAC
if not hmac.compare_digest(device_token, expected_token):
    # Se HMAC falhar, tentar buscar device token registrado
    from apps.assets.models import Device
    try:
        device = Device.objects.get(token=device_token)
        logger.info(f"✅ Authenticated via registered device token: {device.tag}")
    except Device.DoesNotExist:
        logger.error(f"🚨 SECURITY: Invalid device token")
        return Response({"error": "Invalid device token"}, status=401)
```

### Cadastrar Tokens de Dispositivos

```python
# No Django Admin ou via migration
device = Device.objects.get(tag='DEVICE-001')
device.token = secrets.token_hex(32)  # Gerar token único
device.save()
```

Assim cada dispositivo usa seu próprio token fixo, sem depender de HMAC do body.

---

## 📚 Referências

- **EMQX Rule SQL:** https://www.emqx.io/docs/en/latest/data-integration/rule-sql-syntax.html
- **EMQX SQL Functions:** https://www.emqx.io/docs/en/latest/data-integration/rule-sql-builtin-functions.html
- **Backend Ingest:** `apps/ingest/views.py`

---

## 👥 Autor

**Rafael Ribeiro**  
**Data:** 11 de novembro de 2025
