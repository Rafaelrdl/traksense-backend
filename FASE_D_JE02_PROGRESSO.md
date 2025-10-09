# 🚀 FASE D - JE02: Progresso de Implementação

## ✅ Status Atual: Templates Completos (2/10)

**Data**: 2025-10-08  
**Fase**: D — JE02: Templates + Adapter + Seeds + Simulador MQTT

---

## 📊 Progresso Geral

| # | Tarefa | Status | Tempo |
|---|--------|--------|-------|
| 1 | DeviceTemplate + PointTemplate | ✅ COMPLETO | ~15 min |
| 2 | DashboardTemplate | ✅ COMPLETO | ~20 min |
| 3 | Adapter JE02 - Implementação | 🔄 IN PROGRESS | - |
| 4 | Adapter JE02 - Integração | ⏳ TODO | - |
| 5 | Seeds - seed_demo_je02.py | ⏳ TODO | - |
| 6 | Simulador - sim_je02.py | ⏳ TODO | - |
| 7 | Testes Unit - Adapter | ⏳ TODO | - |
| 8 | Testes Integração | ⏳ TODO | - |
| 9 | Documentação | ⏳ TODO | - |
| 10 | Validação Final | ⏳ TODO | - |

**Progresso**: 20% (2/10 tarefas completas)

---

## ✅ 1. DeviceTemplate + PointTemplate (COMPLETO)

### Arquivo criado:
- `apps/templates/migrations/0003_je02_device_template.py`

### Conteúdo:
**DeviceTemplate**: `inverter_je02_v1`
- Code: `inverter_je02_v1`
- Name: "Inversor JE02 v1"
- Version: 1
- Description: Template para inversores JE02 (modelo IO2AI2RO1)
- is_global: True

**PointTemplates** (8 pontos):

| Nome | Tipo | Unidade | Descrição |
|------|------|---------|-----------|
| `status` | ENUM | - | RUN, STOP, FAULT |
| `fault` | BOOL | - | Indica falha ativa |
| `rssi` | NUM | dBm | Sinal WiFi (invertido) |
| `uptime` | NUM | s | Tempo de execução |
| `cntserr` | NUM | - | Contador de erros |
| `var0` | NUM | °C | Temperatura (÷10) |
| `var1` | NUM | % | Umidade (÷10) |
| `rele` | BOOL | - | Estado do relé |

### Aplicação:
```bash
docker compose exec api python manage.py migrate templates
✅ DeviceTemplate 'inverter_je02_v1' criado com 8 PointTemplates
```

---

## ✅ 2. DashboardTemplate (COMPLETO)

### Arquivo criado:
- `apps/templates/migrations/0004_je02_dashboard_template.py`

### Painéis implementados (8):

#### 1. **StatusPanel** (3x2)
- Exibe status atual: RUN (verde), STOP (laranja), FAULT (vermelho)
- Icons: play-circle, pause-circle, alert-triangle
- Refresh: 5s

#### 2. **KpiPanel - Falhas 24h** (3x2)
- Query: count de `fault=True` nas últimas 24h
- Thresholds: 0 (verde), 1+ (laranja), 10+ (vermelho)

#### 3. **KpiPanel - RSSI** (3x2)
- Query: último valor de `rssi` nos últimos 5min
- Thresholds: -85 (crítico), -75 (fraco), -65 (bom)
- Unit: dBm

#### 4. **ButtonPanel - Reset Falha** (3x2)
- Botão: "Reset Falha"
- Action: comando MQTT para ${topic_base}/cmd
- Payload: `{"RELE": 1, "pulse_ms": 500}`
- Tooltip: "Funcionalidade disponível na Fase 6"

#### 5. **TimelinePanel - Status 24h** (12x3)
- Timeline de mudanças de status nas últimas 24h
- Color map: RUN (verde), STOP (laranja), FAULT (vermelho)
- Labels + duração

#### 6. **TimeseriesPanel - Temperatura** (6x4)
- Série: var0 com agg=1m
- Y-axis: Temperatura (°C)
- Time range: 6h
- Color: vermelho

#### 7. **TimeseriesPanel - Umidade** (6x4)
- Série: var1 com agg=1m
- Y-axis: Umidade (%) 0-100
- Time range: 6h
- Color: azul

#### 8. **TimeseriesPanel - RSSI** (12x4)
- Série: rssi com agg=1m
- Y-axis: RSSI (dBm) -100 a -40
- Thresholds: -75 (fraco), -85 (crítico)
- Time range: 6h
- Color: roxo

### Schema:
- **Version**: v1
- **Layout**: Grid 12 columns, gap 16px
- **Total panels**: 8
- **Total rows**: 13

### Aplicação:
```bash
docker compose exec api python manage.py migrate templates
✅ DashboardTemplate criado para 'inverter_je02_v1' (8 painéis)
```

---

## 🔄 3. Adapter JE02 - Implementação (IN PROGRESS)

### Objetivo:
Implementar `ingest/adapters/je02_v1.py` que mapeia payloads JE02 para formato normalizado.

### Payloads esperados:

#### DATA:
```json
{
  "DATA": {
    "INPUT1": 1,      // 1=RUN, 0=STOP
    "INPUT2": 0,      // 1=FALHA, 0=OK
    "RELE": 0,        // estado do relé
    "WRSSI": -62,     // dBm
    "VAR0": 214,      // 21.4 (÷10)
    "VAR1": 503,      // 50.3 (÷10)
    "CNTSERR": 0,
    "UPTIME": 12345
  }
}
```

#### INFO:
```json
{
  "INFO": {
    "DEVNAME": "JE02-INV-01",
    "DEVIP": "192.168.0.25",
    "DEVMAC": "AA:BB:CC:DD:EE:FF",
    "DEVTYPE": "JE02",
    "DEVSUBTYPE": "IO2AI2RO1",
    "VERSION": "1.2.3"
  }
}
```

### Mapeamento (DATA):

| Payload | Point | Lógica |
|---------|-------|--------|
| INPUT2==1 → | `status` | "FAULT" (prioridade) |
| INPUT1==1 → | `status` | "RUN" |
| else → | `status` | "STOP" |
| INPUT2 | `fault` | boolean |
| WRSSI | `rssi` | valor direto (dBm) |
| VAR0 | `var0` | VAR0 / 10.0 |
| VAR1 | `var1` | VAR1 / 10.0 |
| RELE | `rele` | RELE != 0 |
| CNTSERR | `cntserr` | valor direto |
| UPTIME | `uptime` | valor direto |

### Mapeamento (INFO):
- Armazenar em `meta` ou `qual` (dependendo do modelo)
- Campos: devname, devip, devmac, devtype, devsubtype, version, src: "je02_v1"

### Próximos passos:
1. Verificar estrutura existente do ingest
2. Criar arquivo `ingest/adapters/je02_v1.py`
3. Implementar função `adapt_je02_data()` e `adapt_je02_info()`
4. Retornar tupla: `("data"|"info", points: list, meta: dict)`

---

## ⏳ Tarefas Pendentes

### 4. Adapter JE02 - Integração (TODO)
- Registrar adapter em `ingest/main.py`
- Detectar JE02 por chave "DATA" ou "INFO"
- Erro → `public.ingest_errors`

### 5. Seeds - seed_demo_je02.py (TODO)
- Criar tenant demo
- Criar site plant-01
- Criar 7 devices INV-01..INV-07
- Provisionar EMQX (auth + ACL)
- Instanciar DashboardConfig

### 6. Simulador - sim_je02.py (TODO)
- Publish DATA periódico
- INPUT1: 80% RUN, 20% STOP
- INPUT2: 2-5% FAULT (30-60s)
- WRSSI: -55 a -75
- VAR0/VAR1: aleatórios
- Escutar /cmd para RELE

### 7-8. Testes (TODO)
- Unit: adapter_je02_data, adapter_je02_info
- Integração: ingest, seeds, isolamento

### 9. Documentação (TODO)
- README Fase D
- Como rodar seeds
- Como rodar simulador
- Tópicos MQTT
- Troubleshooting

### 10. Validação Final (TODO)
- Executar seed_demo_je02
- Executar sim_je02.py
- Verificar dashboards
- Testar /data/points
- Validar isolamento

---

## 📁 Arquivos Criados

### Migrations:
1. `backend/apps/templates/migrations/0003_je02_device_template.py` ✅
2. `backend/apps/templates/migrations/0004_je02_dashboard_template.py` ✅

### Próximos arquivos:
3. `ingest/adapters/je02_v1.py` (próximo)
4. `ingest/adapters/__init__.py` (atualizar)
5. `ingest/main.py` (atualizar)
6. `backend/apps/devices/management/commands/seed_demo_je02.py`
7. `scripts/sim_je02.py`
8. `ingest/tests/test_adapter_je02_data.py`
9. `ingest/tests/test_adapter_je02_info.py`
10. `backend/apps/devices/tests/test_seeds_je02.py`
11. `backend/apps/timeseries/tests/test_isolation_views.py`
12. `FASE_D_JE02_README.md`

---

## 🎯 Próximo Passo

**Implementar Adapter JE02** (`ingest/adapters/je02_v1.py`)

---

**Autor**: TrakSense Team  
**Data**: 2025-10-08  
**Status**: 20% COMPLETO (2/10 tarefas)  
**Próximo**: Task 3 - Adapter JE02
