# 🔍 GUIA DE DIAGNÓSTICO DE TIMESTAMPS

## 1. Preparação

### 1.1 Reiniciar a API para ativar os novos logs
```powershell
cd "c:\Users\Rafael Ribeiro\TrakSense\traksense-backend"
docker-compose restart api
```

### 1.2 Acompanhar os logs em tempo real
```powershell
docker-compose logs -f api
```

## 2. Teste com Nova Mensagem MQTT

### 2.1 Publicar mensagem via MQTTX

**Configuração:**
- Server: mqtt://192.168.20.60:1883
- Topic: `v1/devices/F80332010002C873/data`
- QoS: 1

**Payload de teste:**
```json
[
  {
    "bn": "F80332010002C873",
    "bt": 1737000000
  },
  {
    "n": "temperatura_saida",
    "v": 8.5,
    "u": "Cel",
    "t": 0
  },
  {
    "n": "temperatura_retorno", 
    "v": 25.0,
    "u": "Cel",
    "t": 1
  },
  {
    "n": "estado",
    "v": 1,
    "u": "",
    "t": 2
  }
]
```

**Valores importantes:**
- `temperatura_saida = 8.5` (deve disparar alerta pois > 6°C)
- `temperatura_retorno = 25.0` (deve disparar alerta pois > 20°C)
- `estado = 1` (ligado)

### 2.2 O que observar nos logs

Você deve ver logs como:

```
⏰ TIMESTAMP RECEBIDO - ts_original=1737000000000ms, ts_convertido_utc=2025-01-15T18:40:00+00:00, timestamp_unix=1737000000.0
```

E também:

```
📊 READING CRIADO - sensor_id=F80332010002C873_temperatura_saida, value=8.5, timestamp_sensor=None, reading_timestamp=2025-01-15T18:40:00+00:00
📊 READING CRIADO - sensor_id=F80332010002C873_temperatura_retorno, value=25.0, timestamp_sensor=None, reading_timestamp=2025-01-15T18:40:00.001000+00:00
📊 READING CRIADO - sensor_id=F80332010002C873_estado, value=1.0, timestamp_sensor=None, reading_timestamp=2025-01-15T18:40:00.002000+00:00
```

**⚠️ ATENÇÃO:**
- Se `timestamp_sensor=None`, o sistema está usando o `bt` (base time) do SenML
- Se `timestamp_sensor=<valor>`, o sensor tem timestamp próprio
- O timestamp final (`reading_timestamp`) é o que vai para o banco

## 3. Verificar Banco de Dados

### 3.1 Executar script de verificação
```powershell
cd "c:\Users\Rafael Ribeiro\TrakSense\traksense-backend"
docker exec -w /app traksense-api python check_timestamps_db.py
```

### 3.2 O que verificar:

**Timestamps devem estar:**
- Em UTC
- Com idade < 15 minutos (para ser avaliado pelas regras)
- Correspondendo ao horário que você publicou

**Exemplo de saída esperada:**
```
⏰ Horário atual (UTC): 2025-01-15T18:45:00+00:00

📡 Últimas 10 leituras do dispositivo F80332010002C873:
1. Sensor: F80332010002C873_temperatura_saida
   Valor: 8.5
   Timestamp (UTC): 2025-01-15T18:40:00+00:00
   Idade: 5.00 minutos
   ✅ FRESCO - Dentro da janela de 15 minutos
```

## 4. Análise de Problemas Comuns

### Problema 1: Timestamp muito antigo
**Sintoma:** Leituras com mais de 3 horas de idade
**Causas possíveis:**
- `bt` (base time) no SenML está errado
- Conversão de ms para segundos incorreta
- Timezone errado

**Como verificar:**
- Compare o `ts_original` do log com o horário atual
- Calcule: `ts_original / 1000 = Unix timestamp em segundos`
- Converta para data: https://www.epochconverter.com/

### Problema 2: Timestamp no futuro
**Sintoma:** Leituras com idade negativa
**Causas possíveis:**
- Relógio do sistema desajustado
- Timestamp em nanosegundos em vez de milissegundos

### Problema 3: Timestamp correto mas alertas não disparam
**Sintoma:** Leituras frescas mas sem alertas
**Causas possíveis:**
- Regras desabilitadas
- Condições não atendidas
- Celery não está rodando

**Como verificar:**
```powershell
# Ver se o Celery está processando
docker-compose logs -f celery

# Testar manualmente
docker exec -w /app traksense-api python -c "
from apps.alerts.tasks import evaluate_rules_task
result = evaluate_rules_task()
print(result)
"
```

## 5. Checklist de Validação

- [ ] API reiniciada com novos logs
- [ ] Logs mostram `⏰ TIMESTAMP RECEBIDO`
- [ ] Logs mostram `📊 READING CRIADO` para cada sensor
- [ ] Timestamp no log está correto (próximo da hora atual)
- [ ] `check_timestamps_db.py` mostra leituras frescas (< 15 min)
- [ ] Valores estão corretos (temperatura_saida=8.5, temperatura_retorno=25.0)
- [ ] Celery está rodando e processando tasks

## 6. Comparação de Timestamps

### Exemplo de análise:

**Mensagem MQTT (22:10:31):**
```
ts=1762909831004  // 1762909831004 ms = 1762909831 segundos
```

**Conversão esperada:**
```bash
# Em Python
datetime.fromtimestamp(1762909831)
# Resultado esperado: 2025-11-11 22:10:31 UTC
```

**No banco de dados deve aparecer:**
```
ts: 2025-11-11 22:10:31+00:00
```

**Se aparecer diferente:**
- 3 horas a menos: problema de timezone
- Anos de diferença: conversão ms/s errada
- Minutos de diferença: usando `bt` em vez de `ts`

## 7. Próximos Passos

Depois de validar os timestamps:

1. **Se timestamps estão corretos:**
   - Aguardar task do Celery (roda a cada minuto)
   - Verificar alertas criados

2. **Se timestamps estão errados:**
   - Compartilhar logs completos
   - Verificar fonte do problema (bt vs ts, conversão, timezone)

3. **Para testar manualmente:**
   ```powershell
   docker exec -w /app traksense-api python test_rule_chiller.py
   ```
