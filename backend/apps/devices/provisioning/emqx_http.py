"""
EMQX HTTP Management API Provisioner - Opção A (Padrão)
=========================================================

Implementação de provisionamento via HTTP Management API do EMQX v5.

Vantagens:
    - Simplicidade (sem configuração de schema SQL)
    - Isolamento (backend não acessa internals do EMQX)
    - Flexibilidade (fácil trocar de broker)

Desvantagens:
    - Latência HTTP adicional
    - Dependência da disponibilidade do endpoint

Mitigações:
    - Retry com backoff exponencial (3 tentativas: 1s, 2s, 4s)
    - Operações idempotentes
    - Logs estruturados para auditoria
    - Métricas de sucessos/falhas

Uso:
    from .factory import get_provisioner
    
    provisioner = get_provisioner()  # Retorna EmqxHttpProvisioner se EMQX_PROVISION_MODE=http
    provisioner.create_user(creds)
    provisioner.set_acl(creds, tenant="abc", site="site1", device="dev123")

Endpoints EMQX v5:
    - POST /api/v5/authentication/password_based:built_in_database/users
    - POST /api/v5/authorization/sources/built_in_database/rules
    - DELETE /api/v5/authentication/password_based:built_in_database/users/{username}

Referências:
    - EMQX v5 HTTP API Docs: https://docs.emqx.com/en/emqx/v5.0/admin/api.html
    - ADR-003: EMQX Authentication & Authorization Strategy
"""

import os
import time
import logging
import requests
from typing import List, Dict, Any, Optional
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .emqx import (
    EmqxProvisioner,
    EmqxCredentials,
    EmqxProvisioningError,
    EmqxConnectionError,
    EmqxAuthenticationError,
    EmqxValidationError,
    EmqxConflictError,
)


logger = logging.getLogger(__name__)


class EmqxHttpProvisioner(EmqxProvisioner):
    """
    Provisionador EMQX via HTTP Management API.
    
    Configuração via variáveis de ambiente:
        - EMQX_MGMT_URL: URL base da API (ex: http://emqx:18083)
        - EMQX_ADMIN_USER: Username admin do EMQX (padrão: admin)
        - EMQX_ADMIN_PASS: Password admin do EMQX (padrão: public)
        - EMQX_REALM: Namespace para autenticação (padrão: traksense)
    
    Retry Policy:
        - 3 tentativas máximas
        - Backoff exponencial: 1s, 2s, 4s
        - Retry em: 500, 502, 503, 504 (erros de servidor)
        - Não retry em: 400, 401, 403, 404 (erros de cliente)
    
    Exemplo:
        provisioner = EmqxHttpProvisioner()
        
        try:
            provisioner.create_user(creds)
            provisioner.set_acl(creds, tenant="abc", site="site1", device="dev123")
        except EmqxConnectionError as e:
            logger.error(f"EMQX indisponível: {e}")
        except EmqxAuthenticationError as e:
            logger.error(f"Credenciais admin inválidas: {e}")
    """
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        admin_user: Optional[str] = None,
        admin_pass: Optional[str] = None,
        realm: Optional[str] = None,
        timeout: int = 10,
        max_retries: int = 3,
    ):
        """
        Inicializa provisionador HTTP.
        
        Args:
            base_url: URL base da Management API (ex: http://emqx:18083)
            admin_user: Username admin do EMQX
            admin_pass: Password admin do EMQX
            realm: Namespace de autenticação
            timeout: Timeout de requisições HTTP (segundos)
            max_retries: Número máximo de tentativas
        """
        # Variáveis de ambiente com fallback
        self.base_url = (base_url or os.getenv('EMQX_MGMT_URL', 'http://emqx:18083')).rstrip('/')
        self.admin_user = admin_user or os.getenv('EMQX_ADMIN_USER', 'admin')
        self.admin_pass = admin_pass or os.getenv('EMQX_ADMIN_PASS', 'public')
        self.realm = realm or os.getenv('EMQX_REALM', 'traksense')
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Configurar sessão HTTP com retry automático
        self.session = self._create_session()
        
        logger.info(
            f"EmqxHttpProvisioner inicializado: base_url={self.base_url}, "
            f"admin_user={self.admin_user}, realm={self.realm}, max_retries={self.max_retries}"
        )
    
    def _create_session(self) -> requests.Session:
        """
        Cria sessão HTTP com retry automático e autenticação JWT (Bearer Token).
        
        EMQX v5 requer JWT token obtido via /api/v5/login ao invés de Basic Auth.
        
        Returns:
            Sessão configurada com retry policy e auth
        """
        session = requests.Session()
        
        # Obter JWT token via login
        token = self._get_jwt_token()
        
        # Configurar Bearer Token para todas as requisições
        session.headers.update({'Authorization': f'Bearer {token}'})
        
        # Retry strategy: 3 tentativas com backoff exponencial
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=1,  # 1s, 2s, 4s
            status_forcelist=[500, 502, 503, 504],  # Retry apenas em erros de servidor
            allowed_methods=["GET", "POST", "PUT", "DELETE"],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _get_jwt_token(self) -> str:
        """
        Obtém JWT token via endpoint /api/v5/login.
        
        EMQX v5 requer este token para acessar a Management API.
        
        Returns:
            JWT token (string)
            
        Raises:
            EmqxAuthenticationError: Se credenciais admin estiverem incorretas
            EmqxConnectionError: Se não conseguir conectar no EMQX
        """
        login_url = f"{self.base_url}/api/v5/login"
        payload = {
            "username": self.admin_user,
            "password": self.admin_pass
        }
        
        try:
            logger.info(f"Obtendo JWT token via {login_url}")
            response = requests.post(
                login_url,
                json=payload,
                timeout=self.timeout,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                data = response.json()
                token = data.get('token')
                if not token:
                    raise EmqxAuthenticationError("Token não retornado pela API de login")
                logger.info("✅ JWT token obtido com sucesso")
                return token
            elif response.status_code == 401:
                raise EmqxAuthenticationError(
                    f"Credenciais admin inválidas: {self.admin_user} "
                    f"(verifique EMQX_ADMIN_USER/PASS)"
                )
            else:
                raise EmqxConnectionError(
                    f"Erro ao fazer login: HTTP {response.status_code} - {response.text}"
                )
                
        except requests.exceptions.RequestException as e:
            raise EmqxConnectionError(f"Falha ao conectar no EMQX: {e}") from e
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        expected_status: int = 200,
    ) -> Dict[str, Any]:
        """
        Executa requisição HTTP com tratamento de erros.
        
        Args:
            method: Método HTTP (GET, POST, PUT, DELETE)
            endpoint: Endpoint relativo (ex: /api/v5/authentication/.../users)
            json_data: Payload JSON (para POST/PUT)
            expected_status: Status HTTP esperado para sucesso
        
        Returns:
            Resposta JSON do EMQX
        
        Raises:
            EmqxConnectionError: Falha de conexão ou timeout
            EmqxAuthenticationError: Credenciais admin inválidas (401)
            EmqxValidationError: Dados inválidos (400)
            EmqxConflictError: Recurso já existe (409)
            EmqxProvisioningError: Outros erros
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            logger.debug(f"EMQX HTTP {method} {url} | payload={json_data}")
            
            response = self.session.request(
                method=method,
                url=url,
                json=json_data,
                timeout=self.timeout,
            )
            
            # Sucesso esperado
            if response.status_code == expected_status:
                logger.info(f"EMQX HTTP {method} {url} | status={response.status_code} | OK")
                return response.json() if response.content else {}
            
            # Tratamento de erros específicos
            if response.status_code == 401:
                raise EmqxAuthenticationError(
                    f"Credenciais admin inválidas: {self.admin_user} (verifique EMQX_ADMIN_USER/PASS)"
                )
            
            if response.status_code == 400:
                error_detail = response.json() if response.content else {}
                raise EmqxValidationError(
                    f"Dados inválidos: {error_detail}"
                )
            
            if response.status_code == 404:
                # Recurso não encontrado (pode ser OK em delete)
                if method == "DELETE":
                    logger.warning(f"EMQX HTTP DELETE {url} | status=404 | Recurso já não existe")
                    return {}
                raise EmqxProvisioningError(f"Recurso não encontrado: {url}")
            
            if response.status_code == 409:
                # Conflito (recurso já existe)
                raise EmqxConflictError(
                    f"Recurso já existe (status 409). Use operação idempotente."
                )
            
            # Erro genérico
            raise EmqxProvisioningError(
                f"EMQX HTTP {method} {url} | status={response.status_code} | "
                f"response={response.text}"
            )
        
        except requests.exceptions.Timeout as e:
            raise EmqxConnectionError(f"Timeout ao conectar no EMQX: {url} (timeout={self.timeout}s)") from e
        
        except requests.exceptions.ConnectionError as e:
            raise EmqxConnectionError(f"Falha ao conectar no EMQX: {url} | erro={e}") from e
        
        except requests.exceptions.RequestException as e:
            raise EmqxProvisioningError(f"Erro HTTP inesperado: {e}") from e
    
    def create_user(self, creds: EmqxCredentials) -> None:
        """
        Cria ou atualiza usuário no EMQX via HTTP API.
        
        Endpoint: POST /api/v5/authentication/password_based:built_in_database/users
        
        Comportamento:
            - Idempotente: se usuário existe, atualiza a senha
            - Valida credenciais antes de enviar
        
        Args:
            creds: Credenciais do dispositivo
        
        Raises:
            EmqxProvisioningError: Falha ao criar usuário
        """
        # Validar credenciais
        self.validate_credentials(creds)
        
        # Preparar payload
        payload = {
            "user_id": creds.username,
            "password": creds.password,
        }
        
        # Tentar criar usuário
        try:
            self._make_request(
                method="POST",
                endpoint="/api/v5/authentication/password_based:built_in_database/users",
                json_data=payload,
                expected_status=201,  # Created
            )
            logger.info(f"✅ Usuário EMQX criado: {creds.username}")
        
        except EmqxConflictError:
            # Usuário já existe → atualizar senha (idempotência)
            logger.warning(f"⚠️ Usuário {creds.username} já existe. Atualizando senha...")
            self._make_request(
                method="PUT",
                endpoint=f"/api/v5/authentication/password_based:built_in_database/users/{creds.username}",
                json_data={"password": creds.password},
                expected_status=200,  # OK
            )
            logger.info(f"✅ Senha atualizada para usuário: {creds.username}")
    
    def set_acl(
        self,
        creds: EmqxCredentials,
        tenant: str,
        site: str,
        device: str
    ) -> None:
        """
        Configura ACL mínima para o dispositivo via HTTP API.
        
        Endpoint: POST /api/v5/authorization/sources/built_in_database/rules
        
        Comportamento:
            - Remove ACLs antigas do usuário (se existirem)
            - Cria apenas as regras necessárias (mínimo privilégio)
            - Nunca usar wildcards # ou + fora do prefixo do device
        
        Args:
            creds: Credenciais do dispositivo
            tenant: UUID ou slug do tenant
            site: Slug do site
            device: UUID ou slug do device
        
        Raises:
            EmqxProvisioningError: Falha ao configurar ACL
        """
        # 1. Remover ACLs antigas (cleanup)
        self._delete_acl(creds.username)
        
        # 2. Gerar regras de ACL mínimas
        topic_base = f"traksense/{tenant}/{site}/{device}"
        
        rules = [
            # Publish permitido em 5 tópicos
            {"action": "publish", "permission": "allow", "topic": f"{topic_base}/state"},
            {"action": "publish", "permission": "allow", "topic": f"{topic_base}/telem"},
            {"action": "publish", "permission": "allow", "topic": f"{topic_base}/event"},
            {"action": "publish", "permission": "allow", "topic": f"{topic_base}/alarm"},
            {"action": "publish", "permission": "allow", "topic": f"{topic_base}/ack"},
            
            # Subscribe permitido apenas em cmd
            {"action": "subscribe", "permission": "allow", "topic": f"{topic_base}/cmd"},
        ]
        
        # 3. Criar todas as regras em uma única requisição (batch)
        # EMQX 5.8 usa /rules/users com array de regras por username
        payload = [{
            "username": creds.username,
            "rules": rules  # Array de regras para este username
        }]
        
        try:
            self._make_request(
                method="POST",
                endpoint="/api/v5/authorization/sources/built_in_database/rules/users",
                json_data=payload,
                expected_status=204,  # No Content (sucesso sem retorno)
            )
            logger.info(
                f"✅ ACL configurada para {creds.username}: {len(rules)} regras "
                f"(5 publish, 1 subscribe) no prefixo {topic_base}"
            )
        
        except EmqxConflictError:
            # Regras já existem → ignorar (idempotência)
            logger.warning(f"⚠️ ACLs já existem para {creds.username}, mantendo existentes")
        except EmqxProvisioningError as e:
            logger.error(f"❌ Falha ao criar ACLs para {creds.username}: {e}")
            raise
    
    def _delete_acl(self, username: str) -> None:
        """
        Remove todas as ACLs de um usuário.
        
        EMQX 5.8 usa DELETE /rules/users/{username} para remover todas as regras de um user.
        
        Args:
            username: Username do dispositivo
        """
        try:
            # DELETE /rules/users/{username} remove todas as regras deste user
            self._make_request(
                method="DELETE",
                endpoint=f"/api/v5/authorization/sources/built_in_database/rules/users/{username}",
                expected_status=204,  # No Content
            )
            logger.debug(f"🗑️ ACLs removidas para: {username}")
        
        except EmqxProvisioningError as e:
            # Ignorar erros ao deletar ACLs antigas (melhor esforço)
            # 404 significa que não há regras (OK)
            if "404" not in str(e):
                logger.warning(f"⚠️ Falha ao remover ACLs antigas de {username}: {e}")
    
    def delete_user(self, username: str) -> None:
        """
        Remove usuário e suas ACLs do EMQX via HTTP API.
        
        Endpoint: DELETE /api/v5/authentication/password_based:built_in_database/users/{username}
        
        Comportamento:
            - Idempotente: não falha se usuário não existir
            - Remove ACLs automaticamente (se suportado pelo EMQX)
            - Desconecta cliente MQTT se estiver conectado
        
        Args:
            username: Username do dispositivo (formato: t:<tenant>:d:<device>)
        
        Raises:
            EmqxProvisioningError: Falha ao deletar usuário
        """
        # 1. Deletar ACLs primeiro (cleanup)
        self._delete_acl(username)
        
        # 2. Deletar usuário
        try:
            self._make_request(
                method="DELETE",
                endpoint=f"/api/v5/authentication/password_based:built_in_database/users/{username}",
                expected_status=204,  # No Content
            )
            logger.info(f"✅ Usuário EMQX deletado: {username}")
        
        except EmqxProvisioningError as e:
            # Se status 404, usuário já não existe (idempotência OK)
            if "404" in str(e):
                logger.warning(f"⚠️ Usuário {username} já não existe (idempotência OK)")
            else:
                raise
