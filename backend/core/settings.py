"""
Settings - Configurações Django para TrakSense Backend

Este arquivo contém todas as configurações do projeto Django, incluindo:
- Multi-tenancy (django-tenants)
- TimescaleDB para telemetria
- Row Level Security (RLS)
- Django REST Framework
- Middleware customizado

IMPORTANTE: Este arquivo usa django-environ para carregar variáveis de ambiente
            do arquivo .env.api (em desenvolvimento) ou secrets (em produção).

Arquitetura Multi-Tenant:
-------------------------
- SHARED_APPS: Apps no schema 'public' (tenancy, timeseries, health)
- TENANT_APPS: Apps por schema de tenant (devices, dashboards, rules, commands)

Schema Structure:
----------------
public (shared):
  ├── ts_measure (hypertable com RLS)
  ├── ts_measure_1m, _5m, _1h (continuous aggregates)
  └── tenancy_client, tenancy_domain

{tenant_schema} (ex: alpha_corp):
  ├── devices_device
  ├── devices_point
  ├── dashboards_config
  ├── rules_rule
  └── commands_command

Autor: TrakSense Team
Data: 2025-10-07
"""

from pathlib import Path
import environ
import os

# ============================================================================
# CONFIGURAÇÃO DE AMBIENTE
# ============================================================================

# Inicializa django-environ para gerenciar variáveis de ambiente
env = environ.Env(
    # Define valores padrão e tipos esperados
    DJANGO_DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, []),
)

# Define o diretório base do projeto (onde manage.py está localizado)
BASE_DIR = Path(__file__).resolve().parent.parent

# Lê arquivo .env se existir (desenvolvimento)
# Em produção, variáveis vêm de secrets do Docker/Kubernetes
environ.Env.read_env(os.path.join(BASE_DIR.parent.parent, 'infra', '.env.api'))

# ============================================================================
# SEGURANÇA
# ============================================================================

# SECRET_KEY: Chave secreta para assinatura de cookies, tokens, etc.
# CRÍTICO: Gerar valor aleatório seguro em produção!
# Comando: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
SECRET_KEY = env('DJANGO_SECRET_KEY', default='dev-secret-key-change-me')

# DEBUG: Modo debug (mostra stack traces detalhados)
# IMPORTANTE: Sempre False em produção!
DEBUG = env.bool('DJANGO_DEBUG', default=True)

# ALLOWED_HOSTS: Hosts permitidos para acessar a aplicação
# Previne ataques de Host Header Injection
# Em produção: lista específica de domínios
# Com django-tenants: deve incluir todos os domínios de tenants
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['*'])

# ============================================================================
# DJANGO-TENANTS: MULTI-TENANCY CONFIGURATION
# ============================================================================

# SHARED_APPS: Apps instalados no schema 'public' (compartilhados entre tenants)
# - django_tenants: DEVE ser o primeiro
# - tenancy: Models Client e Domain (routing)
# - timeseries: Telemetria (ts_measure com RLS)
# - health: Health checks
# - Apps Django padrão: auth, contenttypes, sessions, admin
SHARED_APPS = [
    'django_tenants',  # DEVE ser o primeiro!
    
    # Apps TrakSense compartilhados
    'tenancy',
    'timeseries',
    'health',
    
    # Django built-in apps
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    
    # Django REST Framework
    'rest_framework',
]

# TENANT_APPS: Apps instalados em cada schema de tenant (dados isolados)
# - devices: Equipamentos IoT (Device, Point, DeviceTemplate)
# - dashboards: Configurações de painéis (DashboardConfig)
# - rules: Regras de alertas e limites
# - commands: Comandos MQTT e ACKs
TENANT_APPS = [
    'devices',
    'dashboards',
    'rules',
    'commands',
]

# INSTALLED_APPS: Combinação de SHARED_APPS + TENANT_APPS
# django-tenants usa esta lista para determinar onde criar tabelas
INSTALLED_APPS = list(set(SHARED_APPS + TENANT_APPS))

# TENANT_MODEL: Model que representa um tenant
# Deve herdar de TenantMixin
TENANT_MODEL = 'tenancy.Client'

# TENANT_DOMAIN_MODEL: Model que mapeia domínios para tenants
# Deve herdar de DomainMixin
# django-tenants usa o domínio da requisição para identificar o tenant
TENANT_DOMAIN_MODEL = 'tenancy.Domain'

# ============================================================================
# MIDDLEWARE
# ============================================================================

MIDDLEWARE = [
    # django-tenants middleware DEVE ser o primeiro!
    # Identifica o tenant baseado no domínio da requisição
    # Define connection.tenant para uso posterior
    'django_tenants.middleware.main.TenantMainMiddleware',
    
    # Django middlewares padrão
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
    # TrakSense custom middleware para Row Level Security
    # DEVE ser o último middleware!
    # Configura GUC (app.tenant_id) para RLS no PostgreSQL
    'core.middleware.TenantGucMiddleware',
]

# ============================================================================
# URL CONFIGURATION
# ============================================================================

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================

# DATABASE_URL: String de conexão PostgreSQL/TimescaleDB
# Formato: postgresql://user:password@host:port/database
# Exemplo: postgresql://postgres:postgres@db:5432/traksense
DATABASES = {
    'default': env.db('DATABASE_URL', default='postgresql://postgres:postgres@localhost:5432/traksense')
}

# DATABASE_ROUTERS: Router customizado para django-tenants
# Determina em qual schema criar/consultar tabelas
# - SHARED_APPS → schema 'public'
# - TENANT_APPS → schema do tenant atual
DATABASE_ROUTERS = (
    'django_tenants.routers.TenantSyncRouter',
)

# ============================================================================
# CACHE CONFIGURATION (Redis)
# ============================================================================

# Redis para cache de queries, sessões e Celery (futuro)
# REDIS_URL: redis://host:port/db
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': env('REDIS_URL', default='redis://localhost:6379/0'),
    }
}

# Usar Redis para sessões (recomendado para produção)
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# ============================================================================
# PASSWORD VALIDATION
# ============================================================================

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ============================================================================
# INTERNATIONALIZATION
# ============================================================================

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True  # Sempre usar timezone-aware datetimes

# ============================================================================
# STATIC FILES (CSS, JavaScript, Images)
# ============================================================================

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# ============================================================================
# DEFAULT PRIMARY KEY FIELD TYPE
# ============================================================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ============================================================================
# DJANGO REST FRAMEWORK
# ============================================================================

REST_FRAMEWORK = {
    # Autenticação padrão: Session (cookies)
    # Produção: adicionar TokenAuthentication ou JWTAuthentication
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    
    # Permissões padrão: Autenticado
    # Endpoints públicos devem usar AllowAny explicitamente
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    
    # Paginação padrão: 100 itens por página
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 100,
    
    # Renderer: JSON (remover BrowsableAPIRenderer em produção)
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',  # Remover em prod
    ],
}

# ============================================================================
# LOGGING
# ============================================================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {name} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': env('DJANGO_LOG_LEVEL', default='INFO'),
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': env('DJANGO_LOG_LEVEL', default='INFO'),
            'propagate': False,
        },
        'core.middleware': {
            'handlers': ['console'],
            'level': 'DEBUG' if DEBUG else 'WARNING',
            'propagate': False,
        },
        'timeseries': {
            'handlers': ['console'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
    },
}

# ============================================================================
# SEGURANÇA ADICIONAL (Produção)
# ============================================================================

# Descomentar em produção:
# SECURE_SSL_REDIRECT = True
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True
# SECURE_BROWSER_XSS_FILTER = True
# SECURE_CONTENT_TYPE_NOSNIFF = True
# X_FRAME_OPTIONS = 'DENY'
# SECURE_HSTS_SECONDS = 31536000  # 1 ano
# SECURE_HSTS_INCLUDE_SUBDOMAINS = True
# SECURE_HSTS_PRELOAD = True
