# 🔧 Correção do Body na Action do EMQX

## 🐛 Problema Identificado

Os dados estão sendo salvos no banco, mas com o **device_id errado**:

```
❌ Salvo como: test_publisher_1760933082 (client_id do MQTT)
✅ Deveria ser: GW-1760908415 (device_id do payload)
```

## 📊 Logs Observados

```
INFO Telemetry saved: tenant=umc, device=test_publisher_1760933082, topic=tenants/umc/GW-1760908415
✅ [GUNICORN] post_request: Worker 6 respondeu 202 Accepted para /ingest
```

**Status**: ✅ Backend recebeu e salvou
**Problema**: ❌ Device ID incorreto

## 🎯 Solução: Corrigir Body da Action no EMQX

### Passo 1: Acessar EMQX Dashboard

```
URL: http://localhost:18083
User: admin
Pass: newpass123
```

### Passo 2: Editar Action

1. Navegue: **Data Integration → Rules → r_umc_ingest**
2. Clique na action: **forward_to_django**
3. Clique em: **Edit**
4. Role até a seção: **Body**

### Passo 3: Configurar Body Correto

**❌ NÃO USE** (passa tudo sem estrutura):
```json
${.}
```

**✅ USE ESTE** (estrutura correta esperada pelo backend):
```json
{
  "client_id": "${clientid}",
  "topic": "${topic}",
  "payload": ${payload},
  "ts": ${timestamp}
}
```

**⚠️ ATENÇÃO**: Note que `${payload}` **NÃO tem aspas** porque já é um objeto JSON!

### Passo 4: Salvar e Testar

1. Clique em **Update**
2. Execute novamente: `python publish_test_telemetry.py`
3. Verifique no frontend: http://umc.localhost:5000/sensors

## 📝 O Que Cada Campo Significa

| Campo | Descrição | Exemplo |
|-------|-----------|---------|
| `client_id` | ID do cliente MQTT conectado | `test_publisher_1760933082` |
| `topic` | Tópico MQTT completo | `tenants/umc/GW-1760908415` |
| `payload` | **Objeto JSON** com dados dos sensores | `{"device_id": "GW-1760908415", "sensors": [...]}` |
| `ts` | Timestamp Unix em milissegundos | `1760933082123` |

## 🔍 Como o Backend Processa

```python
# apps/ingest/views.py (linha ~117)
device_id = payload.get('device_id') if isinstance(payload, dict) else None
if not device_id:
    logger.warning(f"Missing device_id in payload. Using client_id as fallback: {client_id}")
    device_id = client_id  # ← Fallback que está sendo usado agora!
```

**Fluxo Atual (Errado)**:
1. EMQX envia body sem estrutura correta
2. Backend não consegue extrair `device_id` do `payload`
3. Backend usa `client_id` como fallback
4. Salva com device_id = `test_publisher_1760933082`

**Fluxo Correto**:
1. EMQX envia body estruturado com `payload` como objeto
2. Backend extrai `device_id` do `payload.get('device_id')`
3. Pega `GW-1760908415` corretamente
4. Salva e consultas funcionam!

## ✅ Validação

Após corrigir, você deve ver nos logs:

```
INFO Telemetry saved: tenant=umc, device=test_publisher_1760933082, topic=tenants/umc/GW-1760908415
```

E no summary deve retornar:

```json
{
  "device_id": "GW-1760908415",
  "device_name2": "GW-1760908415",
  "total_sensors": 4,  ← Agora aparecerão os 4 sensores!
  "sensors": [
    {"sensor_id": "TEMP-AMB-001", ...},
    {"sensor_id": "HUM-001", ...},
    {"sensor_id": "TEMP-WATER-IN-001", ...},
    {"sensor_id": "TEMP-WATER-OUT-001", ...}
  ]
}
```

## 🎯 Resultado Esperado no Frontend

- ✅ **4 sensores** no contador "Sensores Online"
- ✅ **4 cards** na tabela de sensores
- ✅ Device ID correto: `GW-1760908415`
- ✅ Sensores: TEMP-AMB-001, HUM-001, TEMP-WATER-IN-001, TEMP-WATER-OUT-001
