# Fase D — JE02: Templates + Adapter + Seeds + Simulador MQTT

## 📋 Visão Geral

Esta fase implementa suporte completo ao protocolo JE02 para inversores IoT, incluindo:

- ✅ **DeviceTemplate + PointTemplates**: 8 pontos de telemetria (status, fault, rssi, var0, var1, rele, cntserr, uptime)
- ✅ **DashboardTemplate**: 8 painéis (StatusPanel, TimelinePanel, KPI, TimeseriesPanel)
- ✅ **Adapter JE02**: Normalização de payloads DATA e INFO
- ✅ **Seeds**: Criação de tenant demo + 7 inversores com provisioning EMQX
- ✅ **Simulador MQTT**: Script Python para simular devices JE02
- ✅ **Testes Unitários**: Cobertura completa do adapter

---

## 🚀 Quick Start

### 1. Aplicar Migrations

```bash
# Aplicar migrations do template JE02:
docker compose exec api python manage.py migrate templates

# Verificar templates criados:
docker compose exec api python manage.py shell
>>> from apps.templates.models import DeviceTemplate
>>> DeviceTemplate.objects.filter(code='inverter_je02_v1')
```

### 2. Criar Dados Demo

```bash
# Executar seed: cria tenant 'demo' + 7 devices + provisioning EMQX
docker compose exec api python manage.py seed_demo_je02

# Saída esperada:
# ✅ Tenant criado: demo
# ✅ 7 devices criados: INV-01, INV-02, ..., INV-07
# ✅ EMQX provisionado com credenciais
# ✅ DashboardConfigs criados
```

**⚠️ IMPORTANTE**: Salve as credenciais MQTT exibidas! Você precisará delas para o simulador.

### 3. Executar Simulador

```bash
# 1. Criar arquivo de configuração (copie credenciais do seed):
cat > sim_inv01.json <<EOF
{
  "mqtt": {
    "host": "localhost",
    "port": 1883,
    "username": "t:demo:d:inv-01",
    "password": "COLE_SENHA_AQUI"
  },
  "device": {
    "name": "INV-01",
    "topic_base": "traksense/demo/plant-01/inv-01"
  }
}
EOF

# 2. Executar simulador (publica a cada 5 segundos):
python scripts/sim_je02.py --config sim_inv01.json --period 5

# Saída esperada:
# [INV-01] ✅ Conectado!
# [INV-01] 📤 DATA: status=RUN, temp=23.5°C, hum=55.0%, rssi=-68dBm, rele=0
```

### 4. Verificar Dados

```bash
# Verificar dados no TimescaleDB:
docker compose exec db psql -U traksense -d traksense -c "
  SET app.tenant_id = 'demo';
  SELECT device_id, point_id, ts, v_num, v_bool, v_text 
  FROM demo.ts_measure 
  ORDER BY ts DESC 
  LIMIT 20;
"

# Verificar agregações 1m:
docker compose exec db psql -U traksense -d traksense -c "
  SET app.tenant_id = 'demo';
  SELECT device_id, point_id, bucket, avg, min, max, count 
  FROM demo.ts_measure_1m 
  ORDER BY bucket DESC 
  LIMIT 10;
"

# Verificar API (substitua DEVICE_ID):
curl -X GET "http://localhost:8000/api/data/points/?device=<DEVICE_ID>&point=var0&agg=1m&from=now-1h" \
  -H "Host: demo.localhost"
```

---

## 📐 Arquitetura

### Protocolo JE02

#### Payload DATA (Telemetria)

```json
{
  "DATA": {
    "TS": 1696640052,
    "INPUT1": 1,
    "INPUT2": 0,
    "VAR0": 235,
    "VAR1": 550,
    "WRSSI": -68,
    "RELE": 1,
    "CNTSERR": 5,
    "UPTIME": 3600
  }
}
```

**Mapeamento para PointTemplates**:

| Campo      | PointTemplate | Tipo | Unidade | Transformação         |
| ---------- | ------------- | ---- | ------- | --------------------- |
| INPUT1/2   | status        | ENUM | -       | FAULT/RUN/STOP        |
| INPUT2     | fault         | BOOL | -       | INPUT2 == 1           |
| WRSSI      | rssi          | NUM  | dBm     | Direto (negativo)     |
| UPTIME     | uptime        | NUM  | s       | Direto                |
| CNTSERR    | cntserr       | NUM  | -       | Direto                |
| VAR0       | var0          | NUM  | °C      | VAR0 / 10.0           |
| VAR1       | var1          | NUM  | %       | VAR1 / 10.0           |
| RELE       | rele          | BOOL | -       | RELE != 0             |

**Regras de Status**:

- `INPUT2 == 1` → `FAULT`
- `INPUT1 == 1` (e INPUT2 == 0) → `RUN`
- Senão → `STOP`

#### Payload INFO (Metadados)

```json
{
  "INFO": {
    "FW_VERSION": "1.2.3",
    "HW_VERSION": "v1",
    "DEVICE_ID": "INV-01",
    "MODEL": "JE02-INVERTER"
  }
}
```

Armazenado como metadata JSONB (não gera pontos de telemetria).

---

## 🗂️ Estrutura de Arquivos

```
traksense-backend/
├── backend/
│   └── apps/
│       ├── templates/
│       │   └── migrations/
│       │       ├── 0003_je02_device_template.py      ✅ DeviceTemplate + 8 PointTemplates
│       │       └── 0004_je02_dashboard_template.py   ✅ DashboardTemplate + 8 painéis
│       └── devices/
│           └── management/
│               └── commands/
│                   └── seed_demo_je02.py             ✅ Seeds tenant + devices
├── ingest/
│   ├── adapters/
│   │   ├── je02_v1.py                                ✅ Adapter JE02 (DATA + INFO)
│   │   └── __init__.py                               ✅ Exports
│   ├── main.py                                       ✅ Detecção JE02 (chave DATA/INFO)
│   ├── test_adapter_je02_data.py                     ✅ 10 testes unitários
│   └── test_adapter_je02_info.py                     ✅ 6 testes unitários
└── scripts/
    ├── sim_je02.py                                   ✅ Simulador MQTT
    └── sim_inv01_example.json                        ✅ Config exemplo
```

---

## 🔧 Comandos Úteis

### Seeds

```bash
# Criar seed demo (7 devices):
docker compose exec api python manage.py seed_demo_je02

# Limpar e recriar:
docker compose exec api python manage.py seed_demo_je02 --clean

# Provisionar device específico manualmente:
docker compose exec api python manage.py tenant_command provision_emqx \
    <DEVICE_ID> plant-01 --schema=demo
```

### Simulador

```bash
# Simulador simples (1 device):
python scripts/sim_je02.py --config sim_inv01.json --period 5

# Com suporte a comandos:
python scripts/sim_je02.py --config sim_inv01.json --listen-cmd

# Múltiplos devices (use tmux ou screen):
python scripts/sim_je02.py --config sim_inv01.json &
python scripts/sim_je02.py --config sim_inv02.json &
# ...
```

### Testes

```bash
# Testes unitários do adapter:
cd ingest
pytest test_adapter_je02_data.py test_adapter_je02_info.py -v

# Com coverage:
pytest test_adapter_je02_data.py test_adapter_je02_info.py \
    --cov=adapters.je02_v1 \
    --cov-report=term-missing

# Executar todos os testes do ingest:
pytest -v
```

### Logs

```bash
# Logs do ingest service:
docker compose logs -f ingest

# Logs do EMQX (conexões MQTT):
docker compose logs -f emqx

# Logs do API (Django):
docker compose logs -f api
```

---

## 🐛 Troubleshooting

### Problema: Simulador não consegue conectar

**Sintomas**:

```
[INV-01] ❌ Erro MQTT: Connection refused
```

**Solução**:

1. Verificar se EMQX está rodando: `docker compose ps emqx`
2. Verificar porta 1883: `netstat -an | findstr 1883` (Windows)
3. Verificar credenciais: username/password corretos?
4. Testar com mosquitto_pub:

```bash
mosquitto_pub -h localhost -p 1883 \
  -u "t:demo:d:inv-01" \
  -P "<PASSWORD>" \
  -t "traksense/demo/plant-01/inv-01/telem" \
  -m '{"DATA":{"TS":1696640052,"INPUT1":1,"INPUT2":0,"VAR0":235,"VAR1":550,"WRSSI":-68,"RELE":1,"CNTSERR":0,"UPTIME":100}}'
```

---

### Problema: Dados não aparecem no TimescaleDB

**Sintomas**:

```sql
SELECT * FROM demo.ts_measure WHERE device_id = 'inv-01';
-- (0 rows)
```

**Solução**:

1. Verificar se ingest está rodando: `docker compose ps ingest`
2. Verificar logs do ingest: `docker compose logs -f ingest`
3. Verificar DLQ (Dead Letter Queue):

```sql
SELECT * FROM public.ingest_errors ORDER BY created_at DESC LIMIT 10;
```

4. Verificar se payload está chegando no EMQX:

```bash
docker compose exec emqx emqx_ctl broker stats
```

5. Testar adapter manualmente:

```python
from ingest.adapters import adapt_je02_data
payload = {"DATA": {...}}
ts, points, meta = adapt_je02_data(payload)
print(points)
```

---

### Problema: Dashboard não exibe dados

**Sintomas**: Dashboard carrega mas gráficos estão vazios

**Solução**:

1. Verificar se device tem DashboardConfig:

```sql
SELECT * FROM demo.dashboard_config WHERE device_id = '<DEVICE_ID>';
```

2. Verificar se dados existem no período:

```sql
SELECT * FROM demo.ts_measure_1m 
WHERE device_id = '<DEVICE_ID>' 
AND bucket > NOW() - INTERVAL '1 hour'
ORDER BY bucket DESC;
```

3. Verificar filtros do dashboard (range de tempo, agregação)
4. Verificar logs do navegador (DevTools → Console)

---

### Problema: EMQX ACL negando acesso

**Sintomas**:

```
[INV-01] ❌ Erro MQTT: Not authorized
```

**Solução**:

1. Verificar ACL no EMQX Dashboard: http://localhost:18083
2. Login: admin / public
3. Navegar: Access Control → Authorization → Rules
4. Verificar se regra existe para `traksense/demo/plant-01/inv-01/#`
5. Re-provisionar device:

```bash
docker compose exec api python manage.py tenant_command provision_emqx \
    <DEVICE_ID> plant-01 --schema=demo
```

---

## 📊 Métricas e Monitoramento

### Métricas Prometheus (Ingest)

```bash
# Acessar métricas:
curl http://localhost:9100/metrics

# Principais métricas:
# - ingest_messages_total{type="telem_je02"}: Total de mensagens JE02 processadas
# - ingest_points_total: Total de pontos de telemetria inseridos
# - ingest_errors_total{reason="parse_error"}: Total de erros
# - ingest_batch_size: Tamanho dos batches (histograma)
# - ingest_latency_seconds: Latência device→DB (histograma)
```

### Dashboards EMQX

```bash
# Acessar EMQX Dashboard:
http://localhost:18083
# Login: admin / public

# Verificar:
# - Clients conectados
# - Messages/second (throughput)
# - ACL rules
# - Retained messages
```

---

## 🧪 Testes

### Testes Unitários (Adapter)

**test_adapter_je02_data.py** (10 testes):

- ✅ Payload válido status RUN
- ✅ Payload válido status FAULT
- ✅ Payload válido status STOP
- ✅ Escala VAR0/VAR1 (÷10)
- ✅ RELE boolean (!=0)
- ✅ Timestamp Unix → datetime
- ✅ Payload sem chave DATA
- ✅ Payload DATA incompleto
- ✅ Valores extremos

**test_adapter_je02_info.py** (6 testes):

- ✅ Payload INFO válido
- ✅ Campos extras preservados
- ✅ INFO vazio
- ✅ Sem chave INFO
- ✅ INFO nulo
- ✅ Estrutura aninhada preservada

---

## 📝 Próximos Passos

### Fase E (Opcional):

- [ ] Comandos downlink: `SET_RELE`, `RESET_FAULT`
- [ ] Testes de integração E2E
- [ ] Simulador multi-device (1 processo → 7 devices)
- [ ] Alarmes baseados em thresholds (var0, rssi, cntserr)
- [ ] Dashboard Grafana para métricas Prometheus

---

## 📚 Referências

- **DeviceTemplate**: `backend/apps/templates/models.py`
- **DashboardTemplate**: `backend/apps/dashboards/models.py`
- **Adapter JE02**: `ingest/adapters/je02_v1.py`
- **Ingest Service**: `ingest/main.py`
- **EMQX Provisioning**: `backend/apps/devices/services.py`
- **Seeds**: `backend/apps/devices/management/commands/seed_demo_je02.py`
- **Simulador**: `scripts/sim_je02.py`

---

## 👥 Autor

**TrakSense Team**  
Data: 2025-10-08 (Fase D - JE02)

---

## ✅ Checklist de Validação

- [x] DeviceTemplate `inverter_je02_v1` criado com 8 PointTemplates
- [x] DashboardTemplate criado com 8 painéis configurados
- [x] Adapter JE02 implementado (DATA + INFO)
- [x] Adapter integrado no ingest/main.py
- [x] Seeds seed_demo_je02 criado e testado
- [x] Simulador sim_je02.py criado e testado
- [x] Testes unitários do adapter (16 testes total)
- [x] Documentação README completa
- [ ] Validação E2E com 7 devices simultâneos
- [ ] Verificação de isolamento tenant (demo vs public)
- [ ] Teste de dashboards com dados reais

---

**🎉 Fase D Completa! 🎉**
