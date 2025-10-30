"""
Script para testar endpoint de histórico de telemetria
Verifica se o endpoint /api/telemetry/history/<device_id>/ está retornando dados
"""

import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"
DEVICE_ID = "4b686f6d70107115"

# Calcular período (últimas 24h)
end = datetime.now()
start = end - timedelta(hours=24)

# Montar URL
url = f"{BASE_URL}/api/telemetry/history/{DEVICE_ID}/"
params = {
    'start': start.isoformat(),
    'end': end.isoformat()
}

headers = {
    'Host': 'umc.localhost'
}

print("=" * 60)
print("🔍 TESTE: Endpoint de Histórico de Telemetria")
print("=" * 60)
print(f"\n📡 URL: {url}")
print(f"📅 Período: {start.strftime('%Y-%m-%d %H:%M')} até {end.strftime('%Y-%m-%d %H:%M')}")
print(f"🏢 Tenant: umc")
print(f"🔧 Device ID: {DEVICE_ID}")

try:
    response = requests.get(url, params=params, headers=headers)
    print(f"\n✅ Status HTTP: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        
        print(f"\n📊 Resposta da API:")
        print(f"   Device ID: {data.get('deviceId', 'N/A')}")
        print(f"   Agregação: {data.get('aggregation', 'N/A')}")
        print(f"   Período Start: {data.get('period', {}).get('start', 'N/A')}")
        print(f"   Período End: {data.get('period', {}).get('end', 'N/A')}")
        print(f"   Número de séries: {len(data.get('series', []))}")
        
        series_list = data.get('series', [])
        
        if len(series_list) == 0:
            print("\n⚠️  AVISO: Nenhuma série retornada!")
            print("   Possíveis causas:")
            print("   1. Não há dados no banco para este device")
            print("   2. Período de consulta não contém dados")
            print("   3. Device ID está incorreto")
        else:
            for i, series in enumerate(series_list):
                print(f"\n{'='*60}")
                print(f"📈 Série {i+1}/{len(series_list)}")
                print(f"{'='*60}")
                print(f"   Sensor ID: {series.get('sensorId', 'N/A')}")
                print(f"   Sensor Name: {series.get('sensorName', 'N/A')}")
                print(f"   Sensor Type: {series.get('sensorType', 'N/A')}")
                print(f"   Metric Type: {series.get('metricType', 'N/A')}")
                print(f"   Unit: {series.get('unit', 'N/A')}")
                print(f"   Número de pontos: {len(series.get('data', []))}")
                
                data_points = series.get('data', [])
                
                if len(data_points) > 0:
                    print(f"\n   📍 Primeiro ponto:")
                    first = data_points[0]
                    print(f"      Timestamp: {first.get('timestamp')}")
                    print(f"      Avg: {first.get('avg')}")
                    print(f"      Min: {first.get('min')}")
                    print(f"      Max: {first.get('max')}")
                    print(f"      Count: {first.get('count')}")
                    
                    print(f"\n   📍 Último ponto:")
                    last = data_points[-1]
                    print(f"      Timestamp: {last.get('timestamp')}")
                    print(f"      Avg: {last.get('avg')}")
                    print(f"      Min: {last.get('min')}")
                    print(f"      Max: {last.get('max')}")
                    print(f"      Count: {last.get('count')}")
                    
                    print(f"\n   📊 Exemplo de 3 pontos intermediários:")
                    for point in data_points[len(data_points)//4:len(data_points)//4+3]:
                        print(f"      {point.get('timestamp')} -> avg: {point.get('avg')}")
                else:
                    print(f"\n   ⚠️  Array 'data' está vazio!")
        
        # Salvar resposta completa em arquivo
        with open('telemetry_response.json', 'w') as f:
            json.dump(data, f, indent=2)
        print(f"\n💾 Resposta completa salva em: telemetry_response.json")
        
    elif response.status_code == 404:
        print(f"\n❌ ERRO 404: Endpoint não encontrado")
        print(f"   URL testada: {url}")
        print(f"   Verifique se o endpoint está configurado nas URLs")
        
    elif response.status_code == 500:
        print(f"\n❌ ERRO 500: Erro interno do servidor")
        print(f"   Response: {response.text[:500]}")
        
    else:
        print(f"\n❌ ERRO {response.status_code}")
        print(f"   Response: {response.text[:500]}")
        
except requests.exceptions.ConnectionError:
    print(f"\n❌ ERRO DE CONEXÃO")
    print(f"   Não foi possível conectar ao backend")
    print(f"   Verifique se o container Docker está rodando")
    print(f"   Comando: docker ps | grep traksense")
    
except Exception as e:
    print(f"\n❌ EXCEÇÃO: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("✅ Teste concluído!")
print("="*60)
