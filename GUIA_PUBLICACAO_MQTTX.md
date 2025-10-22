# 📡 Guia Rápido: Publicar Telemetria via MQTTX

## 🎯 Novo Formato de Tópico (Recomendado)

### Estrutura do Tópico:
```
tenants/{tenant}/sites/{site_name}/assets/{asset_tag}/telemetry
```

## 🔧 Configuração MQTTX

### Conexão:
- **Host**: localhost
- **Port**: 1883
- **Client ID**: traksense_client_001 (ou qualquer outro)
- **Clean Session**: true
- **Keepalive**: 60
- **Reconnect**: true

## 📝 Exemplos de Publicação

### Exemplo 1: CHILLER no Site "Uberlândia Medical Center"

**Topic**:
```
tenants/umc/sites/Uberlândia Medical Center/assets/CHILLER-001/telemetry
```

**Payload** (SenML):
```json
[
  {
    "bn": "4b686f6d70107115",
    "bt": 155259456
  },
  {
    "n": "model",
    "vs": "nit20l"
  },
  {
    "n": "rssi",
    "u": "dBW",
    "v": -61
  },
  {
    "n": "A",
    "u": "Cel",
    "v": 23.35
  },
  {
    "n": "A",
    "u": "%RH",
    "v": 64.0
  },
  {
    "n": "283286b20a000036",
    "u": "Cel",
    "v": 30.75
  },
  {
    "n": "gateway",
    "vs": "000D6FFFFE642E70"
  }
]
```

**Resultado Esperado**:
- ✅ Site "Uberlândia Medical Center" criado/encontrado
- ✅ Asset "CHILLER-001" criado (tipo: CHILLER)
- ✅ Device "4b686f6d70107115" vinculado
- ✅ 4 sensores criados (rssi, temperatura, umidade, sensor externo)

---

### Exemplo 2: AHU no Site "UMC - UTI Unidade Norte"

**Topic**:
```
tenants/umc/sites/UMC - UTI Unidade Norte/assets/AHU-001/telemetry
```

**Payload** (SenML):
```json
[
  {
    "bn": "5d797f8e20308216",
    "bt": 155260000
  },
  {
    "n": "model",
    "vs": "nit20l"
  },
  {
    "n": "rssi",
    "u": "dBW",
    "v": -55
  },
  {
    "n": "A",
    "u": "Cel",
    "v": 22.5
  },
  {
    "n": "A",
    "u": "%RH",
    "v": 58.0
  },
  {
    "n": "gateway",
    "vs": "000D6FFFFE642E70"
  }
]
```

**Resultado Esperado**:
- ✅ Site "UMC - UTI Unidade Norte" criado/encontrado
- ✅ Asset "AHU-001" criado (tipo: AHU)
- ✅ Device "5d797f8e20308216" vinculado
- ✅ 3 sensores criados

---

### Exemplo 3: VRF no Site "UMC - Laboratório"

**Topic**:
```
tenants/umc/sites/UMC - Laboratório de Análises Clínicas/assets/VRF-SPLIT-001/telemetry
```

**Payload** (SenML):
```json
[
  {
    "bn": "3a486b7d90412817",
    "bt": 155261000
  },
  {
    "n": "model",
    "vs": "nit20l"
  },
  {
    "n": "rssi",
    "u": "dBW",
    "v": -58
  },
  {
    "n": "B",
    "u": "Cel",
    "v": 24.8
  },
  {
    "n": "B",
    "u": "%RH",
    "v": 62.5
  },
  {
    "n": "gateway",
    "vs": "000D6FFFFE642E70"
  }
]
```

**Resultado Esperado**:
- ✅ Site "UMC - Laboratório de Análises Clínicas" criado/encontrado
- ✅ Asset "VRF-SPLIT-001" criado (tipo: VRF)
- ✅ Device "3a486b7d90412817" vinculado
- ✅ 3 sensores criados

---

## 🔄 Formato Legado (Sem Site)

Se não especificar o site, o sistema usa o primeiro site ativo:

**Topic**:
```
tenants/umc/assets/CHILLER-002/telemetry
```

**Comportamento**:
- Usa o primeiro site ativo do tenant UMC
- Funciona mas não recomendado para produção

---

## 🧪 Checklist de Teste

### 1. Teste Básico:
- [ ] Publicar mensagem no formato novo
- [ ] Verificar logs do backend (docker logs traksense-api --tail 50)
- [ ] Confirmar criação automática no Django Admin
- [ ] Verificar exibição no frontend

### 2. Teste Multi-Site:
- [ ] Publicar CHILLER-001 no site "Uberlândia Medical Center"
- [ ] Publicar AHU-001 no site "UMC - UTI Unidade Norte"
- [ ] Verificar que assets estão em sites diferentes
- [ ] Confirmar no frontend que cada site mostra seus assets

### 3. Teste de Movimentação:
- [ ] Publicar CHILLER-001 no site A
- [ ] Publicar CHILLER-001 no site B (mesmo asset, site diferente)
- [ ] Verificar logs mostrando movimentação
- [ ] Confirmar que asset agora está no site B

### 4. Teste de Sensores:
- [ ] Publicar mensagem com múltiplos sensores
- [ ] Verificar que todos os sensores foram criados
- [ ] Confirmar valores em last_value no Django Admin
- [ ] Verificar exibição no frontend

---

## 📊 Verificação de Resultados

### No Backend (Docker Logs):
```bash
docker logs traksense-api --tail 50 -f
```

**Logs esperados**:
```
✅ Extraído do tópico - Site: Uberlândia Medical Center, Asset: CHILLER-001
📍 Site encontrado: Uberlândia Medical Center
✅ Asset CHILLER-001 já existe no site Uberlândia Medical Center
✅ Asset CHILLER-001 processado no site Uberlândia Medical Center
✅ Telemetry saved: tenant=umc, device=4b686f6d70107115, topic=..., format=senml
📊 Created 4 sensor readings
```

### No Django Admin:
1. **Sites**: http://umc.localhost:8000/admin/tenants/tenant/
2. **Assets**: Clicar em "Sites" → Selecionar site → Ver assets
3. **Devices**: Ver devices vinculados ao asset
4. **Sensors**: Ver sensores com last_value atualizado

### No Frontend:
1. **URL**: http://umc.localhost:5173
2. **Header**: Selecionar site
3. **Página**: Ir para "Sensores & Telemetria"
4. **Verificar**: Sensores aparecem com valores atualizados

---

## 🐛 Troubleshooting

### Problema: Site não é criado
**Causa**: Nome do site com caracteres especiais não codificados
**Solução**: MQTTX codifica automaticamente, mas se usar outro cliente, use URL encoding

### Problema: Asset não aparece no frontend
**Causa**: Frontend está em outro site
**Solução**: Trocar de site no header do frontend

### Problema: Sensores aparecem mas sem valores
**Causa**: Device não foi vinculado ao asset
**Solução**: Verificar logs do backend, pode ter erro de permissão

### Problema: Erro 500 no ingest
**Causa**: Payload malformado ou tenant inválido
**Solução**: Verificar logs detalhados do backend

---

## 📝 Variações de Payload

### Apenas Temperatura:
```json
[
  {"bn": "4b686f6d70107115", "bt": 155259456},
  {"n": "model", "vs": "nit20l"},
  {"n": "A", "u": "Cel", "v": 23.35}
]
```

### Múltiplos Sensores Externos (DS18B20):
```json
[
  {"bn": "4b686f6d70107115", "bt": 155259456},
  {"n": "model", "vs": "nit20l"},
  {"n": "283286b20a000036", "u": "Cel", "v": 30.75},
  {"n": "283286b20a000037", "u": "Cel", "v": 28.50},
  {"n": "283286b20a000038", "u": "Cel", "v": 32.10}
]
```

### Com Porta Digital:
```json
[
  {"bn": "4b686f6d70107115", "bt": 155259456},
  {"n": "model", "vs": "nit20l"},
  {"n": "C1", "u": "count", "v": 150}
]
```

---

**Dica**: Salve esses payloads como "snippets" no MQTTX para reutilização rápida!

