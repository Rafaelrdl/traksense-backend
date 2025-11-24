# 🧪 GUIA DE TESTE - TELEMETRIA COM DADOS REAIS

**Data**: 24 de novembro de 2025  
**Objetivo**: Validar endpoints de telemetria do backend com dados reais via MQTT

---

## 📋 **PRÉ-REQUISITOS**

### **1. Backend Rodando**

```bash
cd c:\Users\Rafael Ribeiro\TrakSense\traksense-backend
docker-compose up -d
```

Verificar:
```bash
docker ps | grep traksense
```

Deve mostrar:
- ✅ `traksense-api` (running)
- ✅ `traksense-db` (running)
- ✅ `traksense-emqx` (running)

### **2. Tenant Configurado**

Verificar tenant 'umc' existe:
```bash
docker exec -it traksense-api python manage.py shell
```

```python
from apps.tenants.models import Tenant
print(Tenant.objects.filter(schema_name='umc').exists())
# Deve retornar: True
```

### **3. Devices e Sensores Reais**

Os devices devem ser cadastrados via interface web ou API e enviar dados via MQTT.
Não há mais scripts de geração de dados mockados.

---

## 🚀 **TESTE 1: VALIDAR RECEPÇÃO DE DADOS MQTT**

### **Verificar Rule Engine EMQX**

```bash
docker exec -it traksense-emqx emqx_ctl rules list
```

### **Verificar Leituras Recebidas**

```bash
docker exec -it traksense-api python manage.py shell
```

```python
from django_tenants.utils import schema_context
from apps.ingest.models import Reading

with schema_context('umc'):
    count = Reading.objects.count()
    print(f"Total readings: {count}")
    
    # Verificar range de datas
    first = Reading.objects.order_by('ts').first()
    last = Reading.objects.order_by('-ts').first()
    if first:
        print(f"Primeiro: {first.ts}")
        print(f"Último: {last.ts}")
    
    # Verificar devices únicos
    devices = Reading.objects.values_list('device_id', flat=True).distinct()
    print(f"Devices: {list(devices)}")
```
```

**Resultado esperado**:
```
Total readings: 7200
Primeiro: 2025-10-18 20:30:00+00:00
Último: 2025-10-19 20:30:00+00:00
Devices: ['device_001', 'device_002']
```

✅ **TESTE 1 PASSOU** se count > 0

---

## 🌐 **TESTE 2: ENDPOINT LATEST**

### **Request**

```bash
curl -X GET "http://umc.localhost:8000/api/telemetry/latest/device_001/" \
  -H "accept: application/json"
```

### **Response Esperada** (200 OK)

```json
{
  "device_id": "device_001",
  "last_update": "2025-10-19T20:30:00Z",
  "count": 3,
  "readings": [
    {
      "id": 12345,
      "device_id": "device_001",
      "sensor_id": "TEMPERATURE_1",
      "value": 22.5,
      "labels": {
        "sensor_name": "Temperatura",
        "sensor_type": "TEMPERATURE",
        "unit": "°C"
      },
      "ts": "2025-10-19T20:30:00Z",
      "created_at": "2025-10-19T20:30:01Z"
    },
    // ... mais sensores
  ]
}
```

### **Validações**

- ✅ Status code: 200
- ✅ `device_id` = "device_001"
- ✅ `count` = número de sensores do device
- ✅ `readings` é array não vazio
- ✅ Cada reading tem: `sensor_id`, `value`, `ts`
- ✅ `last_update` é timestamp recente

### **Teste com Sensor Específico**

```bash
curl -X GET "http://umc.localhost:8000/api/telemetry/latest/device_001/?sensor_id=TEMPERATURE_1" \
  -H "accept: application/json"
```

**Deve retornar apenas 1 reading**

✅ **TESTE 2 PASSOU** se response válida e count > 0

---

## 📊 **TESTE 3: ENDPOINT HISTORY**

### **3A: História Completa (24h, auto-agregação)**

```bash
curl -X GET "http://umc.localhost:8000/api/telemetry/history/device_001/" \
  -H "accept: application/json"
```

**Response esperada**:
```json
{
  "device_id": "device_001",
  "sensor_id": null,
  "interval": "5m",
  "from": "2025-10-18T20:30:00Z",
  "to": "2025-10-19T20:30:00Z",
  "count": 864,
  "data": [
    {
      "bucket": "2025-10-19T20:25:00Z",
      "sensor_id": "TEMPERATURE_1",
      "avg_value": 22.45,
      "min_value": 22.1,
      "max_value": 22.8,
      "last_value": 22.5,
      "count": 5
    },
    // ... mais buckets
  ]
}
```

**Validações**:
- ✅ `interval` = "5m" (auto para 24h)
- ✅ `count` > 0
- ✅ `data` é array
- ✅ Cada ponto tem: `bucket`, `avg_value`, `min_value`, `max_value`

### **3B: Dados Brutos (raw)**

```bash
curl -X GET "http://umc.localhost:8000/api/telemetry/history/device_001/?interval=raw&from=2025-10-19T20:00:00Z" \
  -H "accept: application/json"
```

**Response esperada**:
```json
{
  "device_id": "device_001",
  "interval": "raw",
  "from": "2025-10-19T20:00:00Z",
  "to": "2025-10-19T20:30:00Z",
  "count": 90,
  "data": [
    {
      "ts": "2025-10-19T20:30:00Z",
      "sensor_id": "TEMPERATURE_1",
      "value": 22.5
    },
    // ... mais pontos
  ]
}
```

**Validações**:
- ✅ `interval` = "raw"
- ✅ Dados não agregados (apenas `ts`, `sensor_id`, `value`)
- ✅ `count` ≈ (range em segundos / 60)

### **3C: Sensor Específico**

```bash
curl -X GET "http://umc.localhost:8000/api/telemetry/history/device_001/?sensor_id=TEMPERATURE_1&interval=1m" \
  -H "accept: application/json"
```

**Validações**:
- ✅ Todos pontos têm `sensor_id` = "TEMPERATURE_1"
- ✅ `interval` = "1m"

✅ **TESTE 3 PASSOU** se todos sub-testes OK

---

## 📋 **TESTE 4: ENDPOINT SUMMARY**

### **Request**

```bash
curl -X GET "http://umc.localhost:8000/api/telemetry/device/device_001/summary/" \
  -H "accept: application/json"
```

### **Response Esperada** (200 OK)

```json
{
  "device_id": "device_001",
  "status": "online",
  "last_seen": "2025-10-19T20:30:00Z",
  "sensors": [
    {
      "sensor_id": "TEMPERATURE_1",
      "last_value": 22.5,
      "last_reading": "2025-10-19T20:30:00Z",
      "unit": "°C",
      "status": "ok"
    },
    {
      "sensor_id": "HUMIDITY_1",
      "last_value": 65.0,
      "last_reading": "2025-10-19T20:29:55Z",
      "unit": "%",
      "status": "ok"
    }
  ],
  "statistics": {
    "total_readings_24h": 4320,
    "sensor_count": 3,
    "avg_interval": "60s"
  }
}
```

### **Validações**

- ✅ Status code: 200
- ✅ `device_id` = "device_001"
- ✅ `status` = "online" ou "offline"
- ✅ `sensors` é array não vazio
- ✅ Cada sensor tem: `sensor_id`, `last_value`, `last_reading`, `unit`, `status`
- ✅ `statistics.total_readings_24h` > 0
- ✅ `statistics.sensor_count` = length de `sensors`
- ✅ `statistics.avg_interval` tem formato "Xs"

✅ **TESTE 4 PASSOU** se response válida

---

## 🚫 **TESTE 5: ERROR HANDLING**

### **5A: Device Não Encontrado**

```bash
curl -X GET "http://umc.localhost:8000/api/telemetry/latest/device_nao_existe/" \
  -H "accept: application/json"
```

**Response esperada** (404 Not Found):
```json
{
  "detail": "No readings found for this device"
}
```

### **5B: Range Inválido**

```bash
curl -X GET "http://umc.localhost:8000/api/telemetry/history/device_001/?from=2025-10-20T00:00:00Z&to=2025-10-19T00:00:00Z" \
  -H "accept: application/json"
```

**Response esperada** (400 Bad Request):
```json
{
  "detail": "Invalid time range: from must be before to"
}
```

### **5C: Limit Inválido**

```bash
curl -X GET "http://umc.localhost:8000/api/telemetry/history/device_001/?limit=abc" \
  -H "accept: application/json"
```

**Response esperada** (400 Bad Request):
```json
{
  "detail": "Invalid limit parameter"
}
```

✅ **TESTE 5 PASSOU** se todos erros retornados corretamente

---

## 📖 **TESTE 6: DOCUMENTAÇÃO OPENAPI**

### **6A: Acessar Swagger UI**

Abrir navegador:
```
http://umc.localhost:8000/api/docs/
```

**Verificar**:
- ✅ Página carrega sem erros
- ✅ Seção "telemetry" existe
- ✅ 6 endpoints listados:
  - GET /api/telemetry/raw/
  - GET /api/telemetry/readings/
  - GET /api/telemetry/series/
  - GET /api/telemetry/latest/{device_id}/
  - GET /api/telemetry/history/{device_id}/
  - GET /api/telemetry/device/{device_id}/summary/

### **6B: Testar pelo Swagger**

1. Clicar em **GET /api/telemetry/latest/{device_id}/**
2. Clicar em **"Try it out"**
3. Preencher `device_id`: `device_001`
4. Clicar em **"Execute"**
5. Verificar response 200 OK

✅ **TESTE 6 PASSOU** se Swagger funciona

---

## 🔄 **TESTE 7: PERFORMANCE**

### **7A: Query com Histórico Extenso**

Após acumular dados por algumas horas/dias, testar performance:

```bash
time curl -X GET "http://umc.localhost:8000/api/telemetry/history/device_001/?interval=1h" \
  -H "accept: application/json" -o /dev/null -s -w "%{time_total}\n"
```

**Resultado esperado**: < 2 segundos
  -H "accept: application/json" -o /dev/null -s -w "%{time_total}\n"
```

**Resultado esperado**: < 2 segundos

### **7B: Query com Muitos Dados (Carga Alta)**

Aguardar acúmulo de dados (24-48h de operação) e testar:

```bash
time curl -X GET "http://umc.localhost:8000/api/telemetry/history/device_001/?interval=1h&from=2025-01-01T00:00:00Z" \
  -H "accept: application/json" -o /dev/null -s -w "%{time_total}\n"
```

**Resultado esperado**: < 3 segundos mesmo com alto volume

✅ **TESTE 7 PASSOU** se performance aceitável

---

## ✅ **CHECKLIST FINAL**

- [ ] TESTE 1: Dados MQTT recebidos e salvos no banco
- [ ] TESTE 2: Endpoint latest funciona com dados reais
- [ ] TESTE 3: Endpoint history funciona (raw + agregado)
- [ ] TESTE 4: Endpoint summary funciona
- [ ] TESTE 5: Error handling correto
- [ ] TESTE 6: Documentação OpenAPI acessível
- [ ] TESTE 7: Performance aceitável

---

## 🎉 **RESULTADO ESPERADO**

```
✅ Todos os 7 testes passaram!

Backend de telemetria validado com dados reais MQTT.
Sistema pronto para monitoramento em produção.
```

---

## 🐛 **TROUBLESHOOTING**

### **Erro: Device not found**

**Causa**: Device não cadastrado na interface web

**Solução**:
1. Acessar http://umc.localhost:3000/assets
2. Criar device via interface web
3. Associar device_id correto no EMQX Rule

### **Erro: No readings found**

**Causa**: MQTT não está publicando ou Rule Engine com erro

**Solução**:
```bash
# 1. Verificar logs do EMQX
docker logs traksense-emqx --tail 50

# 2. Verificar se rule está ativa
# Acessar http://localhost:18083 (EMQX Dashboard)
# Ir em Rules → Verificar status da rule

# 3. Testar publicação manual via MQTTX
# (ver instruções no GUIA_MQTTX_TESTE.md)
```

### **Erro: 500 Internal Server Error**

**Causa**: Backend não rodando ou erro de código

**Solução**:
```bash
# Ver logs
docker logs traksense-api --tail 50

# Reiniciar
docker restart traksense-api
```

### **Erro: Connection refused**

**Causa**: PostgreSQL não acessível

**Solução**:
```bash
docker-compose down
docker-compose up -d
```

### **Erro: Timestamps incorretos**

**Causa**: Timezone mal configurado ou timestamps em formato errado

**Solução**:
```bash
# Verificar formato dos dados no banco
docker exec -it traksense-api python -c "
from apps.ingest.models import SensorReading
readings = SensorReading.objects.all().order_by('-ts')[:5]
for r in readings:
    print(f'{r.device_id} | {r.ts} | {r.created_at}')
"
```

---

**EXECUTE OS TESTES E VALIDE O BACKEND COM DADOS REAIS!** 🚀
