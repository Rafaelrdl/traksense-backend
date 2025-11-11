"""
Generate HMAC token from actual body received in logs

Este script lê o body EXATO dos logs do backend e gera o token correto.

Usage:
    1. Copie o body dos logs (linha com b'...')
    2. Execute: python scripts/utils/generate_token_from_log.py

Example:
    python scripts/utils/generate_token_from_log.py
"""

import hmac
import hashlib
from pathlib import Path

def load_ingestion_secret():
    """Load INGESTION_SECRET from .env file"""
    env_path = Path(__file__).parent.parent.parent / '.env'
    
    if not env_path.exists():
        print("❌ Erro: arquivo .env não encontrado!")
        return None
    
    with open(env_path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith('INGESTION_SECRET='):
                secret = line.split('=', 1)[1].strip()
                if secret and secret != 'change-me-generate-with-secrets-token-hex-32':
                    return secret
    
    print("❌ Erro: INGESTION_SECRET não configurado no .env!")
    return None


def main():
    # Body EXATO dos logs (copie daqui e cole o body dos seus logs)
    body_from_log = b'{"ts":1762883583811,"topic":"tenants/umc/sites/Uberl\xc3\xa2ndia Medical Center/assets/CHILLER-001/telemetry","payload":"[{\\"bn\\": \\"F80332010002C873\\", \\"bt\\": 1762883583}, {\\"n\\": \\"rssi\\", \\"u\\": \\"dBW\\", \\"v\\": -48}, {\\"n\\": \\"snr\\", \\"u\\": \\"dB\\", \\"v\\": 14.800000000000001}, {\\"n\\": \\"model\\", \\"vs\\": \\"nit21li\\"}, {\\"n\\": \\"battery\\", \\"u\\": \\"V\\", \\"v\\": 3.0}, {\\"n\\": \\"version\\", \\"vs\\": \\"3.0.3.0\\"}, {\\"n\\": \\"temperatura_ambiente\\", \\"u\\": \\"Cel\\", \\"v\\": 27.189999999999998}, {\\"n\\": \\"humidade_ambiente\\", \\"u\\": \\"%RH\\", \\"v\\": 56.0}, {\\"n\\": \\"temperatura_saida\\", \\"u\\": \\"Cel\\", \\"v\\": 5.1200000000000045}, {\\"n\\": \\"temperatura_retorno\\", \\"u\\": \\"Cel\\", \\"v\\": 36.25}, {\\"n\\": \\"gateway\\", \\"vs\\": \\"F8033202CB040000\\"}]","client_id":"publisher_f8033202cb04"}'
    
    secret = load_ingestion_secret()
    if not secret:
        return
    
    # Gerar token HMAC
    token = hmac.new(
        secret.encode('utf-8'),
        body_from_log,
        hashlib.sha256
    ).hexdigest()
    
    print("=" * 80)
    print("🔐 Token HMAC Correto (baseado no body real dos logs)")
    print("=" * 80)
    print(f"\n📏 Body tamanho: {len(body_from_log)} bytes")
    print(f"\n📋 Body (primeiros 200 chars):")
    print(f"   {body_from_log[:200]}...")
    print(f"\n🔑 Token correto (x-device-token):")
    print(f"   {token}")
    print(f"\n📌 Use este token no MQTTX!")
    print("=" * 80)
    print(f"\n⚠️  PROBLEMA IDENTIFICADO:")
    print(f"   O MQTTX está ADICIONANDO campos ao payload:")
    print(f"   - ts (timestamp)")
    print(f"   - client_id")
    print(f"   - payload já vem serializado como string (não objeto)")
    print(f"\n💡 SOLUÇÃO:")
    print(f"   O token HMAC deve ser gerado DEPOIS do MQTTX adicionar esses campos.")
    print(f"   Isso significa que você NÃO pode pré-gerar o token!")
    print(f"\n🔧 ALTERNATIVAS:")
    print(f"   1. Configure o EMQX para NÃO adicionar campos extras")
    print(f"   2. Use autenticação por device token registrado (não HMAC)")
    print(f"   3. Desabilite temporariamente validação HMAC no backend")
    print("=" * 80)


if __name__ == '__main__':
    main()
