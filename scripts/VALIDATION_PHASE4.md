# Validação Fase 4 - Ingest Assíncrono

## 📋 Visão Geral

Este documento descreve o processo de validação do serviço de ingest assíncrono implementado na Fase 4.

**Status:** 🟡 EM ANDAMENTO

**Objetivo:** Validar serviço de ingest com ≥5k points/s, latência ≤1s, DLQ funcional e idempotência

---

## ✅ Checklist de Validação

### 1. Infraestrutura

- [ ] Containers rodando (api, db, emqx, redis, **ingest**)
- [ ] Migração 0002 aplicada (tabelas `ingest_errors` e `cmd_ack`)
- [ ] Broker EMQX acessível em `emqx:1883`
- [ ] TimescaleDB acessível em `db:5432`
- [ ] Métricas Prometheus expostas em `:9100/metrics`

**Como validar:**
```bash
docker compose ps
docker compose exec api python manage.py showmigrations timeseries
curl http://localhost:9100/metrics | grep ingest_
```

---

### 2. Conectividade MQTT

- [ ] Producer conecta ao broker EMQX
- [ ] Subscrição de tópicos bem-sucedida
- [ ] QoS=1 configurado corretamente
- [ ] Reconexão automática em caso de falha

**Como validar:**
```bash
python scripts/validate_phase4.py
# Output esperado: [✅ OK] MQTT connect: emqx:1883
```

---

### 3. Persistência de Telemetria

- [ ] Payload normalizado (schema v1) inserido em `ts_measure`
- [ ] Payload vendor-específico (parsec_v1) normalizado e inserido
- [ ] RLS (Row Level Security) respeitado via `app.tenant_id`
- [ ] Batch insert funcional

**Como validar:**
```bash
# Publicar telemetria via MQTT
docker compose exec api python -c "
import paho.mqtt.client as mqtt
import json

client = mqtt.Client()
client.connect('emqx', 1883)

payload = {
    'schema': 'v1',
    'ts': '2025-10-07T15:30:00Z',
    'points': [
        {'name': 'temp_agua', 't': 'float', 'v': 25.5, 'u': '°C'}
    ],
    'meta': {'fw': '1.0.0', 'src': 'test'}
}

client.publish('traksense/test_alpha/factory/device123/telem', json.dumps(payload))
client.disconnect()
"

# Aguardar 2s para ingest processar
sleep 2

# Verificar no banco
docker compose exec db psql -U postgres -d traksense -c "
SELECT COUNT(*) FROM public.ts_measure 
WHERE tenant_id = 'test_alpha' AND device_id = 'device123';
"
# Esperado: COUNT >= 1
```

---

### 4. Dead Letter Queue (DLQ)

- [ ] Payload JSON inválido vai para `ingest_errors`
- [ ] Payload com campos faltando vai para `ingest_errors`
- [ ] Coluna `reason` contém motivo do erro
- [ ] Payload original preservado na coluna `payload`

**Como validar:**
```bash
# Publicar payload inválido
docker compose exec api python -c "
import paho.mqtt.client as mqtt

client = mqtt.Client()
client.connect('emqx', 1883)

# JSON inválido
client.publish('traksense/test_alpha/factory/device123/telem', '{invalid json')

# Payload sem campo obrigatório 'ts'
import json
client.publish('traksense/test_alpha/factory/device123/telem', 
               json.dumps({'schema': 'v1', 'points': []}))

client.disconnect()
"

sleep 2

# Verificar DLQ
docker compose exec db psql -U postgres -d traksense -c "
SELECT tenant_id, topic, reason FROM public.ingest_errors LIMIT 5;
"
# Esperado: >= 2 registros com motivos claros
```

---

### 5. Idempotência de ACKs

- [ ] ACKs com mesmo `cmd_id` fazem UPSERT (não duplicam)
- [ ] Coluna `updated_at` atualizada em duplicatas
- [ ] Primary key `(tenant_id, device_id, cmd_id)` funcional

**Como validar:**
```bash
# Publicar ACK duplicado
docker compose exec api python -c "
import paho.mqtt.client as mqtt
import json

client = mqtt.Client()
client.connect('emqx', 1883)

ack = {
    'schema': 'v1',
    'cmd_id': '01HQZC5K3M8YBQWER7TXZ9V2P3',
    'ok': True,
    'ts_exec': '2025-10-07T15:30:00Z'
}

# Publicar 3x o mesmo ACK
for _ in range(3):
    client.publish('traksense/test_alpha/factory/device123/ack', json.dumps(ack))

client.disconnect()
"

sleep 2

# Verificar que há apenas 1 registro
docker compose exec db psql -U postgres -d traksense -c "
SELECT COUNT(*) FROM public.cmd_ack WHERE cmd_id = '01HQZC5K3M8YBQWER7TXZ9V2P3';
"
# Esperado: COUNT = 1 (não 3)
```

---

### 6. Throughput (Meta: ≥5k p/s)

- [ ] Script de validação insere 10k pontos em ≤2s
- [ ] Métricas `ingest_points_total` incrementadas corretamente
- [ ] CPU do container ingest ≤200%
- [ ] Sem erros de timeout ou backpressure

**Como validar:**
```bash
python scripts/validate_phase4.py
# Output esperado: [✅ OK] Metrics points_total increased: 10000 pontos em X.XXs ≈ 5000+ p/s
```

---

### 7. Latência (Meta: p50 ≤1s)

- [ ] Latência média device→persisted ≤1s
- [ ] Sem spikes prolongados (>5s)
- [ ] Histogram `ingest_latency_seconds` com p50/p95/p99

**Como validar:**
```bash
python scripts/validate_phase4.py
# Output esperado: [✅ OK] p50 ingest latency: 0.XXXs (target <= 1.0s)
```

---

### 8. Out-of-Order Timestamps

- [ ] Inserts com timestamps fora de ordem aceitos sem erro
- [ ] Dados consultáveis corretamente após ingest
- [ ] Agregados funcionam após out-of-order

**Como validar:**
```bash
# Publicar 3 mensagens com timestamps invertidos
docker compose exec api python -c "
import paho.mqtt.client as mqtt
import json

client = mqtt.Client()
client.connect('emqx', 1883)

# Ordem: 15:02, 15:01, 15:03 (fora de ordem)
for ts in ['2025-10-07T15:02:00Z', '2025-10-07T15:01:00Z', '2025-10-07T15:03:00Z']:
    payload = {
        'schema': 'v1',
        'ts': ts,
        'points': [{'name': 'test_point', 't': 'float', 'v': 10.0}],
        'meta': {}
    }
    client.publish('traksense/test_alpha/factory/device_ooo/telem', json.dumps(payload))

client.disconnect()
"

sleep 2

# Verificar que todos foram inseridos
docker compose exec db psql -U postgres -d traksense -c "
SELECT COUNT(*) FROM public.ts_measure WHERE device_id = 'device_ooo';
"
# Esperado: COUNT = 3
```

---

### 9. Métricas Prometheus

- [ ] Endpoint `:9100/metrics` acessível
- [ ] Métricas `ingest_messages_total`, `ingest_points_total` presentes
- [ ] Métricas `ingest_errors_total` por reason
- [ ] Histogramas `ingest_batch_size`, `ingest_latency_seconds`
- [ ] Gauge `ingest_queue_size`

**Como validar:**
```bash
curl -s http://localhost:9100/metrics | grep ingest_

# Esperado:
# ingest_messages_total{type="telem"} X
# ingest_points_total X
# ingest_errors_total{reason="parse_error"} X
# ingest_batch_size_bucket{le="500"} X
# ingest_latency_seconds_bucket{le="1.0"} X
# ingest_queue_size X
```

---

### 10. Backpressure

- [ ] Fila `asyncio.Queue(maxsize=50000)` criada
- [ ] Producer bloqueia quando fila cheia
- [ ] Batcher drena fila sem estouro de memória
- [ ] Sem mensagens perdidas durante backpressure

**Como validar:**
```bash
# Publicar burst de 60k mensagens rapidamente
docker compose exec api python scripts/test_backpressure.py

# Verificar logs do ingest
docker compose logs ingest | grep QUEUE
# Esperado: mensagens indicando fila próxima ao limite, mas sem erros
```

---

## 📊 Métricas de Sucesso

| Métrica                      | Meta           | Resultado | Status |
|------------------------------|----------------|-----------|--------|
| Throughput (points/s)        | ≥ 5,000        | -         | 🟡     |
| Latência p50 (segundos)      | ≤ 1.0          | -         | 🟡     |
| Taxa de erro (%)             | < 1%           | -         | 🟡     |
| CPU por container (%)        | ≤ 200%         | -         | 🟡     |
| Memória por container (MB)   | ≤ 512          | -         | 🟡     |
| Payloads em DLQ              | Todos capturados| -        | 🟡     |
| ACKs duplicados              | 0 (upsert)     | -         | 🟡     |
| Out-of-order aceitos         | 100%           | -         | 🟡     |

---

## 🚀 Execução Rápida

```bash
# 1. Subir stack completa
docker compose up -d --build

# 2. Aplicar migrações
docker compose exec api python manage.py migrate

# 3. Executar validação automatizada
python scripts/validate_phase4.py

# 4. Visualizar métricas
curl http://localhost:9100/metrics | grep ingest_

# 5. Ver logs do ingest
docker compose logs -f ingest
```

---

## 🐛 Troubleshooting

### Erro: ModuleNotFoundError: No module named 'asyncio_mqtt'

**Solução:**
```bash
docker compose exec ingest pip install -r /app/requirements.txt
docker compose restart ingest
```

### Erro: MQTT connect failed

**Verificar:**
```bash
docker compose ps emqx
docker compose logs emqx | tail -20
```

### Erro: relation "public.ingest_errors" does not exist

**Solução:**
```bash
docker compose exec api python manage.py migrate timeseries
```

### Throughput < 5k p/s

**Possíveis causas:**
- Batch size muito pequeno → aumentar `INGEST_BATCH_SIZE`
- Batch timeout muito curto → aumentar `INGEST_BATCH_MS`
- Pool DB pequeno → aumentar `DB_POOL_MAX`
- Windows sem uvloop → usar Linux/macOS para prod

---

## 📝 Notas Finais

- **Retenção DLQ:** Executar periodicamente `DELETE FROM ingest_errors WHERE ts < NOW() - INTERVAL '14 days'`
- **Monitoramento:** Integrar métricas Prometheus com Grafana para dashboards
- **Performance:** Para >10k p/s, evoluir para `copy_records_to_table()` agrupando por tenant
- **HA:** Deploy de múltiplas instâncias do ingest (load balance via EMQX shared subscription)

---

**Data:** 2025-10-07  
**Autor:** TrakSense Team
