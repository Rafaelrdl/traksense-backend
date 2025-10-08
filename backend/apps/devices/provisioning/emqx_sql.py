"""
EMQX PostgreSQL Authentication & Authorization Provisioner - Opção B (Alternativa)
=====================================================================================

⚠️ **IMPORTANTE: Esta implementação é um SKELETON (esqueleto) não funcional.**
⚠️ **Requer configuração adicional do EMQX para AuthN/AuthZ via Postgres.**

Vantagens sobre HTTP API:
    - Performance: Baixa latência (acesso direto ao DB)
    - Escalabilidade: Suporta milhões de devices
    - Transacional: Provisionamento atômico (credencial + ACL na mesma transação)
    - Produção: Ideal para alta carga

Desvantagens:
    - Complexidade: Requer schema adicional e configuração do EMQX
    - Acoplamento: Backend precisa conhecer estrutura interna do EMQX
    - Manutenção: Alterações no schema do EMQX exigem migrations

Quando usar:
    - Provisionamento de >1000 devices/hora
    - Latência HTTP causando timeouts frequentes
    - EMQX Management API se tornando gargalo

Setup necessário:
    1. Criar tabelas emqx_authn e emqx_acl (ver SQL abaixo)
    2. Configurar EMQX para ler dessas tabelas (emqx.conf ou dashboard)
    3. Definir EMQX_PROVISION_MODE=sql no .env.api
    4. Completar métodos TODO abaixo

Uso:
    from .factory import get_provisioner
    
    # .env.api: EMQX_PROVISION_MODE=sql
    provisioner = get_provisioner()  # Retorna EmqxSqlProvisioner
    
    provisioner.create_user(creds)
    provisioner.set_acl(creds, tenant="abc", site="site1", device="dev123")

Referências:
    - EMQX PostgreSQL AuthN: https://docs.emqx.com/en/emqx/v5.0/access-control/authn/postgresql.html
    - EMQX PostgreSQL AuthZ: https://docs.emqx.com/en/emqx/v5.0/access-control/authz/postgresql.html
    - ADR-003: EMQX Authentication & Authorization Strategy
"""

import os
import logging
import hashlib
import secrets
from typing import Optional

# TODO: Instalar dependência psycopg2-binary no requirements.txt
# import psycopg2
# from psycopg2.extras import RealDictCursor

from .emqx import (
    EmqxProvisioner,
    EmqxCredentials,
    EmqxProvisioningError,
    EmqxConnectionError,
    EmqxValidationError,
)


logger = logging.getLogger(__name__)


# ============================================================================
# SQL Schema (a ser criado no Postgres usado pelo EMQX)
# ============================================================================
"""
-- Tabela de autenticação (usuário/senha)
CREATE TABLE IF NOT EXISTS emqx_authn (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    salt VARCHAR(64),
    is_superuser BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_emqx_authn_username ON emqx_authn(username);

-- Tabela de autorização (ACL)
CREATE TABLE IF NOT EXISTS emqx_acl (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    permission VARCHAR(10) CHECK (permission IN ('allow', 'deny')),
    action VARCHAR(20) CHECK (action IN ('publish', 'subscribe', 'all')),
    topic VARCHAR(512) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(username, action, topic)
);

CREATE INDEX idx_emqx_acl_username ON emqx_acl(username);
CREATE INDEX idx_emqx_acl_username_action ON emqx_acl(username, action);

-- Função para atualizar updated_at automaticamente
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
   NEW.updated_at = NOW();
   RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_emqx_authn_updated_at
BEFORE UPDATE ON emqx_authn
FOR EACH ROW
EXECUTE FUNCTION update_modified_column();
"""

# ============================================================================
# Configuração EMQX (emqx.conf ou dashboard)
# ============================================================================
"""
## Configurar EMQX para usar Postgres AuthN/AuthZ

# Via arquivo emqx.conf (editar infra/emqx/emqx.conf):

authentication {
  enable = true
  backend = "postgresql"
  mechanism = "password_based"
  
  server = "db:5432"
  database = "traksense"
  username = "postgres"
  password = "postgres"
  
  password_hash_algorithm {
    name = "sha256"
    salt_position = "suffix"  # salt após password
  }
  
  query = "SELECT password_hash AS password_hash, salt FROM emqx_authn WHERE username = ${username} LIMIT 1"
}

authorization {
  sources = [
    {
      type = "postgresql"
      enable = true
      
      server = "db:5432"
      database = "traksense"
      username = "postgres"
      password = "postgres"
      
      query = "SELECT permission, action, topic FROM emqx_acl WHERE username = ${username}"
    }
  ]
  
  # Ordem de checagem: PostgreSQL → built-in cache
  cache {
    enable = true
    max_size = 1024
    ttl = "1m"
  }
  
  # Negar tudo por padrão (whitelist approach)
  no_match = "deny"
}

# Reiniciar EMQX após configurar:
# docker compose restart emqx
"""


class EmqxSqlProvisioner(EmqxProvisioner):
    """
    ⚠️ SKELETON NÃO FUNCIONAL - Requer implementação completa.
    
    Provisionador EMQX via Postgres AuthN/ACL.
    
    Configuração via variáveis de ambiente:
        - DATABASE_URL: String de conexão Postgres (mesmo do Django)
        - EMQX_HASH_ALGORITHM: Algoritmo de hash (padrão: sha256)
    
    TODOs para implementação:
        1. Instalar psycopg2-binary no requirements.txt
        2. Criar tabelas emqx_authn e emqx_acl no Postgres
        3. Configurar EMQX para ler dessas tabelas (emqx.conf)
        4. Implementar métodos create_user, set_acl, delete_user
        5. Testar isolamento de ACL (devices não acessam tópicos de outros)
    """
    
    def __init__(
        self,
        database_url: Optional[str] = None,
        hash_algorithm: str = "sha256",
    ):
        """
        Inicializa provisionador SQL.
        
        Args:
            database_url: String de conexão Postgres (ex: postgresql://user:pass@host:port/db)
            hash_algorithm: Algoritmo de hash de senha (sha256, bcrypt, pbkdf2)
        """
        self.database_url = database_url or os.getenv('DATABASE_URL')
        self.hash_algorithm = hash_algorithm
        
        # TODO: Conectar no Postgres
        # self.conn = psycopg2.connect(self.database_url)
        
        logger.warning(
            "⚠️ EmqxSqlProvisioner é um SKELETON não funcional. "
            "Requer configuração adicional do EMQX e implementação dos métodos."
        )
        
        raise NotImplementedError(
            "EmqxSqlProvisioner não implementado. Use EmqxHttpProvisioner (EMQX_PROVISION_MODE=http) "
            "ou implemente os TODOs abaixo. Consulte ADR-003 para detalhes."
        )
    
    def _hash_password(self, password: str, salt: Optional[str] = None) -> tuple[str, str]:
        """
        Gera hash da senha compatível com EMQX.
        
        Args:
            password: Senha plain-text
            salt: Salt (gerar se None)
        
        Returns:
            Tupla (password_hash, salt)
        
        Algoritmos suportados:
            - sha256: SHA-256 com salt
            - bcrypt: bcrypt (requer bcrypt lib)
            - pbkdf2: PBKDF2-HMAC-SHA256
        """
        if salt is None:
            salt = secrets.token_hex(16)  # 32 caracteres hex
        
        if self.hash_algorithm == "sha256":
            # SHA-256 com salt (salt_position=suffix no EMQX)
            hash_input = f"{password}{salt}".encode('utf-8')
            password_hash = hashlib.sha256(hash_input).hexdigest()
        
        elif self.hash_algorithm == "bcrypt":
            # TODO: import bcrypt
            # password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            raise NotImplementedError("bcrypt não implementado")
        
        elif self.hash_algorithm == "pbkdf2":
            # TODO: usar hashlib.pbkdf2_hmac
            raise NotImplementedError("pbkdf2 não implementado")
        
        else:
            raise ValueError(f"Algoritmo de hash não suportado: {self.hash_algorithm}")
        
        return password_hash, salt
    
    def create_user(self, creds: EmqxCredentials) -> None:
        """
        TODO: Implementar criação de usuário na tabela emqx_authn.
        
        SQL esperado:
            INSERT INTO emqx_authn (username, password_hash, salt, is_superuser)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (username) DO UPDATE
            SET password_hash = EXCLUDED.password_hash, salt = EXCLUDED.salt, updated_at = NOW();
        
        Args:
            creds: Credenciais do dispositivo
        """
        self.validate_credentials(creds)
        
        # TODO: Implementar
        # password_hash, salt = self._hash_password(creds.password)
        # 
        # with self.conn.cursor() as cur:
        #     cur.execute(
        #         """
        #         INSERT INTO emqx_authn (username, password_hash, salt, is_superuser)
        #         VALUES (%s, %s, %s, %s)
        #         ON CONFLICT (username) DO UPDATE
        #         SET password_hash = EXCLUDED.password_hash, salt = EXCLUDED.salt, updated_at = NOW()
        #         """,
        #         (creds.username, password_hash, salt, False)
        #     )
        #     self.conn.commit()
        # 
        # logger.info(f"✅ Usuário EMQX criado (SQL): {creds.username}")
        
        raise NotImplementedError("create_user não implementado no EmqxSqlProvisioner")
    
    def set_acl(
        self,
        creds: EmqxCredentials,
        tenant: str,
        site: str,
        device: str
    ) -> None:
        """
        TODO: Implementar criação de ACLs na tabela emqx_acl.
        
        SQL esperado:
            DELETE FROM emqx_acl WHERE username = %s;  -- Cleanup
            
            INSERT INTO emqx_acl (username, permission, action, topic)
            VALUES
                (%s, 'allow', 'publish', 'traksense/{tenant}/{site}/{device}/state'),
                (%s, 'allow', 'publish', 'traksense/{tenant}/{site}/{device}/telem'),
                (%s, 'allow', 'publish', 'traksense/{tenant}/{site}/{device}/event'),
                (%s, 'allow', 'publish', 'traksense/{tenant}/{site}/{device}/alarm'),
                (%s, 'allow', 'publish', 'traksense/{tenant}/{site}/{device}/ack'),
                (%s, 'allow', 'subscribe', 'traksense/{tenant}/{site}/{device}/cmd')
            ON CONFLICT (username, action, topic) DO NOTHING;
        
        Args:
            creds: Credenciais do dispositivo
            tenant: UUID ou slug do tenant
            site: Slug do site
            device: UUID ou slug do device
        """
        topic_base = f"traksense/{tenant}/{site}/{device}"
        
        # TODO: Implementar
        # rules = [
        #     (creds.username, 'allow', 'publish', f"{topic_base}/state"),
        #     (creds.username, 'allow', 'publish', f"{topic_base}/telem"),
        #     (creds.username, 'allow', 'publish', f"{topic_base}/event"),
        #     (creds.username, 'allow', 'publish', f"{topic_base}/alarm"),
        #     (creds.username, 'allow', 'publish', f"{topic_base}/ack"),
        #     (creds.username, 'allow', 'subscribe', f"{topic_base}/cmd"),
        # ]
        # 
        # with self.conn.cursor() as cur:
        #     # Cleanup: deletar ACLs antigas
        #     cur.execute("DELETE FROM emqx_acl WHERE username = %s", (creds.username,))
        #     
        #     # Criar novas ACLs
        #     cur.executemany(
        #         """
        #         INSERT INTO emqx_acl (username, permission, action, topic)
        #         VALUES (%s, %s, %s, %s)
        #         ON CONFLICT (username, action, topic) DO NOTHING
        #         """,
        #         rules
        #     )
        #     self.conn.commit()
        # 
        # logger.info(f"✅ ACL configurada (SQL) para {creds.username}: {len(rules)} regras")
        
        raise NotImplementedError("set_acl não implementado no EmqxSqlProvisioner")
    
    def delete_user(self, username: str) -> None:
        """
        TODO: Implementar remoção de usuário e ACLs.
        
        SQL esperado:
            DELETE FROM emqx_acl WHERE username = %s;
            DELETE FROM emqx_authn WHERE username = %s;
        
        Args:
            username: Username do dispositivo
        """
        # TODO: Implementar
        # with self.conn.cursor() as cur:
        #     cur.execute("DELETE FROM emqx_acl WHERE username = %s", (username,))
        #     cur.execute("DELETE FROM emqx_authn WHERE username = %s", (username,))
        #     self.conn.commit()
        # 
        # logger.info(f"✅ Usuário EMQX deletado (SQL): {username}")
        
        raise NotImplementedError("delete_user não implementado no EmqxSqlProvisioner")
    
    def __del__(self):
        """Fechar conexão ao destruir objeto."""
        # TODO: Implementar
        # if hasattr(self, 'conn') and self.conn:
        #     self.conn.close()
        pass


# ============================================================================
# Migração de dados (exemplo)
# ============================================================================
"""
# Se você já tem devices provisionados via HTTP e quer migrar para SQL:

from apps.devices.models import Device
from apps.devices.provisioning.factory import get_provisioner
from apps.devices.provisioning.emqx import EmqxCredentials

# 1. Listar todos os devices com credenciais
devices = Device.objects.filter(credentials_id__isnull=False)

# 2. Gerar novamente as credenciais no SQL
provisioner = get_provisioner()  # Deve retornar EmqxSqlProvisioner

for device in devices:
    # Gerar novas credenciais (a senha original foi perdida, gerar nova)
    creds = EmqxCredentials(
        username=device.credentials_id,
        password=secrets.token_urlsafe(20),  # Nova senha
        client_id=device.mqtt_client_id or generate_client_id(...)
    )
    
    provisioner.create_user(creds)
    provisioner.set_acl(creds, tenant=str(device.tenant_id), site=device.site, device=str(device.id))
    
    print(f"✅ Migrado: {device.id} → {creds.username}")

print("Migração concluída. Notifique os integradores das novas senhas.")
"""
