"""
Testes Unitários para Adapter JE02 - Payload DATA

Testa a função adapt_je02_data que transforma payloads JE02 DATA
em formato normalizado.

Cobertura:
- ✅ Payload válido → pontos normalizados corretos
- ✅ Status mapping (INPUT2=1→FAULT, INPUT1=1→RUN, else→STOP)
- ✅ Escala var0/var1 (÷10)
- ✅ Boolean rele (!=0)
- ✅ Timestamp Unix → datetime
- ✅ Payload inválido → KeyError

Execução:
    # No diretório ingest:
    pytest test_adapter_je02_data.py -v
    
    # Com coverage:
    pytest test_adapter_je02_data.py --cov=adapters.je02_v1 --cov-report=term-missing

Autor: TrakSense Team
Data: 2025-10-08 (Fase D - JE02)
"""

import pytest
from datetime import datetime
from adapters.je02_v1 import adapt_je02_data


class TestAdaptJE02Data:
    """Testes para adapt_je02_data"""
    
    def test_payload_valido_status_run(self):
        """Testa payload válido com status RUN"""
        payload = {
            "DATA": {
                "TS": 1696640052,
                "INPUT1": 1,  # RUN
                "INPUT2": 0,  # OK
                "VAR0": 235,  # 23.5°C
                "VAR1": 550,  # 55.0%
                "WRSSI": -68,
                "RELE": 1,
                "CNTSERR": 5,
                "UPTIME": 3600
            }
        }
        
        ts, points, meta = adapt_je02_data(payload)
        
        # Verificar timestamp
        assert isinstance(ts, datetime)
        assert ts == datetime.fromtimestamp(1696640052)
        
        # Verificar pontos
        assert len(points) == 8
        
        # Verificar cada ponto
        points_dict = {p[0]: p for p in points}
        
        # status: RUN (INPUT1=1)
        assert points_dict["status"] == ("status", "ENUM", "RUN", None)
        
        # fault: False (INPUT2=0)
        assert points_dict["fault"] == ("fault", "BOOL", False, None)
        
        # rssi: -68 dBm
        assert points_dict["rssi"] == ("rssi", "NUM", -68, "dBm")
        
        # uptime: 3600s
        assert points_dict["uptime"] == ("uptime", "NUM", 3600, "s")
        
        # cntserr: 5
        assert points_dict["cntserr"] == ("cntserr", "NUM", 5, None)
        
        # var0: 23.5°C (235/10)
        assert points_dict["var0"] == ("var0", "NUM", 23.5, "°C")
        
        # var1: 55.0% (550/10)
        assert points_dict["var1"] == ("var1", "NUM", 55.0, "%")
        
        # rele: True (1 != 0)
        assert points_dict["rele"] == ("rele", "BOOL", True, None)
        
        # Metadata vazio
        assert meta == {}
    
    def test_payload_valido_status_fault(self):
        """Testa payload válido com status FAULT"""
        payload = {
            "DATA": {
                "TS": 1696640052,
                "INPUT1": 0,
                "INPUT2": 1,  # FAULT
                "VAR0": 210,
                "VAR1": 450,
                "WRSSI": -75,
                "RELE": 0,
                "CNTSERR": 10,
                "UPTIME": 7200
            }
        }
        
        ts, points, meta = adapt_je02_data(payload)
        
        points_dict = {p[0]: p for p in points}
        
        # status: FAULT (INPUT2=1 tem prioridade)
        assert points_dict["status"][2] == "FAULT"
        
        # fault: True
        assert points_dict["fault"][2] is True
    
    def test_payload_valido_status_stop(self):
        """Testa payload válido com status STOP"""
        payload = {
            "DATA": {
                "TS": 1696640052,
                "INPUT1": 0,  # Não RUN
                "INPUT2": 0,  # Não FAULT
                "VAR0": 260,
                "VAR1": 650,
                "WRSSI": -55,
                "RELE": 0,
                "CNTSERR": 0,
                "UPTIME": 100
            }
        }
        
        ts, points, meta = adapt_je02_data(payload)
        
        points_dict = {p[0]: p for p in points}
        
        # status: STOP (INPUT1=0 e INPUT2=0)
        assert points_dict["status"][2] == "STOP"
        
        # fault: False
        assert points_dict["fault"][2] is False
    
    def test_escala_var0_var1(self):
        """Testa escala de VAR0 e VAR1 (dividir por 10)"""
        payload = {
            "DATA": {
                "TS": 1696640052,
                "INPUT1": 1,
                "INPUT2": 0,
                "VAR0": 210,  # → 21.0°C
                "VAR1": 600,  # → 60.0%
                "WRSSI": -60,
                "RELE": 0,
                "CNTSERR": 0,
                "UPTIME": 0
            }
        }
        
        ts, points, meta = adapt_je02_data(payload)
        
        points_dict = {p[0]: p for p in points}
        
        assert points_dict["var0"][2] == 21.0
        assert points_dict["var1"][2] == 60.0
    
    def test_rele_boolean(self):
        """Testa conversão de RELE para boolean"""
        # RELE=0 → False
        payload_off = {
            "DATA": {
                "TS": 1696640052,
                "INPUT1": 0,
                "INPUT2": 0,
                "VAR0": 220,
                "VAR1": 500,
                "WRSSI": -60,
                "RELE": 0,
                "CNTSERR": 0,
                "UPTIME": 0
            }
        }
        
        ts, points, meta = adapt_je02_data(payload_off)
        points_dict = {p[0]: p for p in points}
        assert points_dict["rele"][2] is False
        
        # RELE=1 → True
        payload_on = {
            "DATA": {
                "TS": 1696640052,
                "INPUT1": 0,
                "INPUT2": 0,
                "VAR0": 220,
                "VAR1": 500,
                "WRSSI": -60,
                "RELE": 1,
                "CNTSERR": 0,
                "UPTIME": 0
            }
        }
        
        ts, points, meta = adapt_je02_data(payload_on)
        points_dict = {p[0]: p for p in points}
        assert points_dict["rele"][2] is True
        
        # RELE=2 → True (qualquer valor != 0)
        payload_2 = {
            "DATA": {
                "TS": 1696640052,
                "INPUT1": 0,
                "INPUT2": 0,
                "VAR0": 220,
                "VAR1": 500,
                "WRSSI": -60,
                "RELE": 2,
                "CNTSERR": 0,
                "UPTIME": 0
            }
        }
        
        ts, points, meta = adapt_je02_data(payload_2)
        points_dict = {p[0]: p for p in points}
        assert points_dict["rele"][2] is True
    
    def test_payload_sem_chave_data(self):
        """Testa erro quando payload não contém chave DATA"""
        payload = {
            "INVALID": {}
        }
        
        with pytest.raises(KeyError):
            adapt_je02_data(payload)
    
    def test_payload_data_incompleto(self):
        """Testa erro quando DATA não contém campos obrigatórios"""
        payload = {
            "DATA": {
                "TS": 1696640052,
                "INPUT1": 1
                # Faltando outros campos
            }
        }
        
        with pytest.raises(KeyError):
            adapt_je02_data(payload)
    
    def test_timestamp_unix_valido(self):
        """Testa conversão de timestamp Unix para datetime"""
        # Timestamp conhecido: 2023-10-07 02:34:12 UTC
        payload = {
            "DATA": {
                "TS": 1696640052,
                "INPUT1": 0,
                "INPUT2": 0,
                "VAR0": 220,
                "VAR1": 500,
                "WRSSI": -60,
                "RELE": 0,
                "CNTSERR": 0,
                "UPTIME": 0
            }
        }
        
        ts, points, meta = adapt_je02_data(payload)
        
        # Verificar datetime
        assert ts.year == 2023
        assert ts.month == 10
        assert ts.day == 7
        assert ts.hour == 2
        assert ts.minute == 34
        assert ts.second == 12
    
    def test_valores_extremos(self):
        """Testa valores nos extremos dos ranges"""
        payload = {
            "DATA": {
                "TS": 1696640052,
                "INPUT1": 1,
                "INPUT2": 1,  # Ambos ligados (FAULT tem prioridade)
                "VAR0": 0,    # Mínimo
                "VAR1": 9999, # Máximo
                "WRSSI": -100,  # Sinal muito fraco
                "RELE": 255,    # Valor alto
                "CNTSERR": 10000,
                "UPTIME": 999999
            }
        }
        
        ts, points, meta = adapt_je02_data(payload)
        
        points_dict = {p[0]: p for p in points}
        
        # Status: FAULT (INPUT2 tem prioridade)
        assert points_dict["status"][2] == "FAULT"
        
        # VAR0: 0.0°C
        assert points_dict["var0"][2] == 0.0
        
        # VAR1: 999.9%
        assert points_dict["var1"][2] == 999.9
        
        # RELE: True (255 != 0)
        assert points_dict["rele"][2] is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
