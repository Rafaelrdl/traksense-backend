# 📘 Guia de Vinculação de Sensores a Ativos

## Visão Geral

Este documento descreve os 3 métodos disponíveis para vincular sensores aos ativos no TrakSense:

1. **Vinculação Automática via Tópico MQTT** (Recomendado para operação)
2. **Vinculação Manual via Django Admin** (Ideal para ajustes e correções)
3. **Provisionamento em Lote via Script CSV** (Ideal para instalações em massa)

---

## Método 1: Vinculação Automática via Tópico MQTT

### Como Funciona

Quando um sensor publica dados em um tópico MQTT que contém o código do ativo, o sistema automaticamente:
- Identifica o ativo pelo código no tópico
- Cria um Device (Gateway) padrão para o ativo, se necessário
- Vincula os sensores ao Device do ativo

### Padrões de Tópico Suportados

```
tenants/{tenant}/assets/{ASSET_TAG}/telemetry
```

**Exemplo:**
```
tenants/umc/assets/CH-001/telemetry
```

Neste caso, o sistema extrai `CH-001` como o código do ativo e vincula automaticamente todos os sensores do payload a esse ativo.

### Configuração do Sensor

Ao configurar o sensor no hardware, use o padrão de tópico acima:

```json
{
  "mqtt_broker": "mqtt.traksense.io",
  "topic": "tenants/umc/assets/CH-001/telemetry",
  "client_id": "GW-CH-001"
}
```

### Vantagens

✅ Zero configuração adicional no backend  
✅ Auto-correção: se o sensor for movido, basta mudar o tópico  
✅ Funciona durante a operação normal  
✅ Ideal para instalações padrão  

### Quando Usar

- Instalações novas onde o tópico pode ser configurado corretamente
- Quando há padrão de nomenclatura para os ativos
- Para operação contínua e auto-correção

---

## Método 2: Vinculação Manual via Django Admin

### Como Funciona

Interface visual no Django Admin para vincular múltiplos sensores a um ativo ou device de uma vez.

### Passo a Passo

#### Opção A: Vincular Sensores a um Ativo

1. **Acesse o Django Admin**
   ```
   https://api.traksense.io/admin/
   ```

2. **Navegue até Sensors**
   - Admin → Assets → Sensors

3. **Selecione os Sensores**
   - Marque as checkboxes dos sensores que deseja vincular
   - Exemplo: Selecione todos os sensores de um chiller

4. **Execute a Ação em Lote**
   - No dropdown "Ações", selecione: **"🔗 Vincular sensores selecionados a um Ativo"**
   - Clique em "Ir"

5. **Selecione o Ativo de Destino**
   - Na tela seguinte, escolha o ativo (ex: CH-001)
   - Opcionalmente, especifique o MQTT Client ID (se vazio, será gerado automaticamente)
   - Clique em "✅ Confirmar e Vincular"

6. **Confirmação**
   - O sistema criará um Device padrão se necessário
   - Todos os sensores serão vinculados ao ativo
   - Mensagem de sucesso será exibida

#### Opção B: Vincular Sensores a um Device Específico

1. Siga os passos 1-3 acima

2. **Execute a Ação em Lote**
   - No dropdown "Ações", selecione: **"🔧 Vincular sensores selecionados a um Device específico"**
   - Clique em "Ir"

3. **Selecione o Device de Destino**
   - Na tela seguinte, escolha o device específico
   - Clique em "✅ Confirmar e Vincular"

### Vantagens

✅ Interface visual intuitiva  
✅ Vinculação em lote (múltiplos sensores de uma vez)  
✅ Controle fino sobre qual device usar  
✅ Ideal para correções e casos especiais  

### Quando Usar

- Correções de vinculações incorretas
- Sensores já cadastrados que precisam ser re-vinculados
- Quando não é possível configurar o tópico MQTT corretamente
- Para controle fino sobre qual device usar

---

## Método 3: Provisionamento em Lote via Script CSV

### Como Funciona

Script Python que lê um arquivo CSV e cria/vincula múltiplos sensores de uma vez.

### Formato do CSV

Crie um arquivo CSV com as seguintes colunas:

```csv
sensor_tag,asset_tag,metric_type,unit,mqtt_client_id
CH-001-TEMP-SUPPLY,CH-001,temp_supply,°C,GW-CH-001
CH-001-TEMP-RETURN,CH-001,temp_return,°C,GW-CH-001
CH-001-POWER-KW,CH-001,power_kw,kW,GW-CH-001
AHU-001-TEMP-SUPPLY,AHU-001,temp_supply,°C,GW-AHU-001
AHU-001-HUMIDITY,AHU-001,humidity,%,GW-AHU-001
```

**Campos:**
- `sensor_tag`: Tag única do sensor (ex: CH-001-TEMP-SUPPLY)
- `asset_tag`: Tag do ativo existente (ex: CH-001)
- `metric_type`: Tipo de métrica (ver lista completa abaixo)
- `unit`: Unidade de medida (ex: °C, kW, Pa, %)
- `mqtt_client_id`: ID do dispositivo MQTT (opcional, será gerado se vazio)

### Tipos de Métricas Válidas

```
Temperatura:
- temp_supply, temp_return, temp_external, temp_setpoint

Umidade:
- humidity, dewpoint

Pressão:
- pressure_suction, pressure_discharge, dp_filter, dp_fan

Fluxo:
- airflow

Rotação:
- rpm_fan

Elétrico:
- voltage, current, power_kw, energy_kwh, power_factor

Refrigeração:
- superheat, subcooling

Vibração e Ruído:
- vibration, noise

Estados e Controle:
- compressor_state, valve_position

Eficiência:
- cop, eer

Manutenção:
- maintenance, maintenance_reminder
```

### Passo a Passo

1. **Prepare o Arquivo CSV**
   - Use o template `example_sensors.csv` como base
   - Preencha com os dados dos sensores a instalar

2. **Execute o Script (Simulação)**
   ```powershell
   python provision_sensors.py --tenant umc --file sensores_cliente.csv --dry-run
   ```
   
   Isso mostrará o que seria criado sem modificar o banco de dados.

3. **Execute o Script (Produção)**
   ```powershell
   python provision_sensors.py --tenant umc --file sensores_cliente.csv
   ```
   
   Isso criará os sensores e devices no banco de dados.

4. **Verifique o Resultado**
   - O script exibirá um resumo:
     - Total de linhas processadas
     - Sensores criados
     - Sensores atualizados
     - Devices criados
     - Erros encontrados

### Exemplo de Saída

```
============================================================
🚀 Iniciando provisionamento de sensores
Tenant: UMC Hospital
Arquivo: sensores_cliente.csv
Modo: PRODUÇÃO
============================================================

   ✨ Device criado: GW-CH-001
✅ Sensor criado: CH-001-TEMP-SUPPLY → CH-001 (temp_supply)
✅ Sensor criado: CH-001-TEMP-RETURN → CH-001 (temp_return)
✅ Sensor criado: CH-001-POWER-KW → CH-001 (power_kw)
   ✨ Device criado: GW-AHU-001
✅ Sensor criado: AHU-001-TEMP-SUPPLY → AHU-001 (temp_supply)
✅ Sensor criado: AHU-001-HUMIDITY → AHU-001 (humidity)

============================================================
📊 RESUMO DO PROVISIONAMENTO
============================================================
Total de linhas processadas: 5
Sensores criados: 5
Sensores atualizados: 0
Devices criados: 2
Erros: 0
============================================================
```

### Vantagens

✅ Provisionamento em massa  
✅ Documentação automática (CSV serve como registro)  
✅ Validação antes de criar (--dry-run)  
✅ Ideal para instalações padronizadas  
✅ Repetível e auditável  

### Quando Usar

- Setup inicial de novos clientes
- Instalações com muitos sensores (>10)
- Quando há um padrão de nomenclatura estabelecido
- Para documentar a instalação em arquivo

---

## Comparação dos Métodos

| Característica | Método 1: MQTT | Método 2: Admin | Método 3: CSV |
|----------------|----------------|-----------------|---------------|
| **Automação** | Alta | Baixa | Média |
| **Setup inicial** | Médio | Fácil | Médio |
| **Operação contínua** | Excelente | Manual | N/A |
| **Correções** | Auto | Fácil | Médio |
| **Instalação em massa** | - | Difícil | Excelente |
| **Documentação** | Baixa | Baixa | Alta |
| **Controle fino** | Baixo | Alto | Médio |

---

## Recomendação por Cenário

### 🏗️ Nova Instalação de Cliente

1. **Antes da visita**: Prepare CSV com sensores planejados
2. **Durante a instalação**: Configure sensores com tópico MQTT correto
3. **Após instalação**: Execute script CSV para garantir tudo criado
4. **Operação**: Vinculação automática via MQTT

### 🔧 Ajuste de Sensor Existente

1. Use Django Admin → Ação "Vincular a Ativo"
2. Selecione sensor(s) e ativo de destino
3. Confirme

### 🚨 Correção de Erro

1. Se sensor está no ativo errado:
   - Opção A: Mude o tópico MQTT (auto-correção na próxima publicação)
   - Opção B: Use Django Admin para re-vincular manualmente

### 📦 Migração em Massa

1. Exporte sensores atuais para CSV (se necessário)
2. Ajuste CSV conforme necessário
3. Execute script com `--dry-run` para validar
4. Execute script em produção

---

## Troubleshooting

### Sensor não está vinculando automaticamente via MQTT

**Sintomas**: Dados chegam mas sensor não aparece no ativo correto.

**Causas possíveis**:
1. Tópico MQTT não segue o padrão esperado
2. Asset tag no tópico não existe no banco
3. Sensor não foi criado previamente no admin

**Solução**:
1. Verifique o tópico: `tenants/{tenant}/assets/{ASSET_TAG}/telemetry`
2. Verifique se o ativo existe: Admin → Assets → buscar pelo tag
3. Verifique os logs do backend:
   ```
   🔗 Asset tag extraído do tópico: CH-001
   🎯 Asset encontrado: CH-001 - Chiller Principal
   ✨ Device criado automaticamente: Gateway CH-001
   ```

### Script CSV retorna erro "Asset não encontrado"

**Sintomas**: `❌ Linha X: Asset 'CH-001' não encontrado`

**Causa**: O ativo precisa existir antes de vincular sensores.

**Solução**:
1. Crie o ativo primeiro no Django Admin
2. Ou ajuste o CSV para usar tags de ativos existentes

### Sensor criado mas não recebe dados

**Sintomas**: Sensor aparece no admin mas `last_value` sempre null.

**Causas possíveis**:
1. `sensor_id` no payload MQTT não corresponde ao `tag` do sensor
2. Tópico MQTT incorreto

**Solução**:
1. Verifique o payload MQTT:
   ```json
   {
     "sensors": [
       {"sensor_id": "CH-001-TEMP-SUPPLY", "value": 23.5}
     ]
   }
   ```
2. `sensor_id` deve ser exatamente igual ao `tag` do sensor no banco

---

## Suporte

Para dúvidas ou problemas:
- Consulte os logs do backend: `docker logs traksense-api`
- Verifique o Django Admin: `https://api.traksense.io/admin/`
- Entre em contato com a equipe de desenvolvimento

---

**Última atualização**: 20 de outubro de 2025
