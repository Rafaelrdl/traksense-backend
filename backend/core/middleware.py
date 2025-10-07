"""
Middleware - TrakSense Custom Middleware

Este módulo contém middlewares personalizados para o TrakSense,
principalmente relacionados à segurança multi-tenant via Row Level Security.

Middlewares:
-----------
- TenantGucMiddleware: Configura GUC (app.tenant_id) para RLS no PostgreSQL

Row Level Security (RLS):
-------------------------
RLS é uma feature do PostgreSQL que filtra rows baseado em políticas.
No TrakSense, usamos RLS para garantir isolamento de dados de telemetria
entre tenants na tabela public.ts_measure.

Como funciona:
1. TenantMainMiddleware (django-tenants) identifica o tenant pelo domínio
2. TenantGucMiddleware configura GUC (app.tenant_id = tenant.pk)
3. PostgreSQL aplica política RLS: (tenant_id = current_setting('app.tenant_id'))
4. Queries só retornam/modificam dados do tenant atual

Benefícios:
- Segurança em nível de banco de dados (não apenas aplicação)
- Impossível acessar dados de outro tenant mesmo com SQL injection
- Performance: RLS é otimizado pelo query planner do PostgreSQL

IMPORTANTE: Este middleware DEVE ser o ÚLTIMO na lista de middlewares!
           Deve executar DEPOIS de TenantMainMiddleware.

Autor: TrakSense Team
Data: 2025-10-07
"""

import logging
from django.db import connection
from django.utils.deprecation import MiddlewareMixin

# Logger para debug e avisos de segurança
logger = logging.getLogger(__name__)


class TenantGucMiddleware(MiddlewareMixin):
    """
    Middleware para configurar GUC (Grand Unified Configuration) do PostgreSQL.
    
    GUC (app.tenant_id) é usado pela política de Row Level Security na tabela
    public.ts_measure para filtrar dados por tenant.
    
    Ordem de Execução:
    -----------------
    1. TenantMainMiddleware (django-tenants) → identifica tenant pelo domínio
    2. [outros middlewares Django]
    3. TenantGucMiddleware (este) → configura GUC para RLS
    4. View é executada
    5. Response é retornado
    
    Segurança:
    ---------
    - Se GUC não for configurado, RLS bloqueia TODOS os acessos
    - Logs de warning são gerados se GUC não for setado
    - Cada requisição tem sua própria transação e GUC isolado
    
    Performance:
    -----------
    - SET LOCAL é usado (scope: transação atual)
    - Não há overhead significativo (< 1ms)
    - GUC é resetado automaticamente ao fim da transação
    """
    
    def process_request(self, request):
        """
        Configura app.tenant_id GUC para Row Level Security.
        
        Este método é chamado ANTES da view ser executada.
        
        Fluxo:
        1. Obtém tenant de connection.tenant (setado por TenantMainMiddleware)
        2. Valida se tenant foi resolvido corretamente
        3. Executa SET LOCAL app.tenant_id = '<tenant_pk>'
        4. Marca request._tenant_id_set = True para auditoria
        
        Args:
            request: HttpRequest object do Django
            
        Comportamento:
        - Se tenant não resolvido: log warning (possível acesso público)
        - Se erro ao setar GUC: log error (queries falharão)
        - Se sucesso: log debug (apenas em modo DEBUG)
        """
        # Obtém tenant setado por django-tenants TenantMainMiddleware
        # connection.tenant é uma instância de Client model
        tenant = getattr(connection, "tenant", None)
        
        # Validação: tenant foi resolvido?
        if not tenant or not getattr(tenant, "schema_name", None):
            # Casos onde tenant não é resolvido:
            # 1. Domínio não cadastrado (404 esperado)
            # 2. Requisição para schema 'public' (ex: admin, health checks)
            # 3. Erro de configuração
            
            request._tenant_id_set = False
            logger.warning(
                f"TenantGucMiddleware: Tenant NÃO resolvido para {request.path} "
                f"(domínio: {request.get_host()})"
            )
            return
        
        # Tenant resolvido com sucesso, configurar GUC
        try:
            with connection.cursor() as cur:
                # app.tenant_id é um custom GUC (Grand Unified Configuration)
                # Nome com ponto é válido no PostgreSQL
                # Usamos tenant.pk (UUID) como identificador
                # Alternativa: usar tenant.schema_name (string)
                tenant_id = str(tenant.pk) if hasattr(tenant, 'pk') else tenant.schema_name
                
                # SET LOCAL: GUC válido apenas para transação atual
                # Automaticamente resetado ao fim da transação
                # Mais seguro que SET (que persiste na conexão)
                cur.execute("SET LOCAL app.tenant_id = %s", [tenant_id])
                
                # Marca request como tendo GUC configurado (auditoria)
                request._tenant_id_set = True
                request._tenant_id = tenant_id
                
                # Log debug (apenas em modo DEBUG)
                logger.debug(
                    f"TenantGucMiddleware: GUC configurado → "
                    f"tenant={tenant.name} (id={tenant_id}, schema={tenant.schema_name})"
                )
        except Exception as e:
            # Erro ao configurar GUC: crítico!
            # Queries de telemetria falharão (RLS bloqueará acesso)
            logger.error(
                f"TenantGucMiddleware: ERRO ao configurar GUC: {e}",
                exc_info=True
            )
            request._tenant_id_set = False
    
    def process_response(self, request, response):
        """
        Processa response e audita se GUC foi configurado.
        
        Este método é chamado APÓS a view ser executada.
        
        Auditoria:
        - Se GUC não foi setado: log WARNING (risco de segurança)
        - Útil para identificar endpoints que acessam telemetria sem tenant
        
        Args:
            request: HttpRequest object
            response: HttpResponse object da view
            
        Returns:
            HttpResponse object (inalterado)
        """
        # Verifica se GUC foi configurado na requisição
        if hasattr(request, "_tenant_id_set") and not request._tenant_id_set:
            # GUC NÃO foi setado!
            # Isso pode indicar:
            # 1. Endpoint público (ok se não acessar telemetria)
            # 2. Erro de configuração (crítico se acessar telemetria)
            # 3. Requisição para schema 'public' (ex: /admin/)
            
            logger.warning(
                f"TenantGucMiddleware: GUC NÃO CONFIGURADO para requisição → "
                f"path={request.path}, método={request.method}, "
                f"domínio={request.get_host()}. "
                f"⚠️  RISCO DE VAZAMENTO DE DADOS se endpoint acessar telemetria!"
            )
        
        # Retorna response inalterado
        return response
