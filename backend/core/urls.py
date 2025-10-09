"""
URLs - Configuração de Rotas do TrakSense Backend

Este arquivo define o mapeamento de URLs para views do Django.
É o roteador principal da aplicação.

Estrutura de URLs:
-----------------
/admin/                      → Django Admin (internal_ops only)
/health                      → Health check geral
/health/timeseries           → Health check específico do timeseries
/api/timeseries/data/points  → Query telemetria com agregações
/api/devices/                → CRUD devices (Fase 2)
/api/dashboards/             → Configurações de dashboards (Fase 2)
/api/cmd/                    → Enviar comandos MQTT (Fase 2)

Multi-Tenancy:
-------------
django-tenants identifica o tenant pelo domínio da requisição.
Exemplos:
- alpha.traksense.com/api/devices/ → Acessa devices do tenant alpha
- beta.traksense.com/api/devices/ → Acessa devices do tenant beta

As URLs são as mesmas, mas os dados são isolados por tenant.

Autor: TrakSense Team
Data: 2025-10-07
"""

from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView
)

# ============================================================================
# ROTAS PRINCIPAIS
# ============================================================================

urlpatterns = [
    # --------------------------------------------------------------------------
    # Django Admin
    # --------------------------------------------------------------------------
    # Interface administrativa do Django
    # Acesso: http://localhost:8000/admin/
    # Credenciais: criar com `python manage.py createsuperuser`
    #
    # IMPORTANTE: Em produção, restringir acesso por:
    # - Firewall (permitir apenas IPs internos)
    # - VPN
    # - Autenticação adicional (2FA)
    #
    # Usado para:
    # - Gerenciar tenants (Client, Domain)
    # - Gerenciar usuários e permissões
    # - Visualizar logs de admin
    # - Operações internas (internal_ops)
    path('admin/', admin.site.urls),
    
    # --------------------------------------------------------------------------
    # Health Checks
    # --------------------------------------------------------------------------
    # Endpoints para monitoramento e healthchecks
    # - GET /health → {"status": "ok"}
    # - GET /health/timeseries → {"status": "ok", "rls_enabled": true, ...}
    #
    # Usado por:
    # - Docker health checks
    # - Kubernetes liveness/readiness probes
    # - Monitoramento (Prometheus, Datadog, etc.)
    # - Load balancers
    path('', include('health.urls')),
    
    # --------------------------------------------------------------------------
    # Timeseries API
    # --------------------------------------------------------------------------
    # Endpoints para consulta de dados de telemetria
    # - GET /api/timeseries/data/points → Query com agregações (1m/5m/1h)
    # - GET /health/timeseries → Health check específico
    #
    # Query Parameters:
    # - device_id: UUID do device
    # - point_id: UUID do point
    # - from: Timestamp inicial (ISO 8601)
    # - to: Timestamp final (ISO 8601)
    # - agg: Nível de agregação (raw|1m|5m|1h)
    #
    # Exemplo:
    # /api/timeseries/data/points?device_id=xxx&point_id=yyy&from=2025-10-06T00:00:00Z&to=2025-10-07T00:00:00Z&agg=1m
    #
    # Segurança:
    # - RLS (Row Level Security) via middleware TenantGucMiddleware
    # - Tenant isolado automaticamente por GUC (app.tenant_id)
    path('', include('apps.timeseries.urls')),
    
    # --------------------------------------------------------------------------
    # API Documentation (Swagger/OpenAPI)
    # --------------------------------------------------------------------------
    # Documentação automática da API REST
    # - GET /api/schema/ → Schema OpenAPI 3.0 (JSON)
    # - GET /api/docs/ → Swagger UI (interface interativa)
    # - GET /api/redoc/ → ReDoc (documentação alternativa)
    #
    # Swagger UI:
    # - Testar endpoints diretamente no navegador
    # - Ver schemas de request/response
    # - Autenticar e fazer requisições
    #
    # Acesso:
    # - http://localhost:8000/api/docs/
    # - http://localhost:8000/api/redoc/
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # TODO (Fase 2): Adicionar rotas para:
    # path('api/', include('devices.urls')),      # CRUD devices/points
    # path('api/', include('dashboards.urls')),   # Configurações dashboards
    # path('api/', include('rules.urls')),        # Regras e alertas
    # path('api/', include('commands.urls')),     # Comandos MQTT e ACKs
]

# ============================================================================
# CONFIGURAÇÕES ADICIONAIS (Produção)
# ============================================================================

# Em produção, considerar:
# - Servir arquivos estáticos via nginx (não Django)
# - Adicionar URL de documentação API (drf-spectacular)
# - Rate limiting por endpoint (django-ratelimit)
# - CORS headers se frontend em domínio diferente (django-cors-headers)

# Exemplo com documentação OpenAPI/Swagger (Fase 2):
# from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
# urlpatterns += [
#     path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
#     path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
# ]
