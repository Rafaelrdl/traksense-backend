"""
Modelos Pydantic para validação de payloads MQTT.

Define os schemas v1 para:
- Telemetria (TelemetryV1)
- Comandos ACK (AckV1)
- Eventos (EventV1)
"""

from pydantic import BaseModel, Field
from typing import Literal, Any, List, Optional
from datetime import datetime


class Point(BaseModel):
    """
    Ponto de dados de telemetria.
    
    Atributos:
        name: Nome do ponto (ex: "temp_agua", "status")
        t: Tipo do valor ("float", "bool", "enum", "text", "num")
        v: Valor do ponto (tipagem dinâmica)
        u: Unidade opcional (ex: "°C", "dBm", "RPM")
    """
    name: str
    t: Literal["float", "bool", "enum", "text", "num"] = "num"
    v: Any
    u: Optional[str] = None


class TelemetryV1(BaseModel):
    """
    Payload de telemetria normalizado (schema v1).
    
    Envelope padrão para dados de sensores/devices.
    """
    schema: Literal["v1"]
    ts: str  # ISO 8601 timestamp
    points: List[Point]
    meta: Optional[dict] = Field(default_factory=dict)
    
    class Config:
        json_schema_extra = {
            "example": {
                "schema": "v1",
                "ts": "2025-10-07T15:30:00Z",
                "points": [
                    {"name": "temp_agua", "t": "float", "v": 7.3, "u": "°C"},
                    {"name": "compressor_1_on", "t": "bool", "v": True}
                ],
                "meta": {"fw": "1.2.3", "src": "parsec_v1"}
            }
        }


class AckV1(BaseModel):
    """
    Payload de ACK de comando (schema v1).
    
    Confirmação de execução de comando por device.
    """
    schema: Literal["v1"]
    cmd_id: str  # ULID ou UUID do comando
    ok: bool  # Sucesso ou falha
    ts_exec: Optional[str] = None  # Timestamp de execução
    err: Optional[str] = None  # Mensagem de erro (se ok=False)
    
    class Config:
        json_schema_extra = {
            "example": {
                "schema": "v1",
                "cmd_id": "01HQZC5K3M8YBQWER7TXZ9V2P3",
                "ok": True,
                "ts_exec": "2025-10-07T15:30:05Z",
                "err": None
            }
        }


class EventV1(BaseModel):
    """
    Payload de evento (schema v1).
    
    Eventos discretos do device (ex: boot, shutdown, reset).
    """
    schema: Literal["v1"]
    event_id: Optional[str] = None  # ULID ou UUID (opcional)
    event_type: str  # Ex: "boot", "shutdown", "reset_fault"
    ts: str  # ISO 8601 timestamp
    data: Optional[dict] = Field(default_factory=dict)
    
    class Config:
        json_schema_extra = {
            "example": {
                "schema": "v1",
                "event_id": "01HQZC5K3M8YBQWER7TXZ9V2P4",
                "event_type": "boot",
                "ts": "2025-10-07T15:00:00Z",
                "data": {"reason": "power_on", "fw": "1.2.3"}
            }
        }
