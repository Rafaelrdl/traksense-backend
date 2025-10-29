"""
URL configuration for TrakSense backend (Tenant schemas).

This URLConf is used for tenant schemas (NOT public schema).
Admin is NOT exposed here - it's centralized in public schema only.

For public schema URLs, see config.urls_public.
"""

from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    # NOTE: Admin is NOT included here - it's only in public schema
    # Admin URL: http://localhost:8000/admin (public schema)
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # Authentication & Users API
    path('api/', include('apps.accounts.urls')),
    
    # Assets Catalog API (tenant-specific data)
    path('api/', include('apps.assets.urls')),
    
    # Telemetry API (tenant-specific data)
    path('api/telemetry/', include('apps.ingest.api_urls')),
    
    # Alerts & Rules API (tenant-specific data)
    path('api/alerts/', include('apps.alerts.urls')),
]
