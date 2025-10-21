"""
Base Django settings for TrakSense backend.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/topics/settings/
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'dev-secret-key-change-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost').split(',')

# Application definition
SHARED_APPS = [
    'django_tenants',  # Must be first
    'apps.accounts',  # Must be before auth for custom user model
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'jazzmin',  # Must be before django.contrib.admin
    'django.contrib.admin',  # Admin only in public schema
    
    # Third-party
    'rest_framework',
    # Note: token_blacklist disabled for multi-tenant compatibility
    # 'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'drf_spectacular',
    
    # Local shared apps
    'apps.tenants',
    'apps.ops',  # Ops panel (staff-only, public schema)
]

TENANT_APPS = [
    'apps.accounts',  # Must be before auth for custom user model
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # NOTE: django.contrib.admin is NOT in TENANT_APPS
    # Admin is centralized in public schema only
    # NOTE: token_blacklist is NOT in TENANT_APPS
    # Token blacklist is centralized in public schema only
    
    # Tenant-specific apps
    'apps.ingest',  # MQTT telemetry ingestion
    'apps.assets',  # Catálogo de Ativos (Sites, Assets, Devices, Sensors)
]


INSTALLED_APPS = list(SHARED_APPS) + [
    app for app in TENANT_APPS if app not in SHARED_APPS
]

MIDDLEWARE = [
    'django_tenants.middleware.main.TenantMainMiddleware',  # Must be first
    'apps.common.middleware.BlockTenantAdminMiddleware',  # Block admin in tenant schemas
    'apps.common.middleware.BlockTenantOpsMiddleware',  # Block ops panel in tenant schemas
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Serve static files in production
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'config.wsgi.application'

# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django_tenants.postgresql_backend',
        'NAME': os.getenv('DB_NAME', 'app'),
        'USER': os.getenv('DB_USER', 'app'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'app'),
        'HOST': os.getenv('DB_HOST', 'postgres'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

DATABASE_ROUTERS = ['django_tenants.routers.TenantSyncRouter']

# Multi-tenant settings
TENANT_MODEL = "tenants.Tenant"
TENANT_DOMAIN_MODEL = "tenants.Domain"
PUBLIC_SCHEMA_NAME = os.getenv('PUBLIC_SCHEMA_NAME', 'public')

# URLConf settings for multi-tenant
PUBLIC_SCHEMA_URLCONF = 'config.urls_public'  # Used when schema == 'public'
ROOT_URLCONF = 'config.urls'  # Default URLConf for tenants

# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# WhiteNoise configuration for serving static files
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 200,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FormParser',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

# drf-spectacular settings
SPECTACULAR_SETTINGS = {
    'TITLE': 'TrakSense / ClimaTrak API',
    'DESCRIPTION': 'Backend multi-tenant para monitoramento HVAC/IoT',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SCHEMA_PATH_PREFIX': '/api',
    'COMPONENT_SPLIT_REQUEST': True,
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayOperationId': True,
    },
}

# CORS settings
CORS_ALLOWED_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:5173').split(',')
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^http://localhost:\d+$",
    r"^http://127\.0\.0\.1:\d+$",
]

# Session & Cookie settings (for JWT cookies)
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = not DEBUG  # True in production
SESSION_COOKIE_SAMESITE = 'Lax'

CSRF_COOKIE_HTTPONLY = False  # Allow JavaScript to read CSRF token
CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_TRUSTED_ORIGINS = os.getenv('CSRF_ORIGINS', 'http://localhost:5173').split(',')

# Simple JWT settings
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': False,  # Disabled for multi-tenant compatibility
    'BLACKLIST_AFTER_ROTATION': False,  # Disabled for multi-tenant (blacklist only in public schema)
    'UPDATE_LAST_LOGIN': True,
    
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    
    'JTI_CLAIM': 'jti',
    
    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=60),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=7),
}

# Redis
REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379/0')

# Celery Configuration
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# MinIO / S3
MINIO_ENDPOINT = os.getenv('MINIO_ENDPOINT', 'minio:9000')
MINIO_ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
MINIO_SECRET_KEY = os.getenv('MINIO_SECRET_KEY', 'minioadmin123')
MINIO_BUCKET = os.getenv('MINIO_BUCKET', 'files')
MINIO_USE_SSL = os.getenv('MINIO_USE_SSL', 'False') == 'True'

# EMQX / MQTT
EMQX_URL = os.getenv('EMQX_URL', 'mqtt://emqx:1883')

# ============================================================================
# PAYLOAD PARSERS - Sistema plugável para diferentes formatos de dispositivos
# ============================================================================
PAYLOAD_PARSER_MODULES = [
    'apps.ingest.parsers.standard',      # Formato padrão TrakSense
    'apps.ingest.parsers.khomp_senml',   # Gateway LoRaWAN Khomp (SenML)
    # Adicione novos parsers aqui conforme necessário
]

# Email (Mailpit for development)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('MAILPIT_SMTP_HOST', 'mailpit')
EMAIL_PORT = int(os.getenv('MAILPIT_SMTP_PORT', '1025'))
EMAIL_USE_TLS = False

# ============================================================================
# DJANGO JAZZMIN - Modern Admin Interface
# ============================================================================
JAZZMIN_SETTINGS = {
    # Title
    "site_title": "TrakSense Admin",
    "site_header": "TrakSense",
    "site_brand": "TrakSense Platform",
    "site_logo": None,
    "login_logo": None,
    "site_icon": None,
    
    # Welcome text
    "welcome_sign": "Bem-vindo ao TrakSense Admin",
    "copyright": "TrakSense © 2025",
    
    # Search model
    "search_model": ["auth.User", "tenants.Tenant", "tenants.Domain"],
    
    # Top menu
    "topmenu_links": [
        {"name": "Home", "url": "admin:index", "permissions": ["auth.view_user"]},
        {"name": "API Docs", "url": "/api/schema/swagger-ui/", "new_window": True},
        {"model": "tenants.Tenant"},
    ],
    
    # User menu
    "usermenu_links": [
        {"model": "auth.user"}
    ],
    
    # Side menu
    "show_sidebar": True,
    "navigation_expanded": True,
    "hide_apps": [],
    "hide_models": [],
    
    # Icons (FontAwesome)
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        "tenants.Tenant": "fas fa-building",
        "tenants.Domain": "fas fa-globe",
        "ingest.Telemetry": "fas fa-database",
    },
    
    # Theme
    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",
    
    # UI Tweaks
    "show_ui_builder": False,
    "changeform_format": "horizontal_tabs",
    "changeform_format_overrides": {
        "auth.user": "collapsible",
        "auth.group": "vertical_tabs"
    },
    
    # Custom CSS/JS
    "custom_css": None,
    "custom_js": None,
    "use_google_fonts_cdn": True,
    "show_ui_builder": False,
    
    # Related modal
    "related_modal_active": True,
    
    # Custom links (per app)
    "custom_links": {
        "auth": [
            {
                "name": "🎛️ Control Center",
                "url": "/ops/",
                "icon": "fas fa-chart-line",
                "permissions": ["auth.view_user"]
            }
        ],
        "tenants": [
            {
                "name": "Ver Documentação Multi-Tenant",
                "url": "/docs/multi-tenant",
                "icon": "fas fa-book",
                "permissions": ["tenants.view_tenant"]
            }
        ],
    },
    
    # Language chooser
    "language_chooser": False,
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-primary",
    "accent": "accent-primary",
    "navbar": "navbar-dark",
    "no_navbar_border": False,
    "navbar_fixed": True,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-primary",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_child_indent": False,
    "sidebar_nav_flat_style": False,
    "theme": "default",
    "dark_mode_theme": None,
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success"
    }
}

EMAIL_USE_SSL = False
