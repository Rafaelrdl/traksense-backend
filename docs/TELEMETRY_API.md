# API de Telemetria - TimescaleDB Continuous Aggregates

## 📋 Visão Geral

API REST para consulta de dados de telemetria IoT/HVAC com suporte a:
- ✅ **Dados brutos** (MQTT messages e sensor readings)
- ✅ **Agregações em tempo real** (1m/5m/1h via Continuous Aggregates)
- ✅ **Filtros avançados** (device_id, sensor_id, range de tempo)
- ✅ **Paginação** (LimitOffset para grandes volumes)
- ✅ **Multi-tenant** (dados isolados por schema)

---

## 🏗️ Arquitetura

### **Modelos**

#### **Telemetry** (Dados Brutos MQTT)
```python
{
  "id": 1,
  "device_id": "device_001",
  "topic": "tenants/umc/devices/001/sensors/temp",
  "payload": {"temperature": 22.5, "unit": "celsius"},
  "timestamp": "2025-10-18T10:00:00Z",
  "created_at": "2025-10-18T10:00:01Z"
}
```
- **Uso**: Mensagens MQTT completas (via EMQX)
- **Hypertable**: `telemetry` particionada por `timestamp`

#### **Reading** (Dados Estruturados para Agregação)
```python
{
  "id": 1,
  "device_id": "device_001",
  "sensor_id": "temp_01",
  "value": 22.5,
  "labels": {"unit": "celsius", "location": "room_a"},
  "ts": "2025-10-18T10:00:00Z",
  "created_at": "2025-10-18T10:00:01Z"
}
```
- **Uso**: Leituras numéricas de sensores (temperatura, umidade, etc.)
- **Hypertable**: `reading` particionada por `ts`
- **Continuous Aggregates**: `reading_1m`, `reading_5m`, `reading_1h`

---

### **TimescaleDB Continuous Aggregates**

Materialized views pré-calculadas para queries de agregação eficientes:

| View | Bucket | Política de Refresh | Retenção |
|------|--------|---------------------|----------|
| `reading_1m` | 1 minuto | A cada 1 minuto | 30 dias |
| `reading_5m` | 5 minutos | A cada 5 minutos | 60 dias |
| `reading_1h` | 1 hora | A cada 1 hora | 90 dias |

**Agregações disponíveis**:
- `avg_value`: Média dos valores no bucket
- `min_value`: Valor mínimo no bucket
- `max_value`: Valor máximo no bucket
- `last_value`: Último valor (por timestamp)
- `count`: Quantidade de leituras no bucket

**Performance**:
- ✅ Queries em CAs são **~100x mais rápidas** que agregação em tempo real
- ✅ Refresh automático pelo TimescaleDB (não bloqueia escritas)
- ✅ Ideal para dashboards e relatórios de longo período

---

## 🔌 Endpoints da API

### **Base URL** (Tenant-specific)
```
http://<tenant-domain>:8000/api/telemetry/
```

Exemplos:
- `http://umc.localhost:8000/api/telemetry/`
- `http://hospital-x.localhost:8000/api/telemetry/`

---

### **1. GET `/api/telemetry/raw/`**

Lista mensagens MQTT brutas (modelo `Telemetry`).

**Query Parameters**:
- `device_id` (string): Filtro exato por device ID
- `topic` (string): Filtro parcial por tópico MQTT
- `timestamp_from` (ISO-8601): Timestamp >= valor
- `timestamp_to` (ISO-8601): Timestamp <= valor
- `limit` (int): Quantidade de resultados (default: 200)
- `offset` (int): Offset de paginação (default: 0)

**Exemplo**:
```bash
curl "http://umc.localhost:8000/api/telemetry/raw/?device_id=device_001&timestamp_from=2025-10-18T00:00:00Z&limit=10"
```

**Resposta**:
```json
{
  "count": 150,
  "next": "http://umc.localhost:8000/api/telemetry/raw/?limit=10&offset=10",
  "previous": null,
  "results": [
    {
      "id": 1,
      "device_id": "device_001",
      "topic": "tenants/umc/devices/001/sensors/temp",
      "payload": {"temperature": 22.5, "unit": "celsius"},
      "timestamp": "2025-10-18T10:00:00Z",
      "created_at": "2025-10-18T10:00:01Z"
    }
  ]
}
```

---

### **2. GET `/api/telemetry/readings/`**

Lista leituras estruturadas de sensores (modelo `Reading`).

**Query Parameters**:
- `device_id` (string): Filtro exato por device ID
- `sensor_id` (string): Filtro exato por sensor ID
- `ts_from` (ISO-8601): Timestamp >= valor
- `ts_to` (ISO-8601): Timestamp <= valor
- `value_min` (float): Valor >= threshold
- `value_max` (float): Valor <= threshold
- `limit` (int): Quantidade de resultados (default: 200)
- `offset` (int): Offset de paginação (default: 0)

**Exemplo**:
```bash
curl "http://umc.localhost:8000/api/telemetry/readings/?sensor_id=temp_01&ts_from=2025-10-18T00:00:00Z&ts_to=2025-10-18T23:59:59Z&limit=50"
```

**Resposta**:
```json
{
  "count": 17280,
  "next": "http://umc.localhost:8000/api/telemetry/readings/?limit=50&offset=50",
  "previous": null,
  "results": [
    {
      "id": 1,
      "device_id": "device_001",
      "sensor_id": "temp_01",
      "value": 22.5,
      "labels": {"unit": "celsius", "location": "room_a"},
      "ts": "2025-10-18T10:00:00Z",
      "created_at": "2025-10-18T10:00:01Z"
    }
  ]
}
```

---

### **3. GET `/api/telemetry/series/` (Continuous Aggregates)**

Consulta séries temporais agregadas (pré-calculadas pelo TimescaleDB).

**Query Parameters** (obrigatório):
- `bucket` **(required)**: `1m` | `5m` | `1h` - Tamanho do bucket de agregação

**Filtros opcionais**:
- `device_id` (string): Filtro por device
- `sensor_id` (string): Filtro por sensor
- `from` (ISO-8601): Início do período
- `to` (ISO-8601): Fim do período
- `limit` (int): Max resultados (default: 500, max: 5000)
- `offset` (int): Offset de paginação (default: 0)

**Exemplo 1: Agregação de 1 minuto**
```bash
curl "http://umc.localhost:8000/api/telemetry/series/?bucket=1m&sensor_id=temp_01&from=2025-10-18T10:00:00Z&to=2025-10-18T11:00:00Z&limit=100"
```

**Exemplo 2: Agregação de 1 hora (análise de longo período)**
```bash
curl "http://umc.localhost:8000/api/telemetry/series/?bucket=1h&sensor_id=temp_01&from=2025-10-01T00:00:00Z&to=2025-10-18T23:59:59Z&limit=500"
```

**Resposta**:
```json
[
  {
    "bucket": "2025-10-18T10:00:00Z",
    "device_id": "device_001",
    "sensor_id": "temp_01",
    "avg_value": 22.5,
    "min_value": 22.1,
    "max_value": 22.9,
    "last_value": 22.7,
    "count": 12
  },
  {
    "bucket": "2025-10-18T10:01:00Z",
    "device_id": "device_001",
    "sensor_id": "temp_01",
    "avg_value": 22.6,
    "min_value": 22.2,
    "max_value": 23.0,
    "last_value": 22.8,
    "count": 12
  }
]
```

**Performance Tips**:
- ✅ Use `1m` para períodos de **horas** (últimas 24h)
- ✅ Use `5m` para períodos de **dias** (última semana)
- ✅ Use `1h` para períodos de **meses** (último trimestre)
- ⚠️ Evite queries sem `from`/`to` em datasets grandes

---

## 🛠️ Setup e Migração

### **1. Instalar Dependências**
```bash
docker exec traksense-api pip install django-filter==24.2
# Ou rebuild da imagem
docker compose build api
```

### **2. Executar Migrations (por tenant)**
```bash
# Public schema (sem Reading/CAs)
docker exec traksense-api python manage.py migrate_schemas --schema=public

# Tenant schema (com Reading + Hypertable + CAs)
docker exec traksense-api python manage.py migrate_schemas --schema=uberlandia_medical_center
```

**O que as migrations fazem**:
1. `0003_reading.py`: Cria modelo `Reading`
2. `0004_timescale_continuous_aggregates.py`:
   - Converte `reading` em hypertable (particionada por `ts`)
   - Cria materialized views `reading_1m`, `reading_5m`, `reading_1h`
   - Adiciona policies de refresh automático

### **3. Validar Hypertable**
```bash
docker exec -it traksense-postgres psql -U postgres -d traksense -c "
SET search_path TO uberlandia_medical_center;
SELECT * FROM timescaledb_information.hypertables WHERE hypertable_name='reading';
"
```

### **4. Validar Continuous Aggregates**
```bash
docker exec -it traksense-postgres psql -U postgres -d traksense -c "
SET search_path TO uberlandia_medical_center;
SELECT view_name, materialized_only, refresh_lag, refresh_interval 
FROM timescaledb_information.continuous_aggregates 
WHERE view_name LIKE 'reading_%';
"
```

### **5. Verificar Dados MQTT Recebidos**
```bash
# Verificar últimas leituras recebidas (últimos 5 minutos)
docker exec traksense-api python -c "
from apps.ingest.models import SensorReading
from django.utils import timezone
from datetime import timedelta

cutoff = timezone.now() - timedelta(minutes=5)
recent = SensorReading.objects.filter(created_at__gte=cutoff)
print(f'Leituras recebidas nos últimos 5 minutos: {recent.count()}')
for r in recent[:10]:
    print(f'{r.device_id} | {r.sensor_id} | {r.value} | {r.ts}')
"

# Verificar volume de dados por device
docker exec traksense-api python -c "
from apps.ingest.models import SensorReading
from django.db.models import Count

stats = SensorReading.objects.values('device_id').annotate(total=Count('id')).order_by('-total')
for s in stats[:5]:
    print(f'{s['device_id']}: {s['total']} leituras')
"
```

---

## 🧪 Testes Manuais

### **Cenário 1: Leituras Brutas (últimas 24h)**
```bash
FROM=$(date -u -d '1 day ago' +%Y-%m-%dT%H:%M:%SZ)
TO=$(date -u +%Y-%m-%dT%H:%M:%SZ)

curl "http://umc.localhost:8000/api/telemetry/readings/?sensor_id=temp_01&ts_from=$FROM&ts_to=$TO&limit=100"
```

### **Cenário 2: Agregação 1 minuto (última hora)**
```bash
FROM=$(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ)
TO=$(date -u +%Y-%m-%dT%H:%M:%SZ)

curl "http://umc.localhost:8000/api/telemetry/series/?bucket=1m&sensor_id=temp_01&from=$FROM&to=$TO&limit=60"
```

### **Cenário 3: Agregação 1 hora (último mês)**
```bash
FROM=$(date -u -d '30 days ago' +%Y-%m-%dT%H:%M:%SZ)
TO=$(date -u +%Y-%m-%dT%H:%M:%SZ)

curl "http://umc.localhost:8000/api/telemetry/series/?bucket=1h&sensor_id=temp_01&from=$FROM&to=$TO&limit=720"
```

### **Cenário 4: Filtro por Threshold (valores acima de 23°C)**
```bash
curl "http://umc.localhost:8000/api/telemetry/readings/?sensor_id=temp_01&value_min=23.0&limit=50"
```

---

## 📊 Performance & Otimização

### **Query Performance Comparison**

| Endpoint | Dataset | Query Time | Use Case |
|----------|---------|------------|----------|
| `/readings/` | 1M rows | ~2-5s | Dados brutos (debugging) |
| `/series/?bucket=1m` | 1M rows → 16K buckets | ~50-100ms | Gráficos em tempo real |
| `/series/?bucket=1h` | 1M rows → 720 buckets | ~20-50ms | Dashboards executivos |

### **Limites Recomendados**

| Bucket | Período Máximo | Motivo |
|--------|----------------|--------|
| `1m` | 7 dias | ~10K buckets (navegável) |
| `5m` | 30 dias | ~8.6K buckets (ideal para semanas) |
| `1h` | 90 dias | ~2.2K buckets (ideal para meses) |

### **Índices TimescaleDB**

Criados automaticamente pela hypertable:
- `(device_id, sensor_id, ts)` - Query principal
- `(sensor_id, ts)` - Query por sensor
- Chunk index por partição de tempo (1 dia)

---

## 🔐 Segurança

- ✅ **Multi-tenant isolation**: Queries automáticas no schema do tenant
- ✅ **SQL Injection protection**: Queries parametrizadas com `cursor.execute(sql, params)`
- ✅ **Rate limiting**: Máximo de 5000 resultados por request (`/series/`)
- ✅ **Input validation**: Validação de bucket, limit, offset
- ⚠️ **Authentication**: Adicionar DRF auth em produção (JWT/Token)

---

## 📖 Documentação OpenAPI

Acesse a documentação interativa:
- **Swagger UI**: http://umc.localhost:8000/api/docs/
- **ReDoc**: http://umc.localhost:8000/api/redoc/
- **Schema JSON**: http://umc.localhost:8000/api/schema/

---

## 🐛 Troubleshooting

### **Erro: "relation reading does not exist"**
**Causa**: Migration não executada no tenant.  
**Solução**: `docker exec traksense-api python manage.py migrate_schemas --schema=uberlandia_medical_center`

### **Erro: "Invalid bucket. Must be one of: 1m, 5m, 1h"**
**Causa**: Parâmetro `bucket` inválido ou ausente.  
**Solução**: `curl "...?bucket=1m&..."`

### **CA não atualiza**
**Causa**: Policy de refresh não criada ou desabilitada.  
**Solução**: Verificar policies:
```sql
SELECT * FROM timescaledb_information.job_stats 
WHERE hypertable_name LIKE 'reading_%';
```

### **Performance ruim em `/readings/`**
**Causa**: Query sem filtros em dataset grande (full table scan).  
**Solução**: Sempre usar `ts_from`/`ts_to` ou `sensor_id` para limitar range.

---

## 📚 Referências

- [TimescaleDB Continuous Aggregates](https://docs.timescale.com/use-timescale/latest/continuous-aggregates/)
- [Django Filter Documentation](https://django-filter.readthedocs.io/)
- [DRF Pagination](https://www.django-rest-framework.org/api-guide/pagination/)
- [drf-spectacular OpenAPI](https://drf-spectacular.readthedocs.io/)

---

**Última atualização**: 18/10/2025  
**Versões**: Django 5.0.1 | DRF 3.14.0 | django-filter 24.2 | TimescaleDB 2.x
