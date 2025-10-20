# Sistema de Parsers de Payload TrakSense

## 📋 Visão Geral

O TrakSense implementa um sistema plugável de parsers que permite processar diferentes formatos de payload MQTT de diversos fabricantes e modelos de dispositivos IoT. Esta arquitetura garante flexibilidade para suportar novos formatos sem modificar o código principal da aplicação.

## 🏗️ Arquitetura

```
┌─────────────────┐
│  Dispositivo    │
│  IoT / Gateway  │
└────────┬────────┘
         │ MQTT Publish
         ▼
┌─────────────────┐
│  Broker EMQX    │
│  (Rule Engine)  │
└────────┬────────┘
         │ HTTP Webhook
         ▼
┌─────────────────────────────────────────────┐
│          IngestView (/ingest)               │
│  ┌───────────────────────────────────────┐  │
│  │   PayloadParserManager                │  │
│  │   ┌─────────────────────────────────┐ │  │
│  │   │  Auto-detecção de formato       │ │  │
│  │   └─────────────────────────────────┘ │  │
│  │                                         │  │
│  │   ┌──────────┐  ┌──────────────────┐  │  │
│  │   │ Standard │  │ Khomp SenML      │  │  │
│  │   │ Parser   │  │ Parser           │  │  │
│  │   └──────────┘  └──────────────────┘  │  │
│  └───────────────────────────────────────┘  │
└────────┬────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│  Formato Padrão TrakSense                   │
│  {                                          │
│    device_id, timestamp, sensors, metadata  │
│  }                                          │
└────────┬────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│  TimescaleDB                                │
│  ┌──────────────┐  ┌────────────────────┐  │
│  │  Telemetry   │  │  Reading           │  │
│  │  (mensagem   │  │  (leituras         │  │
│  │   bruta)     │  │   individuais)     │  │
│  └──────────────┘  └────────────────────┘  │
└─────────────────────────────────────────────┘
```

## 📦 Parsers Disponíveis

### 1. StandardParser

Parser para o formato padrão do TrakSense.

**Formato de Entrada (após EMQX):**
```json
{
  "client_id": "device-001",
  "topic": "tenants/umc/devices/001/sensors",
  "payload": {
    "device_id": "GW-1760908415",
    "timestamp": "2025-10-20T14:30:00Z",
    "sensors": [
      {
        "sensor_id": "temp-amb-01",
        "value": 23.5,
        "unit": "celsius",
        "type": "temperature"
      }
    ]
  },
  "ts": 1729216200000
}
```

### 2. KhompSenMLParser

Parser para gateways LoRaWAN da Khomp que usam formato SenML (RFC 8428).

**Formato de Entrada:**
```json
{
  "client_id": "khomp-gateway-001",
  "topic": "tenants/umc/gateways/khomp/sensors",
  "payload": [
    {
      "bn": "4b686f6d70107115",
      "bt": 1552594568
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
  ],
  "ts": 1729216200000
}
```

**Características:**
- Suporta valores numéricos (v), strings (vs) e booleanos (vb)
- Identifica automaticamente sensores internos (A, B, C1, C2) e externos (DS18B20)
- Diferencia múltiplas medições do mesmo sensor pela unidade (temperatura vs umidade)
- Preserva informações do gateway e modelo do dispositivo
- Converte unidades SenML para unidades padronizadas

## 🎯 Formato Padrão de Saída

Todos os parsers convertem para este formato padrão:

```python
{
    'device_id': str,           # Identificador do dispositivo
    'timestamp': datetime,      # Timestamp da medição
    'sensors': [                # Lista de leituras de sensores
        {
            'sensor_id': str,   # ID único do sensor
            'value': float,     # Valor numérico
            'labels': {         # Metadados do sensor
                'unit': str,
                'type': str,
                'name': str,
                ...
            }
        }
    ],
    'metadata': {               # Metadados adicionais
        'format': str,          # Tipo de parser usado
        'model': str,           # Modelo do dispositivo (opcional)
        'gateway_id': str,      # ID do gateway (opcional)
        ...
    }
}
```

## 🔧 Como Adicionar um Novo Parser

### Passo 1: Criar o Parser

Crie um novo arquivo em `apps/ingest/parsers/` (ex: `my_device_parser.py`):

```python
from apps.ingest.parsers import PayloadParser
from typing import Dict, Any
import datetime

class MyDeviceParser(PayloadParser):
    """Parser para dispositivo XYZ do fabricante ABC."""
    
    def can_parse(self, payload: Dict[str, Any], topic: str) -> bool:
        """
        Verifica se este parser pode processar o payload.
        Implemente a lógica de detecção aqui.
        """
        # Exemplo: verificar se tem campo específico
        if isinstance(payload, dict):
            inner = payload.get('payload', payload)
            return 'xyz_device_type' in inner
        return False
    
    def parse(self, payload: Dict[str, Any], topic: str) -> Dict[str, Any]:
        """
        Processa o payload e retorna no formato padrão.
        """
        # Extrair dados do payload
        inner = payload.get('payload', payload)
        
        # Converter para formato padrão
        result = {
            'device_id': inner['device_id'],
            'timestamp': datetime.datetime.now(),
            'sensors': [],
            'metadata': {
                'format': 'my_device_format'
            }
        }
        
        # Processar sensores...
        # result['sensors'].append({...})
        
        return result
```

### Passo 2: Registrar o Parser

Adicione o módulo em `config/settings/base.py`:

```python
PAYLOAD_PARSER_MODULES = [
    'apps.ingest.parsers.standard',
    'apps.ingest.parsers.khomp_senml',
    'apps.ingest.parsers.my_device_parser',  # ✅ Novo parser
]
```

### Passo 3: Testar

```bash
python test_payload_parsers.py
```

## 🧪 Testes

### Executar Testes dos Parsers

```bash
# Testar todos os parsers
python test_payload_parsers.py

# Publicar dados de teste no formato Khomp
python publish_khomp_senml.py --host localhost --port 1883 --tenant umc
```

### Testes Incluídos

1. **StandardParser**: Valida parsing do formato padrão TrakSense
2. **KhompSenMLParser (Temp/Humid)**: Valida parsing de temperatura e umidade
3. **KhompSenMLParser (Binary Counter)**: Valida parsing de contador binário
4. **ParserManager**: Valida auto-detecção de formato

## 🚀 Deploy em Produção

### Opção 1: Adicionar Parser via Git

1. Criar o arquivo do parser no repositório
2. Registrar em `PAYLOAD_PARSER_MODULES`
3. Fazer commit e deploy via CI/CD
4. Reiniciar a aplicação

```bash
git add apps/ingest/parsers/new_parser.py
git commit -m "feat: adicionar parser para dispositivo XYZ"
git push
# Deploy automático via CI/CD
```

### Opção 2: Hot Reload (Futuro)

Para adicionar parsers sem redeploy, seria possível implementar:

1. **Armazenamento em S3/Azure Blob**
   - Parsers armazenados em bucket cloud
   - Sistema carrega dinamicamente em runtime
   - Atualização sem downtime

2. **Interface Administrativa**
   - Modelo Django para armazenar código do parser
   - Interface web para adicionar/editar parsers
   - Validação de código antes de ativar

3. **API de Gerenciamento**
   - Endpoint para upload de novos parsers
   - Validação e testes automatizados
   - Ativação via API

## 📊 Monitoramento

### Logs

O sistema gera logs detalhados:

```
✅ Registrado parser: StandardParser
✅ Registrado parser: KhompSenMLParser
🎯 Parser selecionado: KhompSenMLParser
✅ KhompSenMLParser: device=4b686f6d70107115, sensors=4, gateway=000D6FFFFE642E70
📊 Device: 4b686f6d70107115, Sensors: 4
✅ Telemetry saved: tenant=umc, device=4b686f6d70107115, format=senml
```

### Métricas

Resposta da API inclui informações do parser:

```json
{
  "status": "accepted",
  "id": 1234,
  "device_id": "4b686f6d70107115",
  "timestamp": "2025-10-20T14:30:00Z",
  "sensors_saved": 4,
  "format": "senml",
  "gateway_id": "000D6FFFFE642E70",
  "model": "nit20l"
}
```

## 🔍 Troubleshooting

### Parser não está sendo detectado

1. Verificar se o módulo está em `PAYLOAD_PARSER_MODULES`
2. Verificar logs de inicialização para erros de importação
3. Garantir que a classe herda de `PayloadParser`
4. Verificar se `can_parse()` retorna `True` para o payload

### Payload não está sendo parseado corretamente

1. Adicionar logs no método `parse()`
2. Validar estrutura do payload recebido
3. Verificar conversão de tipos (timestamp, valores numéricos)
4. Testar isoladamente com `test_payload_parsers.py`

### Recarregar parsers em runtime

```python
from apps.ingest.parsers import parser_manager
parser_manager.reload_parsers()
```

## 📚 Referências

- [RFC 8428 - SenML](https://datatracker.ietf.org/doc/html/rfc8428)
- [Documentação Khomp LoRaWAN](https://www.khomp.com)
- [EMQX Rule Engine](https://www.emqx.io/docs/en/v5.0/data-integration/rules.html)

## 🎉 Próximos Passos

- [ ] Implementar parser para outros fabricantes (ex: Dragino, RAK Wireless)
- [ ] Adicionar validação de schema (JSON Schema, Pydantic)
- [ ] Criar interface administrativa para gerenciar parsers
- [ ] Implementar sistema de hot reload via S3
- [ ] Adicionar métricas de performance por parser
- [ ] Criar testes automatizados de integração
