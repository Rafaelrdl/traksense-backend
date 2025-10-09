# 🧪 Validação Final - Fase D JE02

## Comandos Copy-Paste para Validação

### 1️⃣ Rebuild Containers (se necessário)

```powershell
cd "c:\Users\Rafael Ribeiro\Climatrak\traksense-backend\infra"

# Rebuild ingest com adapter JE02:
docker compose up -d --build ingest

# Verificar logs:
docker compose logs -f ingest
```

---

### 2️⃣ Executar Seeds

```powershell
# Criar tenant demo + 7 devices:
docker compose exec api python manage.py seed_demo_je02

# ⚠️ IMPORTANTE: Copie as credenciais MQTT exibidas!
# Exemplo:
# Username: t:demo:d:inv-01
# Password: Xy9Kp2Lm4Nq6Rs8Tv0Uw
```

---

### 3️⃣ Criar Config do Simulador

```powershell
cd "c:\Users\Rafael Ribeiro\Climatrak\traksense-backend\scripts"

# Criar arquivo de configuração (substitua PASSWORD):
@"
{
  "mqtt": {
    "host": "localhost",
    "port": 1883,
    "username": "COLE_USERNAME_AQUI",
    "password": "COLE_PASSWORD_AQUI"
  },
  "device": {
    "name": "INV-01",
    "topic_base": "traksense/demo/plant-01/inv-01"
  }
}
"@ | Out-File -FilePath sim_inv01.json -Encoding utf8
```

---

### 4️⃣ Executar Simulador

```powershell
cd "c:\Users\Rafael Ribeiro\Climatrak\traksense-backend"

# Instalar aiomqtt (se necessário):
pip install aiomqtt

# Executar simulador (publica a cada 5 segundos):
python scripts/sim_je02.py --config scripts/sim_inv01.json --period 5

# Saída esperada:
# [INV-01] ✅ Conectado!
# [INV-01] 📤 INFO publicado
# [INV-01] 📤 DATA: status=RUN, temp=23.5°C, hum=55.0%, rssi=-68dBm, rele=0
```

---

### 5️⃣ Verificar Dados no TimescaleDB

#### Dados Brutos (ts_measure)

```powershell
docker compose exec db psql -U traksense -d traksense -c "SET app.tenant_id = 'demo'; SELECT device_id, point_id, ts, v_num, v_bool, v_text, unit FROM demo.ts_measure ORDER BY ts DESC LIMIT 20;"
```

**Saída esperada**:

```
 device_id | point_id | ts                         | v_num | v_bool | v_text | unit
-----------+----------+----------------------------+-------+--------+--------+------
 inv-01    | status   | 2025-10-08 15:30:05+00     |       |        | RUN    |
 inv-01    | fault    | 2025-10-08 15:30:05+00     |       | f      |        |
 inv-01    | rssi     | 2025-10-08 15:30:05+00     | -68   |        |        | dBm
 inv-01    | var0     | 2025-10-08 15:30:05+00     | 23.5  |        |        | °C
 inv-01    | var1     | 2025-10-08 15:30:05+00     | 55.0  |        |        | %
 inv-01    | rele     | 2025-10-08 15:30:05+00     |       | t      |        |
 inv-01    | cntserr  | 2025-10-08 15:30:05+00     | 5     |        |        |
 inv-01    | uptime   | 2025-10-08 15:30:05+00     | 3600  |        |        | s
```

---

#### Agregações 1m (ts_measure_1m)

```powershell
docker compose exec db psql -U traksense -d traksense -c "SET app.tenant_id = 'demo'; SELECT device_id, point_id, bucket, avg, min, max, count FROM demo.ts_measure_1m WHERE point_id = 'var0' ORDER BY bucket DESC LIMIT 10;"
```

**Saída esperada**:

```
 device_id | point_id | bucket                     | avg  | min  | max  | count
-----------+----------+----------------------------+------+------+------+-------
 inv-01    | var0     | 2025-10-08 15:30:00+00     | 23.5 | 21.0 | 26.0 | 12
 inv-01    | var0     | 2025-10-08 15:29:00+00     | 24.2 | 22.5 | 25.8 | 12
```

---

### 6️⃣ Verificar Ingest Service

#### Logs do Ingest

```powershell
docker compose logs -f ingest | Select-String "JE02"
```

**Saída esperada**:

```
[FLUSH] Processando batch de 8 mensagens
[FLUSH] Inseridos 8 pontos de telemetria
```

---

#### Métricas Prometheus

```powershell
# Acessar métricas:
curl http://localhost:9100/metrics | Select-String "je02"
```

**Saída esperada**:

```
ingest_messages_total{type="telem_je02"} 42
ingest_messages_total{type="info_je02"} 1
```

---

### 7️⃣ Verificar EMQX

#### Dashboard EMQX

```
http://localhost:18083
Login: admin / public
```

**Verificar**:

- Clients → Deve ter 1 cliente conectado (INV-01)
- Topics → Deve ter mensagens em `traksense/demo/plant-01/inv-01/telem`

---

#### Logs EMQX

```powershell
docker compose logs -f emqx | Select-String "inv-01"
```

---

### 8️⃣ Testar API

#### Listar Devices

```powershell
curl -X GET "http://localhost:8000/api/devices/" -H "Host: demo.localhost"
```

---

#### Buscar Pontos (Raw)

```powershell
# Substitua <DEVICE_ID> pelo UUID do device
curl -X GET "http://localhost:8000/api/data/points/?device=<DEVICE_ID>&point=var0&from=now-1h" -H "Host: demo.localhost"
```

---

#### Buscar Pontos (Agregado 1m)

```powershell
curl -X GET "http://localhost:8000/api/data/points/?device=<DEVICE_ID>&point=var0&agg=1m&from=now-1h" -H "Host: demo.localhost"
```

---

### 9️⃣ Executar Testes Unitários

```powershell
cd "c:\Users\Rafael Ribeiro\Climatrak\traksense-backend\ingest"

# Instalar pytest (se necessário):
pip install pytest pytest-cov

# Executar testes:
pytest test_adapter_je02_data.py test_adapter_je02_info.py -v

# Com coverage:
pytest test_adapter_je02_data.py test_adapter_je02_info.py --cov=adapters.je02_v1 --cov-report=term-missing
```

**Saída esperada**:

```
test_adapter_je02_data.py::TestAdaptJE02Data::test_payload_valido_status_run PASSED
test_adapter_je02_data.py::TestAdaptJE02Data::test_payload_valido_status_fault PASSED
...
================================ 16 passed in 0.5s ================================
```

---

### 🔟 Validar Isolamento Tenant

#### Criar dados em tenant diferente (public)

```powershell
# Publicar em outro tenant para validar isolamento:
docker compose exec db psql -U traksense -d traksense -c "SET app.tenant_id = 'public'; SELECT COUNT(*) FROM public.ts_measure WHERE device_id = 'inv-01';"

# Resultado esperado: 0 (sem dados, isolamento OK)
```

---

## ✅ Checklist de Validação

- [ ] **Seeds executados**: Tenant demo + 7 devices criados
- [ ] **Simulador rodando**: Publicando DATA a cada 5s
- [ ] **Dados no TimescaleDB**: ts_measure e ts_measure_1m populados
- [ ] **Ingest logs**: Sem erros, batches sendo processados
- [ ] **Métricas Prometheus**: ingest_messages_total{type="telem_je02"} incrementando
- [ ] **EMQX Dashboard**: Cliente conectado, mensagens fluindo
- [ ] **API funcionando**: /api/data/points/ retorna dados
- [ ] **Testes unitários**: 16/16 passando
- [ ] **Isolamento tenant**: Dados de 'demo' não visíveis em 'public'

---

## 🐛 Troubleshooting Rápido

### Simulador não conecta

```powershell
# Verificar se EMQX está rodando:
docker compose ps emqx

# Testar conexão com mosquitto:
docker run --rm -it eclipse-mosquitto mosquitto_pub -h host.docker.internal -p 1883 -u "USERNAME" -P "PASSWORD" -t "traksense/demo/plant-01/inv-01/telem" -m '{"DATA":{"TS":1696640052,"INPUT1":1,"INPUT2":0,"VAR0":235,"VAR1":550,"WRSSI":-68,"RELE":1,"CNTSERR":0,"UPTIME":100}}'
```

---

### Dados não aparecem no banco

```powershell
# Verificar DLQ (erros):
docker compose exec db psql -U traksense -d traksense -c "SELECT * FROM public.ingest_errors ORDER BY created_at DESC LIMIT 10;"

# Verificar logs do ingest:
docker compose logs ingest --tail 50
```

---

### Testes falhando

```powershell
# Verificar se ingest/adapters/__init__.py exporta corretamente:
cd ingest
python -c "from adapters import adapt_je02_data, adapt_je02_info; print('OK')"
```

---

## 🎉 Validação Completa!

Se todos os checkboxes acima estiverem marcados, a **Fase D — JE02 está 100% validada!** 🚀
