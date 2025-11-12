# 🔧 CORREÇÃO: Remover Timestamp da SQL do EMQX

## ❌ Problema Identificado

A regra do EMQX estava usando `timestamp as ts` que gera o timestamp do **servidor EMQX**, não do equipamento.

O equipamento envia o timestamp correto no campo `bt` (base time) dentro do payload SenML.

---

## ✅ SQL Corrigida

### Antes (INCORRETO):
```sql
SELECT
  clientid as client_id,
  topic,
  payload,
  timestamp as ts
FROM
  "tenants/umc/#"
```

### Depois (CORRETO):
```sql
SELECT
  clientid as client_id,
  topic,
  payload
FROM
  "tenants/umc/#"
```

---

## 🔧 Body Template Atualizado

Também pode simplificar o Body da Action, removendo o campo `ts`:

### Antes:
```json
{
  "client_id": "${clientid}",
  "topic": "${topic}",
  "payload": ${payload},
  "qos": ${qos},
  "ts": ${timestamp}
}
```

### Depois (Opcional - mais limpo):
```json
{
  "client_id": "${clientid}",
  "topic": "${topic}",
  "payload": ${payload}
}
```

**📝 Nota:** O campo `ts` pode ficar, mas será ignorado. O sistema agora usa o `bt` do payload SenML.

---

## 🖥️ Passo a Passo no Dashboard EMQX

### 1. Editar a SQL da Rule

1. **Abrir Rule**:
   - Dashboard EMQX: http://192.168.20.60:18083
   - Menu: **Integration → Rules**
   - Clicar em `r_umc_ingest` (ou o nome da sua regra)

2. **Editar SQL**:
   - Botão: **Edit** (canto superior direito)
   - Campo: **SQL**
   - **Remover** a linha `timestamp as ts,`
   - SQL final:
   ```sql
   SELECT
     clientid as client_id,
     topic,
     payload
   FROM
     "tenants/umc/#"
   ```

3. **Salvar**:
   - Botão: **Update**
   - Verificar se status continua **Enabled** (verde)

### 2. (Opcional) Simplificar Body da Action

1. **Abrir Action**:
   - Na mesma página da rule
   - Aba: **Action Outputs**
   - Clicar em **Edit** no `forward_to_django`

2. **Editar Body**:
   - Campo: **Body**
   - Remover linha do `ts`:
   ```json
   {
     "client_id": "${clientid}",
     "topic": "${topic}",
     "payload": ${payload}
   }
   ```

3. **Salvar**:
   - Botão: **Update**

---

## ✅ Benefícios da Correção

1. **Timestamp correto**: Usa o timestamp do equipamento (bt) em vez do servidor EMQX
2. **Sem diferença de timezone**: O equipamento já envia o timestamp correto
3. **Alertas funcionam**: Dados ficam dentro da janela de 15 minutos
4. **Mais simples**: Menos campos desnecessários no payload

---

## 🧪 Validar Correção

### 1. Verificar logs da API

```powershell
cd docker
docker-compose logs -f api | Select-String "TIMESTAMP"
```

**Deve mostrar:**
```
⏰ TIMESTAMP DO EQUIPAMENTO (SenML bt) - bt=1731368344s, timestamp_utc=2025-11-11T22:19:04+00:00
```

**NÃO deve mostrar:**
```
⚠️ USANDO TIMESTAMP DO EMQX (fallback) - ...
```

### 2. Verificar banco de dados

```powershell
docker exec -w /app traksense-api python check_timestamps_db.py
```

**Esperado:**
- Timestamps com idade < 15 minutos
- Status: ✅ FRESCO

### 3. Testar alertas

```powershell
# Aguardar 1 minuto para o Celery processar
Start-Sleep -Seconds 60

# Verificar se alertas foram criados
docker exec -w /app traksense-api python -c "
from apps.alerts.models import AlertEvent
from django.db import connection

with connection.cursor() as cursor:
    cursor.execute('SET search_path TO traksense, public;')

events = AlertEvent.objects.filter(rule__name__icontains='chiller').order_by('-created_at')[:5]

for event in events:
    print(f'{event.created_at} - {event.rule.name}: {event.message}')
"
```

---

## 📊 Fluxo de Dados Corrigido

```
┌─────────────┐
│ Equipamento │
│  Khomp      │
└──────┬──────┘
       │ Envia SenML com bt (base time)
       │ [{"bn":"F80332010002C873","bt":1731368344},...]
       ↓
┌──────────────┐
│    EMQX      │
│ Rule Engine  │
└──────┬───────┘
       │ Encaminha payload completo
       │ {"client_id":"...","topic":"...","payload":[...]}
       ↓
┌──────────────┐
│   Django     │
│   API        │
└──────┬───────┘
       │ Extrai bt do payload[0]
       │ timestamp = datetime.fromtimestamp(bt)
       ↓
┌──────────────┐
│  PostgreSQL  │
│  (Reading)   │
└──────────────┘
       │ ts = timestamp do equipamento ✅
       ↓
┌──────────────┐
│    Celery    │
│ Alert Engine │
└──────────────┘
       │ Verifica: ts < 15 minutos? ✅
       │ Cria AlertEvent se condições atendidas
```

---

## 🔍 Troubleshooting

### Problema: Ainda mostra "USANDO TIMESTAMP DO EMQX"

**Causa:** Payload não está no formato SenML ou bt está ausente

**Verificar:**
```powershell
docker exec -w /app traksense-api python analyze_timestamp_source.py
```

**Solução:**
- Verificar se equipamento está enviando campo `bt` no SenML
- Verificar se o primeiro elemento do array tem `bt`

### Problema: bt está errado

**Causa:** Relógio do equipamento desajustado

**Solução:**
- Sincronizar relógio do gateway Khomp via NTP
- Configurar timezone correto no gateway

---

## 📝 Resumo

- ✅ **Remover** `timestamp as ts` da SQL da rule EMQX
- ✅ **API atualizada** para usar `bt` do payload SenML
- ✅ **Timestamps corretos** vindos do equipamento
- ✅ **Alertas funcionando** com dados dentro da janela de 15 minutos
