"""
Script de teste para validar os parsers de payload.

Testa tanto o formato padrão TrakSense quanto o formato SenML da Khomp.
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.ingest.parsers import parser_manager
from apps.ingest.parsers.standard import StandardParser
from apps.ingest.parsers.khomp_senml import KhompSenMLParser
import json
from datetime import datetime


def test_standard_parser():
    """Testa o parser padrão TrakSense."""
    print("=" * 80)
    print("🧪 TESTE 1: Parser Padrão TrakSense")
    print("=" * 80)
    
    # Payload no formato padrão
    payload = {
        "client_id": "GW-1760908415",
        "topic": "tenants/umc/assets/CHILLER-001/telemetry",
        "payload": {
            "device_id": "GW-1760908415",
            "timestamp": "2025-10-20T14:30:00Z",
            "sensors": [
                {
                    "sensor_id": "temp-amb-01",
                    "value": 23.5,
                    "unit": "celsius",
                    "type": "temperature"
                },
                {
                    "sensor_id": "humid-01",
                    "value": 65.2,
                    "unit": "percent",
                    "type": "humidity"
                },
                {
                    "sensor_id": "pressure-01",
                    "value": 1013.25,
                    "unit": "hPa",
                    "type": "pressure"
                }
            ]
        },
        "ts": 1729426200000
    }
    
    parser = StandardParser()
    
    # Testar detecção
    can_parse = parser.can_parse(payload, payload['topic'])
    print(f"✅ Pode parsear: {can_parse}")
    
    if can_parse:
        # Testar parsing
        result = parser.parse(payload, payload['topic'])
        print(f"\n📊 Resultado do Parse:")
        print(f"  Device ID: {result['device_id']}")
        print(f"  Timestamp: {result['timestamp']}")
        print(f"  Formato: {result['metadata']['format']}")
        print(f"\n  Sensores ({len(result['sensors'])}):")
        for sensor in result['sensors']:
            print(f"    - {sensor['sensor_id']}: {sensor['value']} {sensor['labels'].get('unit', 'N/A')}")
            print(f"      Tipo: {sensor['labels'].get('type', 'unknown')}")
    
    print("\n")


def test_khomp_senml_parser_temp_humidity():
    """Testa o parser SenML da Khomp com temperatura e umidade."""
    print("=" * 80)
    print("🧪 TESTE 2: Parser Khomp SenML - Temperatura e Umidade")
    print("=" * 80)
    
    # Payload no formato SenML da Khomp
    payload = {
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
        "ts": 1729426200000
    }
    
    parser = KhompSenMLParser()
    
    # Testar detecção
    can_parse = parser.can_parse(payload, payload['topic'])
    print(f"✅ Pode parsear: {can_parse}")
    
    if can_parse:
        # Testar parsing
        result = parser.parse(payload, payload['topic'])
        print(f"\n📊 Resultado do Parse:")
        print(f"  Device ID: {result['device_id']}")
        print(f"  Timestamp: {result['timestamp']}")
        print(f"  Formato: {result['metadata']['format']}")
        print(f"  Modelo: {result['metadata']['model']}")
        print(f"  Gateway: {result['metadata']['gateway_id']}")
        print(f"\n  Sensores ({len(result['sensors'])}):")
        for sensor in result['sensors']:
            print(f"    - {sensor['sensor_id']}: {sensor['value']}")
            print(f"      Unidade: {sensor['labels'].get('unit', 'N/A')}")
            print(f"      Tipo: {sensor['labels'].get('type', 'unknown')}")
            if sensor['labels'].get('original_unit'):
                print(f"      Unidade original: {sensor['labels']['original_unit']}")
    
    print("\n")


def test_khomp_senml_parser_binary_counter():
    """Testa o parser SenML da Khomp com contador binário."""
    print("=" * 80)
    print("🧪 TESTE 3: Parser Khomp SenML - Contador Binário")
    print("=" * 80)
    
    # Payload no formato SenML da Khomp com contador binário
    payload = {
        "client_id": "khomp-gateway-002",
        "topic": "tenants/umc/gateways/khomp/sensors",
        "payload": [
            {
                "bn": "4b686f6d70108826",
                "bt": 1558394996
            },
            {
                "n": "model",
                "vs": "nit20l"
            },
            {
                "n": "C1",
                "vb": True
            },
            {
                "n": "C1",
                "u": "count",
                "v": 3
            },
            {
                "n": "gateway",
                "vs": "000D6FFFFE642E70"
            }
        ],
        "ts": 1729426200000
    }
    
    parser = KhompSenMLParser()
    
    # Testar detecção
    can_parse = parser.can_parse(payload, payload['topic'])
    print(f"✅ Pode parsear: {can_parse}")
    
    if can_parse:
        # Testar parsing
        result = parser.parse(payload, payload['topic'])
        print(f"\n📊 Resultado do Parse:")
        print(f"  Device ID: {result['device_id']}")
        print(f"  Timestamp: {result['timestamp']}")
        print(f"  Formato: {result['metadata']['format']}")
        print(f"  Modelo: {result['metadata']['model']}")
        print(f"  Gateway: {result['metadata']['gateway_id']}")
        print(f"\n  Sensores ({len(result['sensors'])}):")
        for sensor in result['sensors']:
            print(f"    - {sensor['sensor_id']}: {sensor['value']}")
            print(f"      Tipo: {sensor['labels'].get('type', 'unknown')}")
            print(f"      Tipo de valor: {sensor['labels'].get('value_type', 'numeric')}")
            if sensor['labels'].get('original_value'):
                print(f"      Valor original: {sensor['labels']['original_value']}")
    
    print("\n")


def test_parser_manager():
    """Testa o gerenciador de parsers."""
    print("=" * 80)
    print("🧪 TESTE 4: Gerenciador de Parsers (Auto-detecção)")
    print("=" * 80)
    
    # Testar com payload padrão
    standard_payload = {
        "client_id": "device-001",
        "topic": "tenants/umc/devices/001/telemetry",
        "payload": {
            "device_id": "device-001",
            "sensors": [{"sensor_id": "temp-01", "value": 25.0, "unit": "celsius"}]
        },
        "ts": 1729426200000
    }
    
    # Testar com payload SenML
    senml_payload = {
        "client_id": "khomp-001",
        "topic": "tenants/umc/gateways/khomp",
        "payload": [
            {"bn": "4b686f6d70107115", "bt": 1552594568},
            {"n": "A", "u": "Cel", "v": 23.35}
        ],
        "ts": 1729426200000
    }
    
    print("\n📋 Teste 1: Payload Padrão")
    parser1 = parser_manager.get_parser(standard_payload, standard_payload['topic'])
    if parser1:
        print(f"  ✅ Parser selecionado: {parser1.__class__.__name__}")
    else:
        print("  ❌ Nenhum parser encontrado")
    
    print("\n📋 Teste 2: Payload SenML")
    parser2 = parser_manager.get_parser(senml_payload, senml_payload['topic'])
    if parser2:
        print(f"  ✅ Parser selecionado: {parser2.__class__.__name__}")
    else:
        print("  ❌ Nenhum parser encontrado")
    
    print("\n")


def main():
    """Executa todos os testes."""
    print("\n")
    print("🚀 INICIANDO TESTES DE PARSERS")
    print("=" * 80)
    print("\n")
    
    try:
        test_standard_parser()
        test_khomp_senml_parser_temp_humidity()
        test_khomp_senml_parser_binary_counter()
        test_parser_manager()
        
        print("=" * 80)
        print("✅ TODOS OS TESTES CONCLUÍDOS COM SUCESSO!")
        print("=" * 80)
        print("\n")
        
    except Exception as e:
        print(f"\n❌ ERRO NOS TESTES: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
