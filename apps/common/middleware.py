"""
Common middleware for TrakSense backend.
"""

from django.http import HttpResponseNotFound
from django.db import connection


class BlockTenantAdminMiddleware:
    """
    Defensive middleware to block admin access in tenant schemas.
    
    This ensures admin is ONLY accessible via public schema (localhost:8000/admin).
    Tenant schemas (e.g., umc.localhost:8000/admin) will return 404.
    
    While URLConf separation should prevent this, this middleware provides
    defense-in-depth security against accidental admin exposure in tenants.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Block any admin URLs when NOT in public schema
        if request.path.startswith("/admin/"):
            schema_name = getattr(connection, "schema_name", None)
            if schema_name and schema_name != "public":
                # Return 404 for tenant admin access attempts
                return HttpResponseNotFound(
                    "Admin is only accessible via public schema. "
                    "Please use: http://localhost:8000/admin"
                )
        
        return self.get_response(request)
