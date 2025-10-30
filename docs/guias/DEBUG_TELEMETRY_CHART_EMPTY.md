# 🐛 DEBUG: Telemetria Asset Details - Sem Dados no Gráfico

## 🔍 Problema

Na aba "Telemetria" da página de detalhes do CHILLER-001, os checkboxes aparecem corretamente (Temp. Insuflamento, Umidade, RSSI), mas quando selecionados, o gráfico exibe "Sem dados disponíveis" mesmo havendo publicações MQTT nas últimas 24 horas.

---

## 🧪 Passos de Debug

### 1️⃣ Abrir DevTools e Console

1. Abra o frontend: `http://umc.localhost:5173`
2. Pressione **F12** para abrir DevTools
3. Vá para aba **Console**
4. Limpe o console (ícone 🚫)

### 2️⃣ Navegar para Detalhes do Ativo

1. Ir para página "Ativos"
2. Clicar em "Detalhes" do CHILLER-001
3. Ir para aba "Telemetria"

**Logs esperados:**
```
🔍 Buscando sensores para o ativo CHILLER-001 (ID: 6)
✅ 4 sensores carregados, 3 tipos de métricas disponíveis
```

### 3️⃣ Selecionar Métrica

1. Marcar checkbox "Temp. Insuflamento (°C)"

**Logs esperados:**
```
📊 Buscando telemetria para métricas: temp_supply
🔍 Buscando dados de 1 device(s): ["4b686f6d70107115"]
  📡 Chamando API para device: 4b686f6d70107115
  ✅ Device 4b686f6d70107115 retornou: { deviceId: "...", period: {...}, series: [...] }
📊 Total de séries agregadas: X
📊 Estrutura dos dados: [...]
  🔍 Série XXX: tipo="temp_supply", selecionado=true
✅ X série(s) de telemetria carregadas
```

### 4️⃣ Verificar Network (Rede)

1. Ir para aba **Network** no DevTools
2. Filtrar por: `history`
3. Selecionar novamente a métrica

**Request esperado:**
```
GET /telemetry/history/4b686f6d70107115/?start=2025-10-21T...&end=2025-10-22T...
```

**Response esperado (200 OK):**
```json
{
  "deviceId": "4b686f6d70107115",
  "period": {
    "start": "2025-10-21T...",
    "end": "2025-10-22T..."
  },
  "aggregation": "5m",
  "series": [
    {
      "sensorId": "283286b20a000036",
      "sensorName": "283286b20a000036",
      "sensorType": "temp_supply",
      "unit": "celsius",
      "data": [
        {
          "timestamp": "2025-10-22T20:00:00Z",
          "avg": 32.75,
          "min": 32.5,
          "max": 33.0,
          "count": 5
        },
        // ... mais pontos
      ]
    }
  ]
}
```

---

## 🔎 Diagnósticos Possíveis

### ❌ Cenário 1: API Retorna 404

**Sintoma:**
```
❌ Erro ao buscar dados do device 4b686f6d70107115: Error 404
```

**Causa:** Endpoint não existe ou device ID incorreto

**Solução:**
```bash
# Verificar se endpoint existe
cd "c:\Users\Rafael Ribeiro\TrakSense\traksense-backend"
docker exec traksense-api python manage.py show_urls | grep telemetry
```

### ❌ Cenário 2: API Retorna 200 mas `series` vazio

**Sintoma:**
```
✅ Device 4b686f6d70107115 retornou: { series: [] }
📊 Total de séries agregadas: 0
```

**Causa:** Não há dados no banco ou filtro de período incorreto

**Solução: Verificar dados no banco**
```python
# Script: test_telemetry_history.py
from django_tenants.utils import schema_context
from apps.telemetry.models import TelemetryReading
from datetime import datetime, timedelta
from django.utils import timezone

with schema_context('umc'):
    device_id = '4b686f6d70107115'
    
    # Últimas 24 horas
    start = timezone.now() - timedelta(hours=24)
    
    readings = TelemetryReading.objects.filter(
        device_id=device_id,
        timestamp__gte=start
    ).order_by('-timestamp')[:10]
    
    print(f"📊 Últimas leituras do device {device_id}:")
    for r in readings:
        print(f"  🕐 {r.timestamp}")
        print(f"     Sensor: {r.sensor_id}")
        print(f"     Valor: {r.value}")
        print(f"     Labels: {r.labels}")
```

**Executar:**
```bash
cd "c:\Users\Rafael Ribeiro\TrakSense\traksense-backend"
docker exec traksense-api python test_telemetry_history.py
```

### ❌ Cenário 3: Dados existem mas não são filtrados

**Sintoma:**
```
📊 Total de séries agregadas: 3
🔍 Série 283286b20a000036: tipo="", selecionado=false
🔍 Série 4b686f6d70107115_A_humid: tipo="", selecionado=false
🔍 Série 4b686f6d70107115_rssi: tipo="", selecionado=false
```

**Causa:** Campo `sensorType` ou `metricType` está vazio na resposta

**Solução:** Verificar estrutura da resposta no console:
```javascript
// Copiar do console o objeto completo da resposta
console.log(JSON.stringify(data, null, 2));
```

### ❌ Cenário 4: Formato de dados incompatível

**Sintoma:**
```
✅ 3 série(s) de telemetria carregadas
[Gráfico ainda vazio]
```

**Causa:** Formato dos dados não corresponde ao esperado por `LineChartTemp`

**Verificação:**
```javascript
// No console do navegador, após selecionar métrica:
console.log('Supply data:', telemetryChartData);
```

**Formato esperado:**
```javascript
{
  supply: [
    { timestamp: Date, value: 32.75 },
    { timestamp: Date, value: 32.80 },
    // ...
  ],
  return: [...],
  setpoint: [...]
}
```

---

## 🛠️ Soluções por Cenário

### Solução 1: Verificar Endpoint Backend

```bash
# Testar diretamente no terminal
curl -H "Host: umc.localhost" http://localhost:8000/api/telemetry/history/4b686f6d70107115/?start=2025-10-21T00:00:00Z&end=2025-10-22T23:59:59Z
```

### Solução 2: Publicar Novo Dado MQTT

Use MQTTX para publicar nova mensagem:

**Topic:**
```
tenants/umc/sites/Uberlândia Medical Center/assets/CHILLER-001/telemetry
```

**Payload:**
```json
[
  {
    "bn": "urn:dev:mac:4b686f6d70107115:",
    "bt": 1729635720,
    "bu": "celsius",
    "n": "A_temp",
    "v": 25.5,
    "t": 0
  },
  {
    "n": "A_humid",
    "u": "percent_rh",
    "v": 60.0,
    "t": 0
  }
]
```

Aguarde 5 segundos e selecione a métrica novamente.

### Solução 3: Mapear Campo Correto

Se `sensorType` estiver vazio, precisamos usar outro campo. Verifique a resposta:

```javascript
// Console do navegador
const response = await fetch('/telemetry/history/4b686f6d70107115/?start=...&end=...');
const data = await response.json();
console.log('Estrutura da série:', data.series[0]);
```

**Possíveis campos:**
- `sensorType`
- `metricType`
- `sensor_type`
- `metric_type`
- `labels.metric_type`

---

## 📊 Script de Teste Completo

```python
# test_telemetry_api_endpoint.py
import requests
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"
DEVICE_ID = "4b686f6d70107115"

# Calcular período (últimas 24h)
end = datetime.now()
start = end - timedelta(hours=24)

# Montar URL
url = f"{BASE_URL}/api/telemetry/history/{DEVICE_ID}/"
params = {
    'start': start.isoformat(),
    'end': end.isoformat()
}

headers = {
    'Host': 'umc.localhost'
}

print(f"🔍 Testando endpoint: {url}")
print(f"📅 Período: {start} até {end}")

try:
    response = requests.get(url, params=params, headers=headers)
    print(f"\n✅ Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"📊 Device ID: {data.get('deviceId')}")
        print(f"📊 Agregação: {data.get('aggregation')}")
        print(f"📊 Número de séries: {len(data.get('series', []))}")
        
        for i, series in enumerate(data.get('series', [])):
            print(f"\n  Série {i+1}:")
            print(f"    Sensor ID: {series.get('sensorId')}")
            print(f"    Sensor Type: {series.get('sensorType')}")
            print(f"    Metric Type: {series.get('metricType')}")
            print(f"    Unit: {series.get('unit')}")
            print(f"    Pontos: {len(series.get('data', []))}")
            
            if len(series.get('data', [])) > 0:
                first_point = series['data'][0]
                last_point = series['data'][-1]
                print(f"    Primeiro ponto: {first_point}")
                print(f"    Último ponto: {last_point}")
    else:
        print(f"❌ Erro: {response.text}")
        
except Exception as e:
    print(f"❌ Exceção: {e}")
```

**Executar:**
```bash
cd "c:\Users\Rafael Ribeiro\TrakSense\traksense-backend"
docker exec traksense-api python test_telemetry_api_endpoint.py
```

---

## ✅ Checklist de Validação

- [ ] Console mostra logs de busca de sensores
- [ ] Console mostra logs de busca de telemetria
- [ ] Network mostra request para `/telemetry/history/...`
- [ ] Request retorna 200 OK
- [ ] Response contém `series` com dados
- [ ] Cada série tem `sensorType` ou `metricType` preenchido
- [ ] Cada série tem array `data` com pontos
- [ ] Cada ponto tem `timestamp` e `avg` (ou `value`)
- [ ] Console mostra "X série(s) de telemetria carregadas"
- [ ] Gráfico renderiza com linhas visíveis

---

## 🎯 Próximos Passos

1. **Abrir DevTools** e seguir os passos acima
2. **Copiar logs do console** completos
3. **Copiar resposta da API** da aba Network
4. **Compartilhar aqui** para análise

Com essas informações, conseguirei identificar exatamente onde está o problema! 🚀
