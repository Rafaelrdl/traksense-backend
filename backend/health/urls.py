"""
Health URL Configuration - Rota de health check

Rota:
----
GET /health → {"status": "ok"}

Usado por:
- Kubernetes liveness/readiness probes
- Docker healthcheck
- Load balancers (ALB, NGINX)
- Monitoramento (Prometheus, Datadog)

Autor: TrakSense Team
Data: 2025-10-07
"""
from django.urls import path
from .views import health

urlpatterns = [
    # Health check básico
    # GET /health
    path('health', health, name='health'),
]
