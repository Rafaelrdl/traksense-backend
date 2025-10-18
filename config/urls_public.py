"""
URL configuration for public/non-tenant routes.

These URLs bypass the tenant middleware and are accessible without a tenant domain.
Used for EMQX ingestion, health checks, and other infrastructure endpoints.
"""

from django.urls import include, path

from apps.common.health import health_check

urlpatterns = [
    # Health check
    path('health', health_check, name='health'),
    
    # MQTT Ingest (called by EMQX without tenant domain)
    path('ingest', include('apps.ingest.urls')),
]
