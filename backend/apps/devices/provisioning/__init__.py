"""
Abstração de Provisionamento EMQX - Interface Strategy Pattern
================================================================

Este módulo define a interface para provisionamento de dispositivos IoT no broker EMQX.
A implementação real pode ser via HTTP Management API (dev/staging) ou Postgres AuthN/ACL (prod).

Strategy Pattern permite trocar entre implementações sem alterar o código dos serviços.

Uso:
    from .factory import get_provisioner
    from .emqx import EmqxCredentials
    
    provisioner = get_provisioner()  # Retorna implementação conforme EMQX_PROVISION_MODE
    
    creds = EmqxCredentials(
        username="t:tenant-uuid:d:device-uuid",
        password=secrets.token_urlsafe(20),
        client_id="ts-1a2b3c4d-9f8e7d6c-11aa"
    )
    
    provisioner.create_user(creds)
    provisioner.set_acl(creds, tenant="abc", site="site1", device="dev123")

Referências:
    - ADR-003: EMQX Authentication & Authorization Strategy
    - EMQX v5 Management API: https://docs.emqx.com/en/emqx/v5.0/admin/api.html
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class EmqxCredentials:
    """
    Credenciais MQTT para um dispositivo IoT.
    
    Attributes:
        username: Identificador único do device (formato: t:<tenant_uuid>:d:<device_uuid>)
        password: Senha segura gerada (mínimo 20 chars; em prod deve ser cifrada ao armazenar)
        client_id: ClientID único para rastreabilidade (formato: ts-<tenant_short>-<device_short>-<random>)
    
    Exemplo:
        EmqxCredentials(
            username="t:1a2b3c4d-5e6f-7g8h-9i0j-k1l2m3n4o5p6:d:9f8e7d6c-5b4a-3210-fedc-ba0987654321",
            password="Xy9Kp2Lm4Nq6Rs8Tv0Uw",
            client_id="ts-1a2b3c4d-9f8e7d6c-a1b2c3d4"
        )
    """
    username: str
    password: str
    client_id: str


class EmqxProvisioner(ABC):
    """
    Interface abstrata para provisionamento de dispositivos no EMQX.
    
    Implementações concretas:
        - EmqxHttpProvisioner: usa HTTP Management API (Opção A - padrão)
        - EmqxSqlProvisioner: usa Postgres AuthN/ACL (Opção B - alternativa)
    
    Princípios de segurança:
        - Mínimo privilégio: ACL restrita apenas aos tópicos do próprio device
        - Sem wildcards perigosos: nunca usar # ou + fora do prefixo do device
        - Isolamento multi-tenant: cada device só acessa seus próprios tópicos
    
    Tópicos permitidos:
        - Publish: traksense/{tenant}/{site}/{device}/(state|telem|event|alarm|ack)
        - Subscribe: traksense/{tenant}/{site}/{device}/cmd
    
    Exemplo de uso:
        provisioner = get_provisioner()
        
        # 1. Criar usuário no EMQX
        provisioner.create_user(creds)
        
        # 2. Configurar ACL mínima
        provisioner.set_acl(creds, tenant="abc", site="site1", device="dev123")
        
        # 3. Revogar acesso (opcional)
        provisioner.delete_user(creds.username)
    """
    
    @abstractmethod
    def create_user(self, creds: EmqxCredentials) -> None:
        """
        Cria ou atualiza usuário no sistema de autenticação do EMQX.
        
        Args:
            creds: Credenciais do dispositivo (username, password, client_id)
        
        Raises:
            EmqxProvisioningError: Falha ao criar usuário (rede, autenticação, etc.)
        
        Comportamento:
            - Idempotente: pode ser chamado múltiplas vezes sem efeito colateral
            - Em caso de usuário existente, deve atualizar a senha
            - Deve logar a operação para auditoria
        
        Implementação HTTP:
            POST /api/v5/authentication/{realm}/users
            Body: {"user_id": username, "password": password}
        
        Implementação SQL:
            INSERT INTO emqx_authn (username, password_hash, salt)
            ON CONFLICT (username) DO UPDATE SET password_hash = ..., salt = ...
        """
        pass
    
    @abstractmethod
    def set_acl(
        self,
        creds: EmqxCredentials,
        tenant: str,
        site: str,
        device: str
    ) -> None:
        """
        Configura regras de ACL (Authorization) mínimas para o dispositivo.
        
        Args:
            creds: Credenciais do dispositivo
            tenant: UUID ou slug do tenant
            site: Slug do site
            device: UUID ou slug do device
        
        Raises:
            EmqxProvisioningError: Falha ao configurar ACL
        
        Comportamento:
            - Remove ACLs antigas do usuário (se existirem)
            - Cria apenas as regras necessárias (princípio do mínimo privilégio)
            - Nunca usar wildcards # ou + fora do prefixo do device
        
        Regras criadas:
            - ALLOW publish: traksense/{tenant}/{site}/{device}/state
            - ALLOW publish: traksense/{tenant}/{site}/{device}/telem
            - ALLOW publish: traksense/{tenant}/{site}/{device}/event
            - ALLOW publish: traksense/{tenant}/{site}/{device}/alarm
            - ALLOW publish: traksense/{tenant}/{site}/{device}/ack
            - ALLOW subscribe: traksense/{tenant}/{site}/{device}/cmd
        
        Exemplo:
            provisioner.set_acl(
                creds,
                tenant="1a2b3c4d-5e6f-7g8h-9i0j-k1l2m3n4o5p6",
                site="factory-sp",
                device="9f8e7d6c-5b4a-3210-fedc-ba0987654321"
            )
            # Resultado: device só acessa traksense/1a2b.../factory-sp/9f8e.../...
        """
        pass
    
    @abstractmethod
    def delete_user(self, username: str) -> None:
        """
        Remove usuário e suas ACLs do EMQX.
        
        Args:
            username: Username do dispositivo (formato: t:<tenant>:d:<device>)
        
        Raises:
            EmqxProvisioningError: Falha ao deletar usuário
        
        Comportamento:
            - Idempotente: não falha se usuário não existir
            - Remove ACLs automaticamente (cascade)
            - Desconecta cliente MQTT se estiver conectado
            - Logar operação para auditoria
        
        Uso:
            # Ao deletar um Device no Django:
            provisioner.delete_user(device.credentials_id)
        """
        pass
    
    def validate_credentials(self, creds: EmqxCredentials) -> None:
        """
        Valida formato das credenciais antes de provisionar.
        
        Args:
            creds: Credenciais a validar
        
        Raises:
            ValueError: Credenciais inválidas
        
        Validações:
            - Username não vazio e formato correto (t:<tenant>:d:<device>)
            - Password com mínimo 16 caracteres
            - ClientID único e sem caracteres inválidos (espaços, #, +, /)
        """
        if not creds.username or not creds.username.startswith("t:"):
            raise ValueError(f"Username inválido: {creds.username} (deve ser formato t:<tenant>:d:<device>)")
        
        if not creds.password or len(creds.password) < 16:
            raise ValueError("Password deve ter no mínimo 16 caracteres")
        
        if not creds.client_id or not creds.client_id.startswith("ts-"):
            raise ValueError(f"ClientID inválido: {creds.client_id} (deve começar com ts-)")
        
        # Caracteres proibidos em ClientID (MQTT spec)
        invalid_chars = [' ', '#', '+', '/', '\x00']
        for char in invalid_chars:
            if char in creds.client_id:
                raise ValueError(f"ClientID contém caractere inválido: '{char}'")


class EmqxProvisioningError(Exception):
    """
    Exceção base para erros de provisionamento EMQX.
    
    Subclasses:
        - EmqxConnectionError: Falha ao conectar no EMQX (rede, timeout)
        - EmqxAuthenticationError: Credenciais de admin inválidas
        - EmqxValidationError: Dados de entrada inválidos
        - EmqxConflictError: Recurso já existe (não idempotente)
    """
    pass


class EmqxConnectionError(EmqxProvisioningError):
    """Falha de conexão com EMQX (rede, timeout, serviço indisponível)"""
    pass


class EmqxAuthenticationError(EmqxProvisioningError):
    """Credenciais de admin do EMQX inválidas ou expiradas"""
    pass


class EmqxValidationError(EmqxProvisioningError):
    """Dados de entrada inválidos (formato username/password/topic incorreto)"""
    pass


class EmqxConflictError(EmqxProvisioningError):
    """Recurso já existe e operação não é idempotente"""
    pass
