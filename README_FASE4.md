# Fase 4 - Ingest Assíncrono de Alta Performance

## 📊 Visão Geral

Implementação de um serviço de ingestão assíncrono para consumir telemetria IoT via MQTT e persistir no TimescaleDB com alta performance e confiabilidade.

**Status:** ✅ IMPLEMENTADO

**Performance Targets:**
- **Throughput:** ≥5,000 points/s (dev)
- **Latência p50:** ≤1.0s (device timestamp → persisted)
- **CPU:** ≤200% por container
- **Memória:** ~256MB

---

## 🏗️ Arquitetura

```
[Dispositivos IoT]
      |
      v (publica MQTT)
  [EMQX Broker]
      |
      v (subscribe traksense/+/+/+/telem)
[Producer Task] ---enfileira---> [asyncio.Queue (maxsize=50k)]
                                        |
                                        v (consome)
                                  [Batcher Task]
                                        |
                                        v (flush por tamanho OU tempo)
                                  [Buffer]
                                        |
                                        v (batch insert com RLS)
                      [TimescaleDB public.ts_measure]
```

### Producer-Consumer Pattern

**Producer:** Consome MQTT e enfileira mensagens com metadata (tenant/site/device/kind)

**Batcher:** Coleta da fila e persiste em lotes

**Backpressure:** Queue com maxsize bloqueia producer automaticamente

---

## 📂 Estrutura de Arquivos

```
ingest/
├── main.py                    # Ponto de entrada (producer/batcher/flush)
├── config.py                  # Configuração via env vars
├── models.py                  # Schemas Pydantic (TelemetryV1, AckV1)
├── requirements.txt           # Dependências Python
├── Dockerfile                 # Container image
├── test_ingest.py             # Testes pytest
└── adapters/
    ├── __init__.py            # Exports (normalize_parsec_v1)
    ├── types.py               # Type hints
    └── (parsec_v1 integrado)  # Adapter para inversores Parsec

backend/apps/timeseries/migrations/
└── 0002_ingest_dlq_ack.py     # Migração SQL (tabelas DLQ e ACK)

scripts/
├── validate_phase4.py         # Validação automatizada
└── VALIDATION_PHASE4.md       # Documentação de validação

infra/
├── docker-compose.yml         # Serviço ingest adicionado
└── .env.ingest                # Variáveis de ambiente
```

---

## ⚙️ Configuração

### Variáveis de Ambiente (`.env.ingest`)

```bash
# MQTT Broker
MQTT_URL=mqtt://emqx:1883
MQTT_TOPICS=traksense/+/+/+/telem,traksense/+/+/+/ack
MQTT_QOS=1

# Backpressure & Batching
INGEST_QUEUE_MAX=50000
INGEST_BATCH_SIZE=800
INGEST_BATCH_MS=250

# Database
DATABASE_URL=postgresql://postgres:postgres@db:5432/traksense
DB_POOL_MIN=2
DB_POOL_MAX=8

# Observability
METRICS_PORT=9100
```

### Tuning de Performance

**Aumentar Throughput:**
- ↑ `INGEST_BATCH_SIZE` (500 → 1000)
- ↑ `DB_POOL_MAX` (8 → 16)
- ↓ `INGEST_BATCH_MS` (250 → 150)

**Reduzir Latência:**
- ↓ `INGEST_BATCH_SIZE` (800 → 300)
- ↓ `INGEST_BATCH_MS` (250 → 100)

**Ajustar Backpressure:**
- ↑ `INGEST_QUEUE_MAX` (50000 → 100000) - mais buffer

---

## 🚀 Uso

### 1. Subir Stack Completa

```bash
cd infra
docker compose up -d --build
```

### 2. Aplicar Migrações

```bash
docker compose exec api python manage.py migrate
```

### 3. Verificar Logs

```bash
docker compose logs -f ingest
```

Saída esperada:
```
[MAIN] uvloop instalado com sucesso
[MAIN] Métricas expostas em http://0.0.0.0:9100/metrics
[MAIN] Pool de conexões criado (min=2, max=8)
[MAIN] Fila criada (maxsize=50000)
[PRODUCER] Conectando ao broker emqx:1883
[PRODUCER] Subscrito: traksense/+/+/+/telem (QoS=1)
[BATCHER] Iniciado (batch_size=800, batch_ms=250)
```

### 4. Publicar Telemetria

```python
import paho.mqtt.client as mqtt
import json

client = mqtt.Client()
client.connect('localhost', 1883)

payload = {
    'schema': 'v1',
    'ts': '2025-10-07T15:30:00Z',
    'points': [
        {'name': 'temp_agua', 't': 'float', 'v': 7.3, 'u': '°C'},
        {'name': 'compressor_1_on', 't': 'bool', 'v': True}
    ],
    'meta': {'fw': '1.2.3', 'src': 'test'}
}

client.publish('traksense/test_tenant/factory/device123/telem', json.dumps(payload))
client.disconnect()
```

### 5. Verificar Métricas

```bash
curl http://localhost:9100/metrics | grep ingest_

# Saída:
# ingest_messages_total{type="telem"} 1250
# ingest_points_total 3500
# ingest_errors_total{reason="parse_error"} 3
# ingest_batch_size_bucket{le="500"} 5
# ingest_latency_seconds_sum 45.2
# ingest_queue_size 120
```

---

## ✅ Validação

### Executar Validação Automatizada

```bash
python scripts/validate_phase4.py
```

Saída esperada:
```
================================================================================
VALIDAÇÃO FASE 4 - Ingest Assíncrono
================================================================================

🔌 CHECK 1: Conectividade MQTT
[✅ OK] MQTT connect: emqx:1883

💾 CHECK 2: Persistência
[✅ OK] Inserted telemetry rows: 1 rows

🚨 CHECK 3: Dead Letter Queue
[✅ OK] DLQ captured invalid payloads: 1 errors

⚡ CHECK 4: Throughput Smoke Test
[✅ OK] Metrics points_total increased: 10000 pontos em 2.01s ≈ 4975 p/s

⏱️  CHECK 5: Latência Média
[✅ OK] p50 ingest latency: 0.723s (target <= 1.0s)

================================================================================
✅ ALL CHECKS PASSED
================================================================================
```

### Checklist Manual

Ver `scripts/VALIDATION_PHASE4.md` para validações detalhadas de:
- DLQ (payloads inválidos)
- Idempotência de ACKs
- Out-of-order timestamps
- Backpressure
- Métricas Prometheus

---

## 📊 Features Implementadas

### ✅ Batching Inteligente
- Flush por tamanho (INGEST_BATCH_SIZE)
- Flush por tempo (INGEST_BATCH_MS)
- Evita micro-inserts e latência excessiva

### ✅ Backpressure Automática
- `asyncio.Queue(maxsize=50000)`
- Producer bloqueia quando fila cheia
- Previne estouro de memória

### ✅ DLQ (Dead Letter Queue)
- Tabela `public.ingest_errors`
- Captura JSON inválido, ValidationError, etc.
- Preserva payload original + motivo do erro
- Retenção: 14 dias (cron manual)

### ✅ Idempotência de ACKs
- Tabela `public.cmd_ack`
- Primary key `(tenant_id, device_id, cmd_id)`
- UPSERT via `ON CONFLICT DO UPDATE`
- Previne duplicação de ACKs

### ✅ Métricas Prometheus
- Contadores: messages_total, points_total, errors_total
- Histogramas: batch_size, latency_seconds
- Gauges: queue_size
- Endpoint: `:9100/metrics`

### ✅ Out-of-Order Timestamps
- TimescaleDB aceita inserts desordenados
- Sem necessidade de ordenação prévia
- Agregados funcionam corretamente

### ✅ RLS (Row Level Security)
- GUC `app.tenant_id` setado por inserção
- Isolamento multi-tenant garantido
- Compatível com middleware Django

### ✅ Performance
- **uvloop:** Event loop otimizado (Linux/macOS)
- **orjson:** JSON parsing ultra-rápido
- **asyncpg:** Driver PostgreSQL assíncrono nativo
- **Connection pooling:** Min/max configurável

---

## 🐛 Troubleshooting

### Erro: "asyncio_mqtt" not found

```bash
docker compose exec ingest pip install -r /app/requirements.txt
docker compose restart ingest
```

### Throughput Baixo (<5k p/s)

**Causas possíveis:**
- Batch size muito pequeno → aumentar `INGEST_BATCH_SIZE`
- Pool DB limitado → aumentar `DB_POOL_MAX`
- Windows (sem uvloop) → usar Linux/Docker para prod

**Verificar:**
```bash
docker stats ingest  # CPU/RAM
docker compose logs ingest | grep FLUSH  # Tamanho dos batches
```

### Latência Alta (>1s p50)

**Causas possíveis:**
- Batch timeout muito alto → reduzir `INGEST_BATCH_MS`
- Fila congestionada → verificar `ingest_queue_size`

**Verificar:**
```bash
curl http://localhost:9100/metrics | grep latency_seconds
```

### Payloads Não Chegam ao Banco

**Verificar:**
1. MQTT connect: `docker compose logs ingest | grep PRODUCER`
2. Subscrição: `docker compose logs ingest | grep Subscrito`
3. Parsing: `docker compose logs ingest | grep FLUSH`
4. DLQ: `docker compose exec db psql -U postgres -d traksense -c "SELECT * FROM ingest_errors LIMIT 5;"`

---

## 📚 Documentação Adicional

- **Validação Completa:** `scripts/VALIDATION_PHASE4.md`
- **Schemas Pydantic:** `ingest/models.py`
- **Adapters:** `ingest/adapters/__init__.py`
- **Migrações SQL:** `backend/apps/timeseries/migrations/0002_ingest_dlq_ack.py`
- **Custom Instructions:** `.github/copilot-instructions.md`

---

## 🎯 Próximos Passos (Opcional)

1. **DRF Endpoint:** `POST /api/ingest/test` para publicar via HTTP (debug)
2. **Pytest Fixtures:** Converter scripts paho-mqtt para pytest
3. **Grafana Dashboard:** Visualizar métricas Prometheus
4. **Password Rotation:** Rotação automática de credenciais MQTT (90 dias)
5. **Copy Records:** Evoluir para `copy_records_to_table()` (>10k p/s)
6. **Shared Subscription:** EMQX load balancing entre múltiplas instâncias

---

**Autor:** TrakSense Team  
**Data:** 2025-10-07  
**Versão:** Fase 4 - Ingest Assíncrono
