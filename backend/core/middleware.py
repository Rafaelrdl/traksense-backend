"""
Custom middleware for TrakSense.
"""
import logging
from django.db import connection
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class TenantGucMiddleware(MiddlewareMixin):
    """
    Sets PostgreSQL GUC (app.tenant_id) for Row Level Security.
    
    This middleware MUST run after TenantMainMiddleware from django-tenants.
    It ensures that every database query is filtered by the current tenant.
    """
    
    def process_request(self, request):
        """
        Set app.tenant_id GUC for RLS on ts_measure table.
        """
        # django-tenants sets connection.tenant
        tenant = getattr(connection, "tenant", None)
        
        if not tenant or not getattr(tenant, "schema_name", None):
            # Public schema ou tenant não resolvido
            request._tenant_id_set = False
            logger.warning(
                f"TenantGucMiddleware: Tenant não resolvido para {request.path}"
            )
            return
        
        # Tenant resolvido, setar GUC
        try:
            with connection.cursor() as cur:
                # app.tenant_id é custom GUC válido (nome com ponto)
                # Usamos o schema_name como tenant_id (ou pode usar tenant.pk)
                tenant_id = str(tenant.pk) if hasattr(tenant, 'pk') else tenant.schema_name
                cur.execute("SET LOCAL app.tenant_id = %s", [tenant_id])
                request._tenant_id_set = True
                request._tenant_id = tenant_id
                logger.debug(f"TenantGucMiddleware: GUC setado para tenant={tenant_id}")
        except Exception as e:
            logger.error(f"TenantGucMiddleware: Erro ao setar GUC: {e}")
            request._tenant_id_set = False
    
    def process_response(self, request, response):
        """
        Log warning se GUC não foi setado (possível vazamento de dados).
        """
        if hasattr(request, "_tenant_id_set") and not request._tenant_id_set:
            logger.warning(
                f"TenantGucMiddleware: GUC NÃO SETADO para {request.path} "
                f"(método={request.method}) - RISCO DE VAZAMENTO DE DADOS!"
            )
        return response
