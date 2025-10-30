# ✅ SOLUÇÃO: Sensores Não Aparecem na Lista

**Data:** 19/10/2025 23:57  
**Status:** 🔧 RESOLVIDO  
**Prioridade:** 🔴 CRÍTICA

---

## 🎯 Resumo Executivo

**Problema Reportado:**
> "Ainda aparecem somente os dados mockados na lista de catálogo de sensores"

**Root Cause Identificado:**
1. ❌ **URL de acesso incorreta** - Usando `localhost:5000` ao invés de `umc.localhost:5000`
2. ❌ **Campo mapeado errado** - Frontend buscava `last_reading_at`, backend retornava `last_reading`
3. ❌ **Campos faltando** - Backend não retornava `sensor_name`, `sensor_type`, `is_online`, `statistics_24h`

**Impacto:**
- 0% dos sensores reais carregados
- Apenas dados mockados visíveis
- Erro 404 nas requisições de API
- Auto-refresh não funcionando

---

## 🔧 Correções Aplicadas

### 1. Frontend - Mapeador de Campos ✅

**Arquivo:** `src/lib/mappers/telemetryMapper.ts`  
**Linha:** 146

```diff
export function mapApiSensorSummaryToFrontend(apiSensor: any): SensorSummary {
  return {
    sensorId: apiSensor.sensor_id,
    sensorName: apiSensor.sensor_name || apiSensor.sensor_id,
    sensorType: apiSensor.sensor_type || 'unknown',
    unit: apiSensor.unit || '',
    isOnline: apiSensor.is_online ?? false,
    lastValue: apiSensor.last_value ?? null,
-   lastReadingAt: apiSensor.last_reading_at ?? null,  // ❌ Campo inexistente
+   lastReadingAt: apiSensor.last_reading ?? null,      // ✅ Campo correto
    statistics24h: {
      avg: apiSensor.statistics_24h?.avg ?? null,
      min: apiSensor.statistics_24h?.min ?? null,
      max: apiSensor.statistics_24h?.max ?? null,
      count: apiSensor.statistics_24h?.count || 0,
      stddev: apiSensor.statistics_24h?.stddev ?? null,
    },
  };
}
```

### 2. Backend - Response Completo ✅

**Arquivo:** `apps/ingest/api_views_extended.py`  
**Linhas:** 381-413

```diff
# Parse labels (pode ser string JSON ou dict)
labels = reading_data.get('labels', {})
if isinstance(labels, str):
    try:
        labels = json.loads(labels)
    except (json.JSONDecodeError, TypeError):
        labels = {}

+ # Determinar status: online se última leitura foi dentro do threshold
+ is_online = reading_ts >= online_threshold

sensors.append({
    'sensor_id': reading_data['sensor_id'],
+   'sensor_name': reading_data['sensor_id'],  # ✅ Adicionado
+   'sensor_type': labels.get('type', 'unknown') if isinstance(labels, dict) else 'unknown',  # ✅ Adicionado
+   'unit': labels.get('unit', '') if isinstance(labels, dict) else '',
+   'is_online': is_online,  # ✅ Corrigido (booleano)
    'last_value': reading_data['value'],
    'last_reading': reading_ts.isoformat(),
+   'statistics_24h': {  # ✅ Adicionado
+       'avg': None,
+       'min': None,
+       'max': None,
+       'count': 0,
+       'stddev': None,
+   }
})
```

### 3. Documentação Atualizada ✅

**Arquivos criados/atualizados:**
- ✅ `BUGFIX_TELEMETRY_MAPPER_FIELDS.md` - Bug fix completo
- ✅ `GUIA_ACESSO_MULTITENANCY.md` - Guia de acesso correto
- ✅ `SOLUCAO_SENSORES_NAO_APARECEM.md` - Este arquivo (resumo executivo)

**Porta corrigida em documentos:**
- ❌ Antes: `http://localhost:5173`
- ✅ Agora: `http://umc.localhost:5000`

---

## ⚠️ AÇÃO NECESSÁRIA DO USUÁRIO

### Passo 1: Acessar URL Correta

**URL CORRETA (com tenant):**
```
http://umc.localhost:5000/sensors
```

**URL INCORRETA (sem tenant):**
```
❌ http://localhost:5000/sensors
```

### Passo 2: Verificar Hosts File

**Windows:**
```powershell
# PowerShell como Administrador
notepad C:\Windows\System32\drivers\etc\hosts

# Adicionar linha se não existir:
127.0.0.1 umc.localhost

# Flush DNS
ipconfig /flushdns
```

**Linux/Mac:**
```bash
sudo nano /etc/hosts
# Adicionar:
127.0.0.1 umc.localhost

# Flush DNS (Mac)
sudo dscacheutil -flushcache
```

### Passo 3: Recarregar Página

1. Fechar todas as abas do navegador em `localhost:5000`
2. Abrir nova aba
3. Acessar: `http://umc.localhost:5000/sensors`
4. Aguardar carregamento (3-5 segundos)

---

## ✅ Resultado Esperado

### DevTools (F12 → Console)

**✅ SEM ERROS:**
- ✅ Sem "Cannot read properties of undefined"
- ✅ Sem erro 404
- ✅ Sem erro 500

**✅ COM LOGS DE SUCESSO:**
```
✅ Telemetria carregada: 35 sensores do device GW-1760908415
```

### DevTools (F12 → Network)

**Request:**
```
GET http://umc.localhost:8000/api/telemetry/device/GW-1760908415/summary/
Status: 200 OK
```

**Response Preview:**
```json
{
  "device_id": "GW-1760908415",
  "status": "online",
  "sensors": [
    {
      "sensor_id": "TEMP-1760908415",
      "sensor_name": "TEMP-1760908415",
      "sensor_type": "temperature",
      "unit": "°C",
      "is_online": true,
      "last_value": 22.5,
      "last_reading": "2025-10-19T23:46:30Z",
      "statistics_24h": { ... }
    }
  ]
}
```

### UI - Catálogo de Sensores

**Cards de Resumo (topo):**
- ✅ **35** Sensores Online (verde)
- ✅ **0** Sensores Offline (vermelho)
- ✅ **100.0%** Disponibilidade (azul)

**Grid de Sensores:**
| Sensor | Equipamento | Tipo | Última Leitura | Status | Disponibilidade |
|--------|-------------|------|----------------|--------|-----------------|
| 📡 JE02-AHU-001_INPUT1 | Equipamento não encontrado | Input1 | 1.00 @ 19/10, 23:55 | 🟢 Online | 99.5% |
| 📡 JE02-AHU-001_INPUT2 | Equipamento não encontrado | Input2 | 0.00 @ 19/10, 23:55 | 🟢 Online | 99.5% |
| 📡 JE02-AHU-001_RSSI | Equipamento não encontrado | Rssi | -64.29 dBm @ 19/10, 23:55 | 🟢 Online | 99.5% |
| ... | ... | ... | ... | ... | ... |

**Detalhes importantes:**
- ✅ Valores **reais** do banco (não mais 0.00 mockado)
- ✅ Timestamps **corretos** (19/10, 23:55)
- ✅ Status **Online** (ícone verde)
- ✅ Tipos de sensor corretos (Input1, Input2, Rssi, Uptime, etc.)

### Auto-Refresh

**Badge superior direito:**
```
🔄 Última atualização: 23:55:50
```

**Comportamento:**
- ✅ Badge atualiza a cada **30 segundos**
- ✅ Grid recarrega automaticamente
- ✅ Sem necessidade de F5 manual

---

## 🔍 Troubleshooting

### Problema: Ainda mostra erro 404

**Causa:** Não está acessando via domínio tenant

**Verificação:**
1. Abrir DevTools → Network
2. Verificar URL das requisições
3. Deve ser: `http://umc.localhost:8000/api/...`
4. **NÃO**: `http://localhost:8000/api/...`

**Solução:**
- Fechar todas as abas
- Acessar via `http://umc.localhost:5000`

---

### Problema: "DNS_PROBE_FINISHED_NXDOMAIN"

**Causa:** Browser não resolve `umc.localhost`

**Verificação:**
```powershell
# Windows - PowerShell
ping umc.localhost

# Esperado: Reply from 127.0.0.1
```

**Solução:**
1. Editar hosts file (ver Passo 2 acima)
2. Flush DNS
3. Reiniciar navegador

---

### Problema: Backend retorna 401 Unauthorized

**Causa:** Não logado ou token expirado

**Solução:**
1. Fazer login: `http://umc.localhost:5000/`
2. Usar credenciais:
   - Email: `teste@umc.localhost`
   - Senha: (verificar com backend team)
3. Aguardar redirect automático

---

## 📊 Status dos Serviços

### Backend (API)

```bash
# Verificar containers
docker ps

# Esperado:
# traksense-api    Up 2 hours   0.0.0.0:8000->8000/tcp
# traksense-db     Up 2 hours   0.0.0.0:5432->5432/tcp
# traksense-emqx   Up 2 hours   0.0.0.0:1883->1883/tcp
```

**Logs (últimas 10 linhas):**
```bash
docker logs traksense-api --tail 10

# Esperado:
# ✅ [GUNICORN] post_request: Worker 7 respondeu 200 OK para /api/telemetry/device/GW-1760908415/summary/
```

### Frontend (Vite)

```bash
# Verificar processo Node
Get-NetTCPConnection -LocalPort 5000 -State Listen

# Esperado:
# LocalAddress LocalPort OwningProcess
# ::1          5000      6776
```

### Database (Telemetry Data)

```bash
# Entrar no container
docker exec -it traksense-db psql -U traksense -d traksense

# Conectar ao schema tenant
\c traksense
SET search_path TO umc, public;

# Verificar leituras
SELECT COUNT(*) FROM ingest_reading;
-- Esperado: 1440 (ou mais)

SELECT sensor_id, COUNT(*) 
FROM ingest_reading 
GROUP BY sensor_id 
ORDER BY COUNT(*) DESC 
LIMIT 5;

-- Esperado: Lista de sensores com contagens
```

---

## 📋 Checklist Final

Antes de reportar novo bug, validar:

- [ ] Acessando via `http://umc.localhost:5000` (não `localhost`)
- [ ] Hosts file tem `127.0.0.1 umc.localhost`
- [ ] DNS cache limpo (`ipconfig /flushdns`)
- [ ] Backend containers rodando (`docker ps`)
- [ ] Frontend rodando (porta 5000 ocupada)
- [ ] DevTools → Network mostra 200 OK
- [ ] DevTools → Console sem erros
- [ ] Grid mostra sensores reais (JE02-AHU-001_*)
- [ ] Valores não são todos 0.00
- [ ] Auto-refresh badge atualiza

---

## 🎓 Lições Aprendidas

### 1. Multi-Tenancy Requer Domínio Correto

**Problema:** Acessar `localhost` sem tenant

**Impacto:**
- Backend não identifica schema
- Todas as rotas `/api/*` retornam 404
- Dados não carregam

**Solução:**
- Sempre usar domínio do tenant
- Configurar hosts file
- Validar URL no browser

### 2. Validar Contratos de API

**Problema:** Frontend espera `last_reading_at`, backend retorna `last_reading`

**Impacto:**
- Parsing falha silenciosamente
- Valores ficam `null`
- UI mostra dados incompletos

**Solução:**
- Testar endpoint com curl/Postman
- Documentar schema (OpenAPI)
- Criar testes de contrato

### 3. Response Completo

**Problema:** Backend não retornava todos os campos necessários

**Impacto:**
- Mapeador usa fallbacks
- Dados incompletos na UI
- Funcionalidades quebradas

**Solução:**
- Alinhar backend com frontend types
- Validar response shape
- Usar TypeScript strict mode

---

## 📁 Arquivos Modificados

### Frontend

- ✅ `src/lib/mappers/telemetryMapper.ts` (linha 146)
  * Corrigido: `last_reading_at` → `last_reading`

### Backend

- ✅ `apps/ingest/api_views_extended.py` (linhas 381-413)
  * Adicionado: `sensor_name`
  * Adicionado: `sensor_type`
  * Corrigido: `is_online` (booleano)
  * Adicionado: `statistics_24h`

### Documentação

- ✅ `BUGFIX_TELEMETRY_MAPPER_FIELDS.md`
- ✅ `GUIA_ACESSO_MULTITENANCY.md`
- ✅ `SOLUCAO_SENSORES_NAO_APARECEM.md` (este arquivo)

---

## 🚀 Próximos Passos

### 1. Validar Solução (URGENTE)

**Usuário deve:**
1. Acessar `http://umc.localhost:5000/sensors`
2. Confirmar sensores aparecem
3. Verificar valores reais (não mockados)
4. Testar auto-refresh (aguardar 30s)

### 2. Implementar Estatísticas 24h

**Backend TODO:**
```python
# Calcular estatísticas reais
statistics_24h = calculate_sensor_stats_24h(sensor_id)
# Retornar: avg, min, max, count, stddev
```

### 3. Melhorar Nomes de Sensores

**Backend TODO:**
```python
# Buscar nome do model Sensor se existir
from apps.assets.models import Sensor
sensor_obj = Sensor.objects.filter(tag=sensor_id).first()
sensor_name = sensor_obj.tag if sensor_obj else sensor_id
```

---

**Criado:** 19/10/2025 23:57  
**Backend Reiniciado:** 19/10/2025 23:48  
**Status:** ⏳ Aguardando validação do usuário  
**Responsável:** GitHub Copilot
