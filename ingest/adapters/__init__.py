"""
Adapters de Normalização de Payloads - TrakSense Ingest

Este módulo contém adapters para validar e normalizar payloads MQTT
de diferentes vendors/fabricantes de equipamentos IoT.

Arquitetura de Adapters:
-----------------------
Cada vendor/equipamento pode enviar dados em formatos diferentes.
Os adapters convertem esses formatos proprietários para um formato
padrão (envelope normalizado) que pode ser persistido no TimescaleDB.

Fluxo:
------
    [Device Parsec] ---> payload_parsec.json
                              |
                              v
                    [normalize_parsec_v1()]
                              |
                              v (valida e normaliza)
                    envelope_padrao.json
                              |
                              v
                    [TimescaleDB insert]

Formato do Envelope Padrão:
---------------------------
{
  "schema": "v1",
  "ts": "2025-10-07T02:34:12Z",
  "points": [
    {"name":"temp_agua", "t":"float", "v":7.3, "u":"°C"},
    {"name":"compressor_1_on", "t":"bool", "v":true}
  ],
  "meta": {"fw":"1.2.3", "src":"parsec_v1"}
}

Campos:
- schema: Versão do schema (versionamento)
- ts: Timestamp ISO8601 UTC
- points: Lista de medições normalizadas
  - name: Identificador do ponto (snake_case)
  - t: Tipo (float, bool, int, string)
  - v: Valor medido
  - u: Unidade (opcional, ex: °C, kW, bar)
- meta: Metadados adicionais (firmware, versão do adapter, etc.)

Implementação de Novos Adapters:
--------------------------------
1. Criar arquivo: adapters/vendor_vX.py (ex: parsec_v1.py)
2. Definir schema Pydantic para validação do payload de entrada
3. Implementar função normalize(payload: dict) -> dict
4. Retornar envelope padrão ou levantar ValidationError
5. Registrar adapter no registry (adapters/__init__.py)

Exemplo de Adapter (parsec_v1.py):
----------------------------------
from pydantic import BaseModel, ValidationError
from datetime import datetime

class ParsecPayload(BaseModel):
    timestamp: int  # Unix timestamp
    DI1: int        # Digital Input 1 (0/1)
    DI2: int        # Digital Input 2 (0/1)
    AI1: float      # Analog Input 1

def normalize(raw: dict, tenant_id: str, device_id: str) -> dict:
    # Valida payload de entrada
    payload = ParsecPayload(**raw)
    
    # Converte para envelope padrão
    return {
        "schema": "v1",
        "ts": datetime.fromtimestamp(payload.timestamp).isoformat(),
        "points": [
            {"name": "device_status", "t": "int", "v": payload.DI1},
            {"name": "fault_status", "t": "int", "v": payload.DI2},
            {"name": "temperatura", "t": "float", "v": payload.AI1, "u": "°C"}
        ],
        "meta": {"src": "parsec_v1"}
    }

Registry de Adapters:
--------------------
Mapeamento de identificador -> função de normalização.
Permite seleção dinâmica do adapter baseado em:
- Device template (ex: device.template.adapter_id)
- Tópico MQTT (ex: parsec/v1/...)
- Header no payload (ex: {"adapter": "parsec_v1"})

Erro Handling:
-------------
- ValidationError (Pydantic): Payload não corresponde ao schema esperado
  -> Enviar para DLQ (Dead Letter Queue) com erro detalhado
  -> Não tentar novamente (erro permanente)

- ValueError: Valores fora do range esperado
  -> Logar warning e usar valor padrão OU rejeitar

- KeyError: Campo obrigatório ausente
  -> Enviar para DLQ (payload malformado)

Testes:
-------
Cada adapter deve ter testes unitários com:
- Payload válido -> envelope padrão correto
- Payload inválido -> ValidationError com mensagem clara
- Edge cases (valores nulos, limites, etc.)

Exemplo:
def test_parsec_v1_normalize():
    raw = {"timestamp": 1696640052, "DI1": 1, "DI2": 0, "AI1": 22.5}
    result = parsec_v1.normalize(raw, tenant_id, device_id)
    assert result["schema"] == "v1"
    assert len(result["points"]) == 3
    assert result["points"][2]["v"] == 22.5

Referências:
-----------
- Pydantic Docs: https://docs.pydantic.dev/
- MQTT Topic Structure: /docs/mqtt-topics.md
- Device Templates: backend/apps/devices/models.py

TODO (Fase 2):
-------------
- [ ] Implementar parsec_v1.py (inversores Parsec)
- [ ] Implementar chiller_v1.py (chillers genéricos)
- [ ] Implementar modbus_tcp.py (equipamentos Modbus)
- [ ] Criar registry dinâmico de adapters
- [ ] Adicionar testes para cada adapter
- [ ] Documentar schema de cada vendor em /docs/adapters/

Autor: TrakSense Team
Data: 2025-10-07
"""

# ============================================================================
# REGISTRY DE ADAPTERS (Fase 2)
# ============================================================================
# Será populado quando adapters forem implementados:
#
# from adapters import parsec_v1, chiller_v1, modbus_tcp
#
# ADAPTER_REGISTRY = {
#     'parsec_v1': parsec_v1.normalize,
#     'chiller_v1': chiller_v1.normalize,
#     'modbus_tcp': modbus_tcp.normalize,
# }
#
# def get_adapter(adapter_id: str):
#     if adapter_id not in ADAPTER_REGISTRY:
#         raise ValueError(f"Adapter '{adapter_id}' não encontrado")
#     return ADAPTER_REGISTRY[adapter_id]
# ============================================================================


# ============================================================================
# Função normalize_parsec_v1 (Fase 4 - Ingest Assíncrono)
# ============================================================================
from .types import Normalized


def normalize_parsec_v1(payload: dict, tenant: str, site: str, device: str) -> Normalized:
    """
    Normaliza payload do inversor Parsec v1 para formato interno.
    
    Payload esperado (exemplo):
    {
        "di1": 1,        # Digital Input 1: 1=RUN, 0=STOP
        "di2": 0,        # Digital Input 2: 1=FAULT, 0=OK
        "rssi": -68,     # Sinal WiFi (dBm)
        "fw": "1.2.3",   # Versão do firmware
        "ts": "2025-10-07T15:30:00Z"
    }
    
    Args:
        payload: Dicionário do payload bruto
        tenant: ID do tenant
        site: ID do site
        device: ID do device
    
    Returns:
        Tupla (timestamp, lista_de_pontos, metadata)
        - timestamp: datetime object (não string!)
        - lista_de_pontos: [(nome, tipo, valor, unidade), ...]
        - metadata: dict com fw, src, etc.
    
    Raises:
        KeyError: Se campos obrigatórios estiverem faltando
        ValueError: Se valores forem inválidos
    """
    from datetime import datetime
    
    # Extrair timestamp (obrigatório) e converter para datetime
    ts_str = payload["ts"]
    ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
    
    # Extrair digital inputs
    di1 = payload.get("di1", 0)
    di2 = payload.get("di2", 0)
    
    # Mapear DI1 para status (enum)
    status = "RUN" if di1 == 1 else "STOP"
    
    # Mapear DI2 para fault (bool)
    fault = bool(di2 == 1)
    
    # Extrair RSSI (sinal WiFi)
    rssi = payload.get("rssi")
    
    # Montar lista de pontos normalizados
    # Formato: (nome, tipo, valor, unidade)
    points = [
        ("status", "enum", status, None),
        ("fault", "bool", fault, None),
    ]
    
    # Adicionar RSSI se presente
    if rssi is not None:
        points.append(("rssi", "num", rssi, "dBm"))
    
    # Metadata adicional
    meta = {
        "fw": payload.get("fw"),
        "src": "parsec_v1",
        "tenant": tenant,
        "site": site,
        "device": device
    }
    
    return ts, points, meta


# ============================================================================
# Função adapt_je02_data (Fase D - JE02 Protocol)
# ============================================================================
from .je02_v1 import adapt_je02_data, adapt_je02_info


# ============================================================================
# Exports
# ============================================================================
__all__ = [
    "normalize_parsec_v1",  # Fase 4
    "adapt_je02_data",      # Fase D - JE02 DATA
    "adapt_je02_info",      # Fase D - JE02 INFO
]
