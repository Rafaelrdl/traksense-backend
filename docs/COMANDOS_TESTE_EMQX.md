# 🧪 Comandos de Teste - Validação EMQX

> Comandos prontos para copiar/colar após corrigir header x-tenant no Dashboard

---

## 1️⃣ Publicar Mensagem de Teste MQTT

```powershell
# Publicar 1 mensagem
docker run --rm --network docker_traksense eclipse-mosquitto mosquitto_pub `
  -h traksense-emqx `
  -p 1883 `
  -t "tenants/umc/devices/device-test-001/sensors/temperature" `
  -m '{"value": 99.9, "unit": "celsius"}'
```

**Resultado Esperado**: Comando retorna sem erros

---

## 2️⃣ Verificar Logs da API

```powershell
# Buscar log de telemetria salva (últimas 20 linhas)
docker logs traksense-api --tail 20 | Select-String -Pattern "Telemetry saved"
```

**Resultado Esperado**:
```
INFO views Telemetry saved: tenant=uberlandia-medical-center, device=device-test-001, topic=tenants/umc/devices/device-test-001/sensors/temperature
```

---

## 3️⃣ Verificar Banco de Dados

```powershell
# Contar registros
docker exec traksense-postgres psql -U app -d app -c "
  SET search_path TO uberlandia_medical_center;
  SELECT COUNT(*) as total FROM telemetry;
"
```

**Resultado Esperado**: `total = 6` (5 HTTP + 1 MQTT)

```powershell
# Ver último registro
docker exec traksense-postgres psql -U app -d app -c "
  SET search_path TO uberlandia_medical_center;
  SELECT 
    id, 
    device_id, 
    payload->>'value' as temp,
    payload->>'unit' as unit,
    topic,
    timestamp,
    created_at
  FROM telemetry
  ORDER BY created_at DESC
  LIMIT 1;
"
```

**Resultado Esperado**:
```
 id |   device_id    | temp | unit    | topic                                         | timestamp              | created_at
----+----------------+------+---------+-----------------------------------------------+------------------------+---------------------------
  6 | device-test-001| 99.9 | celsius | tenants/umc/devices/device-test-001/sensors/...| 2025-10-17 22:XX:XX+00 | 2025-10-17 22:XX:XX+00
```

---

## 4️⃣ Publicar Múltiplas Mensagens

```powershell
# Publicar 5 mensagens de diferentes dispositivos
for ($i=1; $i -le 5; $i++) {
    docker run --rm --network docker_traksense eclipse-mosquitto mosquitto_pub `
      -h traksense-emqx `
      -p 1883 `
      -t "tenants/umc/devices/sensor-$i/sensors/temperature" `
      -m "{`"value`": $($20 + $i), `"unit`": `"celsius`"}"
    
    Write-Host "✅ Mensagem $i publicada"
    Start-Sleep -Milliseconds 500
}
```

**Resultado Esperado**: 5 mensagens publicadas com sucesso

---

## 5️⃣ Validar Contagem Final

```powershell
# Deve ter 11 registros (5 HTTP + 1 teste + 5 múltiplas)
docker exec traksense-postgres psql -U app -d app -c "
  SET search_path TO uberlandia_medical_center;
  SELECT 
    COUNT(*) as total,
    MIN(created_at) as primeira_msg,
    MAX(created_at) as ultima_msg,
    COUNT(DISTINCT device_id) as dispositivos_unicos
  FROM telemetry;
"
```

**Resultado Esperado**:
```
 total | primeira_msg            | ultima_msg              | dispositivos_unicos
-------+-------------------------+-------------------------+--------------------
    11 | 2025-10-17 22:41:46+00  | 2025-10-17 22:XX:XX+00  |                 10
```

---

## 6️⃣ Testar Diferentes Tipos de Sensores

```powershell
# Temperatura
docker run --rm --network docker_traksense eclipse-mosquitto mosquitto_pub `
  -h traksense-emqx -p 1883 `
  -t "tenants/umc/devices/hvac-001/sensors/temperature" `
  -m '{"value": 22.5, "unit": "celsius"}'

# Umidade
docker run --rm --network docker_traksense eclipse-mosquitto mosquitto_pub `
  -h traksense-emqx -p 1883 `
  -t "tenants/umc/devices/hvac-001/sensors/humidity" `
  -m '{"value": 65.0, "unit": "percent"}'

# Pressão
docker run --rm --network docker_traksense eclipse-mosquitto mosquitto_pub `
  -h traksense-emqx -p 1883 `
  -t "tenants/umc/devices/hvac-001/sensors/pressure" `
  -m '{"value": 1013.25, "unit": "hPa"}'

# CO2
docker run --rm --network docker_traksense eclipse-mosquitto mosquitto_pub `
  -h traksense-emqx -p 1883 `
  -t "tenants/umc/devices/hvac-001/sensors/co2" `
  -m '{"value": 450, "unit": "ppm"}'
```

---

## 7️⃣ Consultas Analíticas (TimescaleDB)

### Últimas 10 leituras
```powershell
docker exec traksense-postgres psql -U app -d app -c "
  SET search_path TO uberlandia_medical_center;
  SELECT 
    device_id,
    topic,
    payload->>'value' as valor,
    payload->>'unit' as unidade,
    timestamp
  FROM telemetry
  ORDER BY timestamp DESC
  LIMIT 10;
"
```

### Média de temperatura por hora
```powershell
docker exec traksense-postgres psql -U app -d app -c "
  SET search_path TO uberlandia_medical_center;
  SELECT 
    time_bucket('1 hour', timestamp) AS hora,
    AVG((payload->>'value')::float) as temp_media,
    COUNT(*) as leituras
  FROM telemetry
  WHERE topic LIKE '%temperature%'
  GROUP BY hora
  ORDER BY hora DESC;
"
```

### Estatísticas por dispositivo
```powershell
docker exec traksense-postgres psql -U app -d app -c "
  SET search_path TO uberlandia_medical_center;
  SELECT 
    device_id,
    COUNT(*) as total_leituras,
    MIN(created_at) as primeira_leitura,
    MAX(created_at) as ultima_leitura
  FROM telemetry
  GROUP BY device_id
  ORDER BY total_leituras DESC;
"
```

---

## 8️⃣ Limpar Dados de Teste (Opcional)

```powershell
# ⚠️ CUIDADO: Remove TODOS os registros da tabela telemetry
docker exec traksense-postgres psql -U app -d app -c "
  SET search_path TO uberlandia_medical_center;
  TRUNCATE TABLE telemetry;
  SELECT COUNT(*) as total FROM telemetry;
"
```

**Resultado Esperado**: `total = 0`

---

## 9️⃣ Monitoramento em Tempo Real

### Terminal 1: Logs da API
```powershell
# Monitorar logs continuamente
docker logs traksense-api --follow | Select-String -Pattern "ingest|Telemetry"
```

### Terminal 2: Publicar Mensagens
```powershell
# Em outra janela, publicar mensagens
docker run --rm --network docker_traksense eclipse-mosquitto mosquitto_pub `
  -h traksense-emqx -p 1883 `
  -t "tenants/umc/devices/test-real-time/sensors/temperature" `
  -m '{"value": 25.0, "unit": "celsius"}'
```

**Resultado Esperado no Terminal 1**:
```
INFO views Telemetry saved: tenant=uberlandia-medical-center, device=test-real-time, ...
```

---

## 🔟 Verificar Métricas EMQX via API

```powershell
# Obter estatísticas da Rule
docker exec traksense-api curl -s -u 'admin:Tr@kS3ns3!' `
  'http://emqx:18083/api/v5/rules/r_umc_ingest' | python -m json.tool
```

**Resultado Esperado**: JSON com métricas `matched`, `success`, `failed`

---

## 🎯 Checklist de Validação Completa

Execute na ordem:

```powershell
# 1. Publicar mensagem teste
docker run --rm --network docker_traksense eclipse-mosquitto mosquitto_pub -h traksense-emqx -p 1883 -t "tenants/umc/devices/final-test/sensors/temperature" -m '{"value": 100, "unit": "celsius"}'

# 2. Aguardar 2 segundos
Start-Sleep -Seconds 2

# 3. Verificar log
docker logs traksense-api --tail 5 | Select-String "Telemetry saved"

# 4. Verificar banco
docker exec traksense-postgres psql -U app -d app -c "SET search_path TO uberlandia_medical_center; SELECT COUNT(*) FROM telemetry WHERE device_id='final-test';"

# 5. Se resultado = 1, então ✅ VALIDAÇÃO COMPLETA
```

---

## 📊 Exemplo de Saída Completa

```
PS> docker run --rm --network docker_traksense eclipse-mosquitto mosquitto_pub ...
✅ (sem erros)

PS> docker logs traksense-api --tail 5
INFO 2025-10-17 22:30:15 views Telemetry saved: tenant=uberlandia-medical-center, device=final-test, topic=tenants/umc/devices/final-test/sensors/temperature

PS> docker exec traksense-postgres psql ...
 count
-------
     1
(1 row)

✅ SUCESSO: Fluxo MQTT → EMQX → Django → TimescaleDB funcionando!
```

---

**Última Atualização**: 2025-10-17 19:50 BRT  
**Pré-requisito**: Header `x-tenant` corrigido no EMQX Dashboard
