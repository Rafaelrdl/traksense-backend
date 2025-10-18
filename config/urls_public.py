"""
URL configuration for public/non-tenant routes (schema: public).

These URLs are used when accessing the public schema.
Includes centralized Django Admin with Jazzmin.
"""

from django.contrib import admin
from django.urls import include, path

from apps.common.health import health_check

urlpatterns = [
    # Centralized Django Admin (only in public schema)
    path('admin/', admin.site.urls),
    
    # Ops Panel (staff-only, public schema)
    path('ops/', include('apps.ops.urls')),
    
    # Health check
    path('health', health_check, name='health'),
    
    # MQTT Ingest (called by EMQX without tenant domain)
    path('ingest', include('apps.ingest.urls')),
]
