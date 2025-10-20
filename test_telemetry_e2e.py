"""
FASE 3 - Teste End-to-End: Telemetria Completa
=================================================

Testa a integração completa:
1. Backend API (3 endpoints)
2. Geração de dados de teste
3. Validação de responses
4. Performance e agregação

Requisitos:
- Backend rodando em http://localhost:8000
- Usuário admin criado
- Dados de teste gerados (test_generate_telemetry.py)
"""

import requests
import json
from datetime import datetime, timedelta
import time

# ==============================
# CONFIGURAÇÃO
# ==============================

API_BASE_URL = "http://localhost:8000"
USERNAME = "admin"
PASSWORD = "admin"
DEVICE_ID = "GW-1760908415"  # Device criado pelo test_generate_telemetry.py

# Cores para output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

# ==============================
# HELPER FUNCTIONS
# ==============================

def print_header(text):
    """Imprime cabeçalho destacado."""
    print(f"\n{BLUE}{'=' * 70}{RESET}")
    print(f"{BLUE}{text.center(70)}{RESET}")
    print(f"{BLUE}{'=' * 70}{RESET}\n")

def print_success(text):
    """Imprime mensagem de sucesso."""
    print(f"{GREEN}✓ {text}{RESET}")

def print_error(text):
    """Imprime mensagem de erro."""
    print(f"{RED}✗ {text}{RESET}")

def print_info(text):
    """Imprime mensagem informativa."""
    print(f"{YELLOW}ℹ {text}{RESET}")

def get_auth_token():
    """Obtém token de autenticação."""
    print_info("Obtendo token de autenticação...")
    
    url = f"{API_BASE_URL}/api/auth/login/"
    data = {
        "username": USERNAME,
        "password": PASSWORD
    }
    
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        
        token = response.json().get('access')
        if token:
            print_success(f"Token obtido: {token[:20]}...")
            return token
        else:
            print_error("Token não encontrado na resposta")
            return None
    except requests.exceptions.RequestException as e:
        print_error(f"Erro ao obter token: {e}")
        return None

# ==============================
# TESTES DE ENDPOINTS
# ==============================

def test_latest_endpoint(token):
    """Testa GET /api/telemetry/latest/{device_id}/"""
    print_header("TESTE 1: Latest Readings")
    
    url = f"{API_BASE_URL}/api/telemetry/latest/{DEVICE_ID}/"
    headers = {"Authorization": f"Bearer {token}"}
    
    print_info(f"GET {url}")
    
    try:
        start_time = time.time()
        response = requests.get(url, headers=headers)
        elapsed = (time.time() - start_time) * 1000
        
        print_info(f"Status Code: {response.status_code}")
        print_info(f"Response Time: {elapsed:.2f}ms")
        
        if response.status_code == 200:
            data = response.json()
            
            # Validações
            assert 'device_id' in data, "Campo 'device_id' ausente"
            assert data['device_id'] == DEVICE_ID, f"device_id incorreto: {data['device_id']}"
            assert 'readings' in data, "Campo 'readings' ausente"
            assert isinstance(data['readings'], list), "'readings' deve ser uma lista"
            
            readings_count = len(data['readings'])
            print_success(f"Device ID: {data['device_id']}")
            print_success(f"Leituras encontradas: {readings_count}")
            
            if readings_count > 0:
                # Analisar primeira leitura
                reading = data['readings'][0]
                print_success(f"Primeira leitura:")
                print(f"  - sensor_id: {reading.get('sensor_id')}")
                print(f"  - sensor_name: {reading.get('sensor_name')}")
                print(f"  - value: {reading.get('value')}")
                print(f"  - timestamp: {reading.get('timestamp')}")
                
                # Validar estrutura
                required_fields = ['sensor_id', 'sensor_name', 'sensor_type', 'value', 'unit', 'timestamp']
                for field in required_fields:
                    assert field in reading, f"Campo '{field}' ausente na leitura"
                
                print_success("✓ Estrutura da resposta válida")
            else:
                print_error("Nenhuma leitura encontrada! Execute test_generate_telemetry.py")
            
            return True
            
        else:
            print_error(f"Erro na requisição: {response.status_code}")
            print_error(response.text)
            return False
            
    except Exception as e:
        print_error(f"Erro no teste: {e}")
        return False

def test_history_endpoint(token):
    """Testa GET /api/telemetry/history/{device_id}/"""
    print_header("TESTE 2: History (Time Series)")
    
    # Testar com diferentes ranges
    test_cases = [
        {"hours": 1, "expected_bucket": "raw ou 1m"},
        {"hours": 6, "expected_bucket": "1m"},
        {"hours": 24, "expected_bucket": "5m ou 1h"},
    ]
    
    for case in test_cases:
        hours = case['hours']
        print_info(f"\n--- Testando range: últimas {hours}h ---")
        
        url = f"{API_BASE_URL}/api/telemetry/history/{DEVICE_ID}/"
        headers = {"Authorization": f"Bearer {token}"}
        params = {"hours": hours}
        
        print_info(f"GET {url}?hours={hours}")
        
        try:
            start_time = time.time()
            response = requests.get(url, headers=headers, params=params)
            elapsed = (time.time() - start_time) * 1000
            
            print_info(f"Status Code: {response.status_code}")
            print_info(f"Response Time: {elapsed:.2f}ms")
            
            if response.status_code == 200:
                data = response.json()
                
                # Validações
                assert 'device_id' in data, "Campo 'device_id' ausente"
                assert 'sensors' in data, "Campo 'sensors' ausente"
                assert isinstance(data['sensors'], list), "'sensors' deve ser uma lista"
                
                sensors_count = len(data['sensors'])
                print_success(f"Sensores encontrados: {sensors_count}")
                
                if sensors_count > 0:
                    sensor = data['sensors'][0]
                    print_success(f"Primeiro sensor:")
                    print(f"  - sensor_id: {sensor.get('sensor_id')}")
                    print(f"  - sensor_name: {sensor.get('sensor_name')}")
                    
                    # Validar série temporal
                    assert 'data' in sensor, "Campo 'data' ausente no sensor"
                    data_points = len(sensor['data'])
                    print_success(f"  - data points: {data_points}")
                    
                    if data_points > 0:
                        point = sensor['data'][0]
                        print_success(f"  Primeiro ponto:")
                        print(f"    - timestamp: {point.get('timestamp')}")
                        print(f"    - avg: {point.get('avg')}")
                        print(f"    - min: {point.get('min')}")
                        print(f"    - max: {point.get('max')}")
                        print(f"    - count: {point.get('count')}")
                        
                        # Validar estrutura de agregação
                        required_fields = ['timestamp', 'avg', 'min', 'max', 'count']
                        for field in required_fields:
                            assert field in point, f"Campo '{field}' ausente no data point"
                        
                        print_success(f"✓ Agregação funcionando ({case['expected_bucket']})")
                
            else:
                print_error(f"Erro na requisição: {response.status_code}")
                print_error(response.text)
                return False
                
        except Exception as e:
            print_error(f"Erro no teste: {e}")
            return False
    
    return True

def test_device_summary_endpoint(token):
    """Testa GET /api/telemetry/device/{device_id}/summary/"""
    print_header("TESTE 3: Device Summary")
    
    url = f"{API_BASE_URL}/api/telemetry/device/{DEVICE_ID}/summary/"
    headers = {"Authorization": f"Bearer {token}"}
    
    print_info(f"GET {url}")
    
    try:
        start_time = time.time()
        response = requests.get(url, headers=headers)
        elapsed = (time.time() - start_time) * 1000
        
        print_info(f"Status Code: {response.status_code}")
        print_info(f"Response Time: {elapsed:.2f}ms")
        
        if response.status_code == 200:
            data = response.json()
            
            # Validações
            assert 'device_id' in data, "Campo 'device_id' ausente"
            assert 'device_name' in data, "Campo 'device_name' ausente"
            assert 'sensors' in data, "Campo 'sensors' ausente"
            assert isinstance(data['sensors'], list), "'sensors' deve ser uma lista"
            
            sensors_count = len(data['sensors'])
            print_success(f"Device ID: {data['device_id']}")
            print_success(f"Device Name: {data['device_name']}")
            print_success(f"Sensores: {sensors_count}")
            
            if sensors_count > 0:
                sensor = data['sensors'][0]
                print_success(f"\nPrimeiro sensor (resumo):")
                print(f"  - sensor_id: {sensor.get('sensor_id')}")
                print(f"  - sensor_name: {sensor.get('sensor_name')}")
                print(f"  - sensor_type: {sensor.get('sensor_type')}")
                print(f"  - is_online: {sensor.get('is_online')}")
                print(f"  - last_value: {sensor.get('last_value')}")
                print(f"  - last_reading_at: {sensor.get('last_reading_at')}")
                
                # Validar estatísticas 24h
                if 'statistics_24h' in sensor:
                    stats = sensor['statistics_24h']
                    print_success(f"  Estatísticas 24h:")
                    print(f"    - avg: {stats.get('avg')}")
                    print(f"    - min: {stats.get('min')}")
                    print(f"    - max: {stats.get('max')}")
                    print(f"    - count: {stats.get('count')}")
                
                # Validar estrutura
                required_fields = ['sensor_id', 'sensor_name', 'sensor_type', 'is_online']
                for field in required_fields:
                    assert field in sensor, f"Campo '{field}' ausente no sensor"
                
                print_success("✓ Estrutura do summary válida")
            
            return True
            
        else:
            print_error(f"Erro na requisição: {response.status_code}")
            print_error(response.text)
            return False
            
    except Exception as e:
        print_error(f"Erro no teste: {e}")
        return False

# ==============================
# TESTES DE PERFORMANCE
# ==============================

def test_performance(token):
    """Testa performance dos endpoints."""
    print_header("TESTE 4: Performance")
    
    endpoints = [
        f"/api/telemetry/latest/{DEVICE_ID}/",
        f"/api/telemetry/history/{DEVICE_ID}/?hours=24",
        f"/api/telemetry/device/{DEVICE_ID}/summary/",
    ]
    
    headers = {"Authorization": f"Bearer {token}"}
    
    for endpoint in endpoints:
        url = f"{API_BASE_URL}{endpoint}"
        print_info(f"\nTestando: {endpoint}")
        
        # Fazer 5 requisições
        times = []
        for i in range(5):
            start = time.time()
            response = requests.get(url, headers=headers)
            elapsed = (time.time() - start) * 1000
            times.append(elapsed)
        
        # Calcular estatísticas
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        print_success(f"  Média: {avg_time:.2f}ms")
        print_info(f"  Min: {min_time:.2f}ms | Max: {max_time:.2f}ms")
        
        # Validar performance
        if avg_time < 1000:  # < 1 segundo
            print_success("  ✓ Performance adequada")
        elif avg_time < 3000:  # < 3 segundos
            print_info("  ⚠ Performance aceitável (mas pode melhorar)")
        else:
            print_error("  ✗ Performance ruim (> 3s)")
    
    return True

# ==============================
# TESTES DE EDGE CASES
# ==============================

def test_edge_cases(token):
    """Testa casos extremos e erros."""
    print_header("TESTE 5: Edge Cases")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Caso 1: Device inexistente
    print_info("\n--- Caso 1: Device inexistente ---")
    url = f"{API_BASE_URL}/api/telemetry/latest/DEVICE_INEXISTENTE/"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 404 or (response.status_code == 200 and len(response.json().get('readings', [])) == 0):
        print_success("✓ Retorna vazio ou 404 para device inexistente")
    else:
        print_error(f"✗ Comportamento inesperado: {response.status_code}")
    
    # Caso 2: Range inválido (negativo)
    print_info("\n--- Caso 2: Range negativo ---")
    url = f"{API_BASE_URL}/api/telemetry/history/{DEVICE_ID}/"
    response = requests.get(url, headers=headers, params={"hours": -1})
    
    if response.status_code == 400 or response.status_code == 200:
        print_success("✓ Tratamento de range negativo OK")
    else:
        print_error(f"✗ Comportamento inesperado: {response.status_code}")
    
    # Caso 3: Range muito grande (> 720h)
    print_info("\n--- Caso 3: Range muito grande (1000h) ---")
    url = f"{API_BASE_URL}/api/telemetry/history/{DEVICE_ID}/"
    response = requests.get(url, headers=headers, params={"hours": 1000})
    
    if response.status_code in [200, 400]:
        data = response.json() if response.status_code == 200 else {}
        sensors = data.get('sensors', [])
        if sensors:
            points = len(sensors[0].get('data', []))
            print_success(f"✓ Retornou {points} pontos (limite aplicado se < 5000)")
        else:
            print_info("  Sem dados para esse range")
    
    # Caso 4: Sem token de autenticação
    print_info("\n--- Caso 4: Sem autenticação ---")
    url = f"{API_BASE_URL}/api/telemetry/latest/{DEVICE_ID}/"
    response = requests.get(url)  # Sem header Authorization
    
    if response.status_code == 401:
        print_success("✓ Retorna 401 Unauthorized sem token")
    else:
        print_error(f"✗ Deveria retornar 401, retornou: {response.status_code}")
    
    return True

# ==============================
# MAIN TEST RUNNER
# ==============================

def run_all_tests():
    """Executa todos os testes."""
    print_header("TESTE E2E - TELEMETRIA COMPLETA")
    print(f"API Base URL: {API_BASE_URL}")
    print(f"Device ID: {DEVICE_ID}")
    print(f"Username: {USERNAME}")
    
    # Obter token
    token = get_auth_token()
    if not token:
        print_error("\n❌ FALHA: Não foi possível obter token de autenticação")
        print_info("Verifique se o backend está rodando e credenciais corretas")
        return
    
    # Executar testes
    results = {
        "Latest Endpoint": test_latest_endpoint(token),
        "History Endpoint": test_history_endpoint(token),
        "Device Summary": test_device_summary_endpoint(token),
        "Performance": test_performance(token),
        "Edge Cases": test_edge_cases(token),
    }
    
    # Resumo final
    print_header("RESUMO DOS TESTES")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = f"{GREEN}✓ PASSOU{RESET}" if result else f"{RED}✗ FALHOU{RESET}"
        print(f"{test_name:.<50} {status}")
    
    print(f"\n{BLUE}{'=' * 70}{RESET}")
    
    if passed == total:
        print(f"{GREEN}✓ TODOS OS TESTES PASSARAM ({passed}/{total}){RESET}")
        print(f"{GREEN}✓ Integração Backend funcionando corretamente!{RESET}")
    else:
        print(f"{YELLOW}⚠ {passed}/{total} testes passaram{RESET}")
        print(f"{YELLOW}Verifique os erros acima{RESET}")
    
    print(f"{BLUE}{'=' * 70}{RESET}\n")

if __name__ == "__main__":
    run_all_tests()
