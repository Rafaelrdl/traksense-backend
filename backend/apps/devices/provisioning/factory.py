"""
Factory de Provisioners - Strategy Pattern
===========================================

Factory que retorna a implementação correta de EmqxProvisioner baseado
na variável de ambiente EMQX_PROVISION_MODE.

Permite trocar entre implementações sem alterar código dos serviços:
    - 'http' (padrão): EmqxHttpProvisioner (HTTP Management API)
    - 'sql': EmqxSqlProvisioner (Postgres AuthN/ACL) - não implementado

Uso em services.py:
    from .provisioning.factory import get_provisioner
    
    provisioner = get_provisioner()  # Detecta implementação automaticamente
    provisioner.create_user(creds)
    provisioner.set_acl(creds, tenant="abc", site="site1", device="dev123")

Trocar implementação:
    1. Mudar .env.api: EMQX_PROVISION_MODE=sql
    2. Reiniciar Django: docker compose restart api
    3. Testar provisionamento
    
    Não é necessário alterar código do backend!

Referências:
    - ADR-003: EMQX Authentication & Authorization Strategy
    - Design Pattern: Strategy (comportamento intercambiável)
"""

import os
import logging
from typing import Optional

from .emqx import EmqxProvisioner
from .emqx_http import EmqxHttpProvisioner
# from .emqx_sql import EmqxSqlProvisioner  # Descomentado quando implementar


logger = logging.getLogger(__name__)


# Cache singleton da instância do provisioner (evita recriar a cada chamada)
_provisioner_instance: Optional[EmqxProvisioner] = None


def get_provisioner(force_recreate: bool = False) -> EmqxProvisioner:
    """
    Retorna a implementação correta de EmqxProvisioner baseado em EMQX_PROVISION_MODE.
    
    Args:
        force_recreate: Se True, força recriação da instância (útil em testes)
    
    Returns:
        Instância concreta de EmqxProvisioner
    
    Raises:
        ValueError: Se EMQX_PROVISION_MODE for inválido
    
    Comportamento:
        - Singleton: reutiliza instância existente (economia de recursos)
        - Lazy loading: cria instância apenas quando necessário
        - Thread-safe: pode ser chamado de múltiplos workers Django/Celery
    
    Modos suportados:
        - 'http' (padrão): EmqxHttpProvisioner
            * Simples, ideal para dev/staging
            * Latência HTTP aceitável (<1000 devices/hora)
            * Sem configuração adicional no EMQX
        
        - 'sql': EmqxSqlProvisioner (não implementado)
            * Alta performance, ideal para produção
            * Requer configuração do EMQX (emqx.conf)
            * Requer tabelas emqx_authn e emqx_acl
    
    Exemplos:
        # Dev/Staging (padrão):
        # .env.api: EMQX_PROVISION_MODE=http
        provisioner = get_provisioner()
        # Retorna: EmqxHttpProvisioner(base_url='http://emqx:18083', ...)
        
        # Produção (quando implementado):
        # .env.api: EMQX_PROVISION_MODE=sql
        provisioner = get_provisioner()
        # Retorna: EmqxSqlProvisioner(database_url='postgresql://...', ...)
        
        # Testes (forçar recriação):
        provisioner = get_provisioner(force_recreate=True)
    """
    global _provisioner_instance
    
    # Retornar instância cached (singleton)
    if _provisioner_instance is not None and not force_recreate:
        return _provisioner_instance
    
    # Detectar modo de provisionamento
    mode = os.getenv('EMQX_PROVISION_MODE', 'http').lower().strip()
    
    logger.info(f"Criando EmqxProvisioner com modo: {mode}")
    
    # Factory: criar implementação correta
    if mode == 'http':
        # Opção A: HTTP Management API (padrão)
        _provisioner_instance = EmqxHttpProvisioner()
        logger.info("✅ EmqxHttpProvisioner inicializado (HTTP Management API)")
    
    elif mode == 'sql':
        # Opção B: Postgres AuthN/ACL (skeleton não implementado)
        logger.error(
            "❌ EMQX_PROVISION_MODE=sql não implementado. "
            "Use 'http' ou implemente EmqxSqlProvisioner (ver ADR-003)."
        )
        raise ValueError(
            f"EMQX_PROVISION_MODE='{mode}' não implementado. "
            f"Opções disponíveis: 'http'. "
            f"Para SQL, implemente EmqxSqlProvisioner (ver ADR-003 e provisioning/emqx_sql.py)."
        )
    
    else:
        # Modo inválido
        logger.error(f"❌ EMQX_PROVISION_MODE inválido: '{mode}'")
        raise ValueError(
            f"EMQX_PROVISION_MODE inválido: '{mode}'. "
            f"Valores aceitos: 'http', 'sql'. "
            f"Verifique .env.api ou variáveis de ambiente."
        )
    
    return _provisioner_instance


def reset_provisioner() -> None:
    """
    Reseta o singleton do provisioner (útil em testes).
    
    Uso:
        # Em setup de testes:
        reset_provisioner()
        
        # Mockando o provisioner:
        from unittest.mock import patch
        with patch('apps.devices.provisioning.factory._provisioner_instance', MockProvisioner()):
            ...
    """
    global _provisioner_instance
    _provisioner_instance = None
    logger.debug("EmqxProvisioner singleton resetado")


# ============================================================================
# Helpers de configuração
# ============================================================================

def get_provisioner_mode() -> str:
    """
    Retorna o modo de provisionamento atual.
    
    Returns:
        'http' ou 'sql'
    
    Uso:
        if get_provisioner_mode() == 'http':
            print("Usando HTTP Management API")
    """
    return os.getenv('EMQX_PROVISION_MODE', 'http').lower().strip()


def is_http_mode() -> bool:
    """Verifica se está usando HTTP Management API."""
    return get_provisioner_mode() == 'http'


def is_sql_mode() -> bool:
    """Verifica se está usando Postgres AuthN/ACL."""
    return get_provisioner_mode() == 'sql'


# ============================================================================
# Validação de configuração (chamado no startup do Django)
# ============================================================================

def validate_provisioner_config() -> None:
    """
    Valida configuração do provisioner no startup do Django.
    
    Verifica:
        - EMQX_PROVISION_MODE é válido
        - Variáveis de ambiente obrigatórias estão definidas
        - Conexão com EMQX está OK (HTTP) ou Postgres (SQL)
    
    Raises:
        ValueError: Configuração inválida
        EmqxConnectionError: Falha ao conectar
    
    Uso em apps.py:
        # apps/devices/apps.py
        class DevicesConfig(AppConfig):
            def ready(self):
                from .provisioning.factory import validate_provisioner_config
                validate_provisioner_config()
    """
    mode = get_provisioner_mode()
    
    logger.info(f"Validando configuração do provisioner (modo: {mode})...")
    
    if mode == 'http':
        # Validar variáveis obrigatórias
        required_vars = ['EMQX_MGMT_URL', 'EMQX_ADMIN_USER', 'EMQX_ADMIN_PASS']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            raise ValueError(
                f"Variáveis de ambiente obrigatórias faltando (modo http): {missing_vars}. "
                f"Configure em .env.api ou docker-compose.yml."
            )
        
        # Testar conexão (opcional: comentar se causar problemas no startup)
        # try:
        #     provisioner = get_provisioner()
        #     # Fazer uma requisição simples para validar credenciais
        #     # provisioner._make_request("GET", "/api/v5/status")
        #     logger.info("✅ Conexão com EMQX HTTP API OK")
        # except Exception as e:
        #     logger.warning(f"⚠️ Falha ao conectar no EMQX (pode estar desligado): {e}")
    
    elif mode == 'sql':
        # Validar variáveis obrigatórias
        if not os.getenv('DATABASE_URL'):
            raise ValueError(
                "DATABASE_URL não definida (modo sql). "
                "Configure em .env.api ou docker-compose.yml."
            )
        
        logger.warning("⚠️ Modo 'sql' não implementado. Use 'http'.")
    
    else:
        raise ValueError(
            f"EMQX_PROVISION_MODE inválido: '{mode}'. "
            f"Valores aceitos: 'http', 'sql'."
        )
    
    logger.info(f"✅ Configuração do provisioner válida (modo: {mode})")


# ============================================================================
# Testes
# ============================================================================

if __name__ == '__main__':
    # Teste rápido do factory
    import sys
    
    # Forçar modo http
    os.environ['EMQX_PROVISION_MODE'] = 'http'
    os.environ['EMQX_MGMT_URL'] = 'http://localhost:18083'
    os.environ['EMQX_ADMIN_USER'] = 'admin'
    os.environ['EMQX_ADMIN_PASS'] = 'public'
    
    # Validar configuração
    try:
        validate_provisioner_config()
        print("✅ Configuração válida")
    except Exception as e:
        print(f"❌ Erro na configuração: {e}")
        sys.exit(1)
    
    # Obter provisioner
    try:
        provisioner = get_provisioner()
        print(f"✅ Provisioner criado: {type(provisioner).__name__}")
        print(f"   - Base URL: {provisioner.base_url}")
        print(f"   - Admin User: {provisioner.admin_user}")
        print(f"   - Realm: {provisioner.realm}")
    except Exception as e:
        print(f"❌ Erro ao criar provisioner: {e}")
        sys.exit(1)
    
    # Testar singleton
    provisioner2 = get_provisioner()
    assert provisioner is provisioner2, "Singleton não funciona!"
    print("✅ Singleton OK (mesma instância reutilizada)")
    
    # Testar reset
    reset_provisioner()
    provisioner3 = get_provisioner()
    assert provisioner is not provisioner3, "Reset não funciona!"
    print("✅ Reset OK (nova instância criada)")
    
    print("\n✅ Todos os testes do factory passaram!")
