"""
Middleware para configurar GUC app.tenant_id baseado no tenant ativo.

CRÍTICO: Sem este middleware, as VIEWs *_tenant retornarão 0 linhas.

Fluxo:
1. django-tenants identifica tenant do request (via domínio/schema)
2. Este middleware configura SET LOCAL app.tenant_id = '<uuid>'
3. VIEWs *_tenant filtram automaticamente por este GUC
4. Queries retornam apenas dados do tenant correto
"""
from django.db import connection
import logging

logger = logging.getLogger(__name__)


class TenantIsolationMiddleware:
    """
    Configura GUC app.tenant_id para isolar queries multi-tenant via VIEWs.
    
    Este middleware é essencial para a Opção B (VIEWs + GUC) de isolamento.
    Sem ele, todas as queries nas VIEWs *_tenant retornarão 0 linhas.
    
    Documentação: README_FASE_R.md, ADR-004
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Skip se não houver tenant no request (ex: durante migrations, management commands)
        if not hasattr(request, 'tenant'):
            logger.debug("TenantIsolationMiddleware: request sem tenant, skipping GUC")
            return self.get_response(request)
        
        # Obter tenant_id do request (django-tenants)
        tenant = request.tenant
        tenant_id_str = str(tenant.id)
        
        # Configurar GUC para queries subsequentes neste request
        # SET LOCAL garante que só vale para esta transação/request
        try:
            with connection.cursor() as cursor:
                cursor.execute("SET LOCAL app.tenant_id = %s", [tenant_id_str])
            
            logger.debug(f"TenantIsolationMiddleware: GUC configurado para tenant {tenant_id_str}")
        
        except Exception as e:
            logger.error(f"TenantIsolationMiddleware: Erro ao configurar GUC: {e}")
            # Não bloquear request, mas logar erro
        
        # Continuar processamento do request
        response = self.get_response(request)
        
        return response
