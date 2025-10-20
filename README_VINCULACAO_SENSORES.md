# 🎉 Vinculação de Sensores a Ativos - Implementação Completa

## ✅ O que foi implementado

### 1. 🤖 Vinculação Automática via Tópico MQTT (Opção 2)

**Localização**: `apps/ingest/views.py`

- ✅ Método `_extract_asset_tag_from_topic()` para extrair código do ativo do tópico MQTT
- ✅ Método `_auto_link_sensors_to_asset()` para vinculação automática
- ✅ Integração no fluxo de ingestão de telemetria
- ✅ Criação automática de Device (Gateway) quando necessário
- ✅ Logs detalhados para troubleshooting

**Como usar**:
Configure o sensor para publicar em: `tenants/umc/assets/{ASSET_TAG}/telemetry`

### 2. 🖥️ Interface Admin Melhorada (Opção 3)

**Localização**: `apps/assets/admin.py`

- ✅ Ação em lote: "🔗 Vincular sensores selecionados a um Ativo"
- ✅ Ação em lote: "🔧 Vincular sensores selecionados a um Device específico"
- ✅ Templates HTML customizados com interface visual
- ✅ Criação automática de Device quando necessário
- ✅ Mensagens de sucesso/erro detalhadas

**Como usar**:
1. Admin → Assets → Sensors
2. Selecione múltiplos sensores
3. Ações → "Vincular sensores..."
4. Escolha ativo/device → Confirme

### 3. 📦 Script de Provisionamento em Lote (Bônus)

**Localização**: `provision_sensors.py`

- ✅ Leitura de arquivo CSV
- ✅ Validação de campos e metric_types
- ✅ Modo dry-run para simulação
- ✅ Estatísticas detalhadas de execução
- ✅ Criação/atualização em lote

**Como usar**:
```powershell
python provision_sensors.py --tenant umc --file sensores.csv --dry-run
python provision_sensors.py --tenant umc --file sensores.csv
```

---

## 📁 Arquivos Criados/Modificados

### Código Backend
- ✏️ `apps/ingest/views.py` (modificado)
- ✏️ `apps/assets/admin.py` (modificado)
- ✨ `provision_sensors.py` (novo)

### Templates
- ✨ `apps/assets/templates/admin/sensors/bulk_assign_asset.html` (novo)
- ✨ `apps/assets/templates/admin/sensors/bulk_assign_device.html` (novo)

### Documentação
- ✨ `GUIA_VINCULACAO_SENSORES.md` (novo) - Guia completo para equipe técnica
- ✨ `IMPLEMENTACAO_VINCULACAO_SENSORES.md` (novo) - Documentação técnica
- ✨ `example_sensors.csv` (novo) - Template de CSV

---

## 🚀 Como Testar

### Teste 1: Vinculação Automática via MQTT

```bash
# Publicar telemetria com tópico contendo o asset_tag
curl -X POST http://localhost:8000/api/v1/ingest/ \
  -H "x-tenant: umc" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "tenants/umc/assets/CH-001/telemetry",
    "ts": 1697572800000,
    "payload": {
      "device_id": "GW-CH-001",
      "sensors": [
        {"sensor_id": "CH-001-TEMP-SUPPLY", "value": 23.5}
      ]
    }
  }'

# Verificar logs
docker logs traksense-api | grep "🔗"
```

### Teste 2: Interface Admin

1. Acesse: `http://localhost:8000/admin/`
2. Navegue: Assets → Sensors
3. Selecione alguns sensores
4. Ações → "🔗 Vincular sensores selecionados a um Ativo"
5. Escolha o ativo → Confirme
6. Verifique mensagem de sucesso

### Teste 3: Script CSV

```powershell
# Criar arquivo de teste
echo "sensor_tag,asset_tag,metric_type,unit
TEST-001-TEMP,CH-001,temp_supply,°C
TEST-002-POWER,CH-001,power_kw,kW" > teste.csv

# Simulação
python provision_sensors.py --tenant umc --file teste.csv --dry-run

# Produção
python provision_sensors.py --tenant umc --file teste.csv
```

---

## 📊 Vantagens da Implementação

| Método | Velocidade | Automação | Controle | Uso Ideal |
|--------|-----------|-----------|----------|-----------|
| **MQTT** | ⚡ Instantâneo | 🤖 Total | 📊 Médio | Operação contínua |
| **Admin** | 👆 Manual | 🖐️ Baixa | 🎯 Total | Correções/ajustes |
| **CSV** | 📦 Em lote | 🔄 Alta | 📋 Médio | Setup inicial |

---

## 🎯 Fluxo de Trabalho Recomendado

### Para Nova Instalação:
1. **Pré-instalação**: Preparar CSV com sensores planejados
2. **Instalação**: Configurar sensores com tópico MQTT correto
3. **Pós-instalação**: Executar script CSV para garantir tudo criado
4. **Operação**: Vinculação automática via MQTT funciona

### Para Correções:
1. Acessar Django Admin
2. Selecionar sensores problemáticos
3. Usar ação "Vincular ao Ativo"
4. Confirmar

---

## 📖 Documentação Completa

- **Guia do Técnico**: `GUIA_VINCULACAO_SENSORES.md`
  - Passo a passo de cada método
  - Troubleshooting
  - Exemplos práticos

- **Documentação Técnica**: `IMPLEMENTACAO_VINCULACAO_SENSORES.md`
  - Decisões de design
  - Fluxo de dados
  - Arquitetura

---

## 🎓 Tipos de Métricas Suportadas

```python
# Temperatura
temp_supply, temp_return, temp_external, temp_setpoint

# Umidade
humidity, dewpoint

# Pressão
pressure_suction, pressure_discharge, dp_filter, dp_fan

# Elétrico
voltage, current, power_kw, energy_kwh, power_factor

# E mais 20+ tipos...
```

Ver lista completa em `GUIA_VINCULACAO_SENSORES.md`

---

## ⚠️ Requisitos

- Django 4.2+
- Python 3.10+
- django-tenants
- PostgreSQL com schemas

---

## 🐛 Troubleshooting

### Sensor não vincula automaticamente

**Verifique**:
1. Tópico segue padrão: `tenants/{tenant}/assets/{ASSET_TAG}/telemetry`
2. Asset existe no banco com tag exato
3. Logs do backend: `docker logs traksense-api | grep "🔗"`

### Script CSV retorna erro

**Verifique**:
1. Asset existe antes de executar script
2. metric_type é válido (ver lista em GUIA)
3. CSV está em UTF-8
4. Use `--dry-run` primeiro para validar

---

## 📞 Suporte

Consulte a documentação completa ou entre em contato com a equipe de desenvolvimento.

---

**Status**: ✅ Implementação Completa  
**Data**: 20 de outubro de 2025  
**Desenvolvido por**: GitHub Copilot
