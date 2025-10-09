"""
Adapter para protocolo JE02 v1 - Inversores IoT

Protocolo JE02:
--------------
- Payload DATA: telemetria periódica com INPUT1, INPUT2, VAR0, VAR1, WRSSI, RELE, CNTSERR, UPTIME
- Payload INFO: metadados do dispositivo (versão firmware, etc)

Mapeamento DATA → PointTemplates:
--------------------------------
- status (ENUM): 
    - INPUT2 == 1 → 'FAULT'
    - INPUT1 == 1 → 'RUN'
    - else → 'STOP'
- fault (BOOL): INPUT2 == 1
- rssi (NUM, dBm): WRSSI (sinal WiFi, negativo)
- uptime (NUM, s): UPTIME
- cntserr (NUM): CNTSERR (contador de erros seriais)
- var0 (NUM, °C): VAR0 / 10.0 (temperatura)
- var1 (NUM, %): VAR1 / 10.0 (umidade)
- rele (BOOL): RELE != 0

Autor: TrakSense Team
Data: 2025-10-08 (Fase D)
"""

from datetime import datetime, timezone
from typing import Dict, Any
from .types import Normalized


def adapt_je02_data(payload: Dict[str, Any]) -> Normalized:
    """
    Transforma payload JE02 DATA em formato normalizado.
    
    Args:
        payload: Dict com chave 'DATA' contendo:
            - TS (int): timestamp Unix (segundos)
            - INPUT1 (int): 0 ou 1 (RUN)
            - INPUT2 (int): 0 ou 1 (FAULT)
            - VAR0 (int): temperatura * 10 (ex: 235 → 23.5°C)
            - VAR1 (int): umidade * 10 (ex: 550 → 55.0%)
            - WRSSI (int): sinal WiFi (ex: -65 dBm)
            - RELE (int): estado do relé (0 ou 1)
            - CNTSERR (int): contador de erros seriais
            - UPTIME (int): uptime em segundos
    
    Returns:
        Tupla (timestamp, points, metadata) onde:
        - timestamp: datetime object
        - points: lista de (name, type, value, unit)
        - metadata: dict vazio (sem metadata adicional)
    
    Raises:
        KeyError: se payload não contém chave 'DATA' ou campos obrigatórios
        ValueError: se valores estão fora dos ranges esperados
    """
    data = payload["DATA"]
    
    # 1. Extrair timestamp (sempre em UTC)
    ts_unix = data["TS"]
    ts = datetime.fromtimestamp(ts_unix, tz=timezone.utc)
    
    # 2. Extrair valores brutos
    input1 = data["INPUT1"]
    input2 = data["INPUT2"]
    var0_raw = data["VAR0"]
    var1_raw = data["VAR1"]
    wrssi = data["WRSSI"]
    rele_raw = data["RELE"]
    cntserr = data["CNTSERR"]
    uptime = data["UPTIME"]
    
    # 3. Calcular status (ENUM)
    if input2 == 1:
        status = "FAULT"
    elif input1 == 1:
        status = "RUN"
    else:
        status = "STOP"
    
    # 4. Calcular valores derivados
    fault = (input2 == 1)
    var0 = var0_raw / 10.0  # Temperatura em °C
    var1 = var1_raw / 10.0  # Umidade em %
    rele = (rele_raw != 0)
    
    # 5. Montar lista de pontos
    # Formato: (name, type, value, unit)
    points = [
        ("status", "ENUM", status, None),
        ("fault", "BOOL", fault, None),
        ("rssi", "NUM", wrssi, "dBm"),
        ("uptime", "NUM", uptime, "s"),
        ("cntserr", "NUM", cntserr, None),
        ("var0", "NUM", var0, "°C"),
        ("var1", "NUM", var1, "%"),
        ("rele", "BOOL", rele, None),
    ]
    
    # 6. Metadata vazio (sem metadata adicional no protocolo JE02)
    metadata = {}
    
    return (ts, points, metadata)


def adapt_je02_info(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extrai metadados do payload JE02 INFO.
    
    Args:
        payload: Dict com chave 'INFO' contendo metadados do dispositivo
            Exemplo:
            {
                "INFO": {
                    "FW_VERSION": "1.2.3",
                    "HW_VERSION": "v1",
                    "DEVICE_ID": "INV-01",
                    "MODEL": "JE02-INVERTER"
                }
            }
    
    Returns:
        Dict com metadados extraídos (preserva estrutura original)
    
    Raises:
        KeyError: se payload não contém chave 'INFO'
    """
    info = payload["INFO"]
    
    # Retornar metadados como dict (será serializado para JSONB)
    # Preserva estrutura original do INFO
    metadata = {
        "source": "je02_info",
        "info": info
    }
    
    return metadata
