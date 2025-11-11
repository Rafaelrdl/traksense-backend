# Correção: MQTT Ingest Token + Site Selection

**Data:** 11 de novembro de 2025  
**Status:** 🔴 **PENDENTE - Requer Configuração**

---

## 📋 Problema 1: MQTT Ingest - 401 Unauthorized

### Erro Observado
```
[GUNICORN] pre_request: Worker 7 recebendo POST /ingest
WARNING Missing x-device-token header in ingest request
WARNING Unauthorized: /ingest
✅ [GUNICORN] post_request: Worker 7 respondeu 401 Unauthorized para /ingest
```

### Causa Raiz
O endpoint `/ingest` requer autenticação via header `x-device-token` com assinatura HMAC SHA256 do body. O MQTTX não está enviando este header.

### Solução

#### 1. Gerar INGESTION_SECRET

Execute no terminal (Python):
```bash
cd c:\Users\Rafael Ribeiro\TrakSense\traksense-backend
python -c "import secrets; print(secrets.token_hex(32))"
```

**Exemplo de output:**
```
7f3a8b9c1d2e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a
```

#### 2. Adicionar ao `.env`

Edite `traksense-backend/.env`:
```bash
# Adicione esta linha ao final do arquivo
INGESTION_SECRET=7f3a8b9c1d2e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a
```

#### 3. Reiniciar Backend

```powershell
cd "c:\Users\Rafael Ribeiro\TrakSense\traksense-backend"
docker-compose -f docker/docker-compose.yml restart api
```

#### 4. Gerar Token HMAC para MQTTX

**Script Python para gerar token:**

Crie arquivo `traksense-backend/scripts/utils/generate_mqtt_token.py`:
```python
"""
Generate HMAC token for MQTTX testing

Usage:
    python scripts/utils/generate_mqtt_token.py <payload_json>

Example:
    python scripts/utils/generate_mqtt_token.py '{"topic": "test", "value": 123}'
"""
import sys
import hmac
import hashlib
import os
from pathlib import Path

# Load .env
env_path = Path(__file__).parent.parent.parent / '.env'
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            if line.startswith('INGESTION_SECRET='):
                secret = line.split('=', 1)[1].strip()
                break
else:
    print("❌ .env file not found!")
    sys.exit(1)

if len(sys.argv) < 2:
    print("Usage: python generate_mqtt_token.py '<json_payload>'")
    print("Example: python generate_mqtt_token.py '{\"topic\": \"test\"}'")
    sys.exit(1)

payload = sys.argv[1].encode('utf-8')

# Generate HMAC signature
token = hmac.new(
    secret.encode('utf-8'),
    payload,
    hashlib.sha256
).hexdigest()

print(f"🔐 HMAC Token (x-device-token): {token}")
print(f"\n📋 Payload: {payload.decode('utf-8')}")
print(f"\n📌 Use este token no header: x-device-token: {token}")
```

**Executar:**
```powershell
cd "c:\Users\Rafael Ribeiro\TrakSense\traksense-backend"

# Exemplo com payload simples
python scripts/utils/generate_mqtt_token.py '{}'

# Output:
# 🔐 HMAC Token: abc123def456...
```

#### 5. Configurar MQTTX

**Headers a adicionar:**
```
x-device-token: <token_gerado_acima>
x-tenant: umc
Content-Type: application/json
```

**Payload exemplo:**
```json
{
  "topic": "tenants/umc/sites/Uberlândia Medical Center/assets/CHILLER-001/telemetry",
  "payload": {
    "sensor_14": 77.0,
    "sensor_15": 25.2
  }
}
```

**Importante:** O token HMAC deve ser calculado do body EXATO que você vai enviar. Se mudar o payload, o token muda!

---

## 📋 Problema 2: Site Não Selecionado na SensorsPage

### Erro Observado
```
installHook.js:1 ⚠️ Nenhum site selecionado. Aguardando seleção de site...
```

### Causa Raiz
A `SensorsPage` mostra warning quando `currentSite` é `null`, mas logo depois o site é carregado automaticamente. Este é um **log informativo**, não um erro.

### Fluxo Normal (Observado nos logs)
```
1. ⚠️ Nenhum site selecionado (inicial)
2. 📤 Request: GET /sites/
3. ✅ Carregados 1 sites disponíveis
4. 📡 Carregando devices summary do site: Uberlândia Medical Center (ID: 7)
5. ✅ 1 device(s) encontrado(s)
6. 🔄 Auto-refresh iniciado (30s)
```

### Análise
✅ **Sistema está funcionando corretamente:**
- Site é carregado automaticamente após login
- Devices são carregados com sucesso
- Telemetria é atualizada a cada 30s
- Nenhum erro real está ocorrendo

### Solução (Opcional - Melhorar UX)

Se quiser remover o warning inicial, pode ajustar a lógica de loading em `SensorsPage.tsx`:

```typescript
// traksense-hvac-monit/src/components/pages/SensorsPage.tsx

// Linhas ~80-85 (ajustar)
useEffect(() => {
  if (!currentSite) {
    // ❌ ANTES: Mostrava warning sempre
    console.warn("⚠️ Nenhum site selecionado. Aguardando seleção de site...");
    return;
  }
  
  // ✅ DEPOIS: Só mostra se sites já foram carregados
  if (!isLoadingAssets && !currentSite) {
    console.warn("⚠️ Nenhum site disponível. Verifique se há sites cadastrados.");
    return;
  }
  
  if (!currentSite) {
    // Sites ainda estão sendo carregados, não mostre warning
    return;
  }
  
  // ... resto do código
}, [currentSite, isLoadingAssets]);
```

**Ou simplesmente remova o `console.warn`** já que é um estado transitório normal.

---

## ✅ Checklist de Validação

### Backend (MQTT Ingest)
- [ ] `INGESTION_SECRET` adicionado ao `.env` (64 caracteres hex)
- [ ] Backend reiniciado (`docker-compose restart api`)
- [ ] Script `generate_mqtt_token.py` criado em `scripts/utils/`
- [ ] Token HMAC gerado para payload de teste

### MQTTX
- [ ] Header `x-device-token` configurado com token HMAC
- [ ] Header `x-tenant` configurado (exemplo: `umc`)
- [ ] Header `Content-Type` = `application/json`
- [ ] Payload JSON válido com topic MQTT

### Teste Final
- [ ] Enviar mensagem via MQTTX
- [ ] Backend responde **200 OK** (não 401)
- [ ] Logs mostram: `✅ [GUNICORN] post_request: Worker 7 respondeu 200 OK`
- [ ] Telemetria aparece no frontend

### Frontend (Site Selection)
- [ ] Site carrega automaticamente após login
- [ ] Devices aparecem na SensorsPage
- [ ] Auto-refresh funciona (30s)
- [ ] (Opcional) Warning removido ou ajustado

---

## 🧪 Teste Rápido

### 1. Gerar Token
```powershell
cd "c:\Users\Rafael Ribeiro\TrakSense\traksense-backend"

# Payload de teste (SIMPLES - apenas body vazio para começar)
python scripts/utils/generate_mqtt_token.py '{}'
```

### 2. Testar com cURL (Windows PowerShell)
```powershell
$payload = '{}'
$token = '<token_gerado_acima>'

# Teste de autenticação
curl -X POST http://umc.localhost:8000/ingest `
  -H "Content-Type: application/json" `
  -H "x-tenant: umc" `
  -H "x-device-token: $token" `
  -d $payload

# Deve retornar 200 OK ou erro de validação (não 401)
```

### 3. Testar no MQTTX
```
URL: http://umc.localhost:8000/ingest
Method: POST
Headers:
  Content-Type: application/json
  x-tenant: umc
  x-device-token: <token_gerado>
Body:
  {}
```

---

## 📚 Referências

- **Backend Ingest:** `apps/ingest/views.py` (IngestView)
- **Security Config:** `config/settings/base.py` (INGESTION_SECRET)
- **MQTT Parser:** `apps/ingest/parsers/khomp_senml.py`
- **Frontend Sensors:** `src/components/pages/SensorsPage.tsx`

---

## 👥 Autor

**Rafael Ribeiro**  
**Data:** 11 de novembro de 2025
