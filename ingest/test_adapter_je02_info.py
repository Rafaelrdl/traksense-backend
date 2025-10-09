"""
Testes Unitários para Adapter JE02 - Payload INFO

Testa a função adapt_je02_info que extrai metadados do payload INFO.

Cobertura:
- ✅ Payload INFO válido → metadata extraído
- ✅ Preservação da estrutura original
- ✅ Payload sem chave INFO → KeyError

Execução:
    # No diretório ingest:
    pytest test_adapter_je02_info.py -v
    
    # Com coverage:
    pytest test_adapter_je02_info.py --cov=adapters.je02_v1 --cov-report=term-missing

Autor: TrakSense Team
Data: 2025-10-08 (Fase D - JE02)
"""

import pytest
from adapters.je02_v1 import adapt_je02_info


class TestAdaptJE02Info:
    """Testes para adapt_je02_info"""
    
    def test_payload_info_valido(self):
        """Testa payload INFO válido"""
        payload = {
            "INFO": {
                "FW_VERSION": "1.2.3",
                "HW_VERSION": "v1",
                "DEVICE_ID": "INV-01",
                "MODEL": "JE02-INVERTER"
            }
        }
        
        meta = adapt_je02_info(payload)
        
        # Verificar estrutura do metadata
        assert "source" in meta
        assert meta["source"] == "je02_info"
        
        assert "info" in meta
        assert meta["info"] == payload["INFO"]
        
        # Verificar campos específicos
        assert meta["info"]["FW_VERSION"] == "1.2.3"
        assert meta["info"]["HW_VERSION"] == "v1"
        assert meta["info"]["DEVICE_ID"] == "INV-01"
        assert meta["info"]["MODEL"] == "JE02-INVERTER"
    
    def test_payload_info_campos_extras(self):
        """Testa payload INFO com campos adicionais"""
        payload = {
            "INFO": {
                "FW_VERSION": "2.0.0",
                "HW_VERSION": "v2",
                "DEVICE_ID": "INV-07",
                "MODEL": "JE02-INVERTER-PRO",
                "MANUFACTURER": "TrakSense",
                "SERIAL": "ABC123XYZ",
                "BUILD_DATE": "2025-01-15"
            }
        }
        
        meta = adapt_je02_info(payload)
        
        # Verificar que todos os campos foram preservados
        assert meta["info"]["FW_VERSION"] == "2.0.0"
        assert meta["info"]["MANUFACTURER"] == "TrakSense"
        assert meta["info"]["SERIAL"] == "ABC123XYZ"
        assert meta["info"]["BUILD_DATE"] == "2025-01-15"
    
    def test_payload_info_vazio(self):
        """Testa payload INFO vazio"""
        payload = {
            "INFO": {}
        }
        
        meta = adapt_je02_info(payload)
        
        # Metadata deve conter estrutura básica mesmo com INFO vazio
        assert meta["source"] == "je02_info"
        assert meta["info"] == {}
    
    def test_payload_sem_chave_info(self):
        """Testa erro quando payload não contém chave INFO"""
        payload = {
            "DATA": {}
        }
        
        with pytest.raises(KeyError):
            adapt_je02_info(payload)
    
    def test_payload_info_nulo(self):
        """Testa payload com INFO nulo"""
        payload = {
            "INFO": None
        }
        
        meta = adapt_je02_info(payload)
        
        # Deve preservar estrutura mesmo com None
        assert meta["source"] == "je02_info"
        assert meta["info"] is None
    
    def test_preservacao_estrutura_original(self):
        """Testa que a estrutura original do INFO é preservada"""
        payload = {
            "INFO": {
                "FW_VERSION": "1.2.3",
                "nested": {
                    "key1": "value1",
                    "key2": 123
                },
                "array": [1, 2, 3]
            }
        }
        
        meta = adapt_je02_info(payload)
        
        # Verificar que estrutura aninhada foi preservada
        assert meta["info"]["nested"]["key1"] == "value1"
        assert meta["info"]["nested"]["key2"] == 123
        assert meta["info"]["array"] == [1, 2, 3]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
