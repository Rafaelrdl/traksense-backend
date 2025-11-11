"""
Generate HMAC token for MQTTX testing

Este script gera tokens HMAC SHA256 para autenticação no endpoint /ingest.
O token é baseado no payload exato que será enviado.

Usage:
    python scripts/utils/generate_mqtt_token.py <payload_json>

Examples:
    # Payload vazio (teste básico)
    python scripts/utils/generate_mqtt_token.py '{}'
    
    # Payload com telemetria
    python scripts/utils/generate_mqtt_token.py '{"topic": "tenants/umc/sites/Site1/assets/ASSET-001/telemetry", "payload": {"temp": 25.5}}'
    
    # Payload complexo
    python scripts/utils/generate_mqtt_token.py '{"topic": "tenants/umc/sites/Uberlândia Medical Center/assets/CHILLER-001/telemetry", "payload": {"sensor_14": 77.0, "sensor_15": 25.2}}'

Note:
    - O token muda se o payload mudar (mesmo um espaço a mais!)
    - Use o mesmo payload no MQTTX que você usou para gerar o token
    - O INGESTION_SECRET deve estar configurado no .env
"""

import sys
import hmac
import hashlib
from pathlib import Path


def load_ingestion_secret():
    """Load INGESTION_SECRET from .env file"""
    env_path = Path(__file__).parent.parent.parent / '.env'
    
    if not env_path.exists():
        print("❌ Erro: arquivo .env não encontrado!")
        print(f"   Procurado em: {env_path}")
        print("\n💡 Solução:")
        print("   1. Gere um secret: python -c \"import secrets; print(secrets.token_hex(32))\"")
        print("   2. Adicione ao .env: INGESTION_SECRET=<secret_gerado>")
        sys.exit(1)
    
    with open(env_path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith('INGESTION_SECRET='):
                secret = line.split('=', 1)[1].strip()
                if secret and secret != 'change-me-generate-with-secrets-token-hex-32':
                    return secret
    
    print("❌ Erro: INGESTION_SECRET não configurado no .env!")
    print("\n💡 Solução:")
    print("   1. Gere um secret:")
    print("      python -c \"import secrets; print(secrets.token_hex(32))\"")
    print("\n   2. Adicione ao .env:")
    print("      INGESTION_SECRET=<secret_gerado>")
    print("\n   3. Reinicie o backend:")
    print("      docker-compose -f docker/docker-compose.yml restart api")
    sys.exit(1)


def generate_token(payload: str, secret: str) -> str:
    """Generate HMAC SHA256 token for payload"""
    return hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()


def main():
    if len(sys.argv) < 2:
        print("❌ Erro: Payload não fornecido!")
        print("\n📖 Uso:")
        print("   python scripts/utils/generate_mqtt_token.py '<json_payload>'")
        print("\n📝 Exemplos:")
        print("   # Payload vazio")
        print("   python scripts/utils/generate_mqtt_token.py '{}'")
        print("\n   # Payload com telemetria")
        print("   python scripts/utils/generate_mqtt_token.py '{\"topic\": \"test\", \"payload\": {\"temp\": 25}}'")
        sys.exit(1)
    
    payload = sys.argv[1]
    secret = load_ingestion_secret()
    token = generate_token(payload, secret)
    
    print("=" * 70)
    print("🔐 Token HMAC SHA256 Gerado")
    print("=" * 70)
    print(f"\n📋 Payload (string):")
    print(f"   {payload}")
    print(f"\n� Payload (bytes - usado no HMAC):")
    print(f"   {payload.encode('utf-8')}")
    print(f"\n📊 Tamanho: {len(payload)} caracteres, {len(payload.encode('utf-8'))} bytes")
    print(f"\n�🔑 Token (x-device-token):")
    print(f"   {token}")
    print(f"\n📌 Headers para MQTTX:")
    print(f"   Content-Type: application/json")
    print(f"   x-tenant: umc")
    print(f"   x-device-token: {token}")
    print(f"\n⚠️  IMPORTANTE:")
    print(f"   - Use o MESMO payload no MQTTX (byte a byte)")
    print(f"   - Se mudar o payload, gere novo token!")
    print(f"\n🐛 DEBUG - Para validar no backend:")
    print(f"   Adicione em settings/base.py: DEBUG = True")
    print(f"   Backend vai logar o body recebido para comparação")
    print("=" * 70)


if __name__ == '__main__':
    main()
