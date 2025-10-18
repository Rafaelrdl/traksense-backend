"""
Development settings for TrakSense backend.
"""

import sys
print("🔵 [SETTINGS] Carregando development.py", file=sys.stderr, flush=True)

from .base import *

print("🔵 [SETTINGS] base.py importado", file=sys.stderr, flush=True)

DEBUG = True

# Allow all hosts in development
ALLOWED_HOSTS = ['*']

# Development-specific apps
INSTALLED_APPS += []

# Enable Django Debug Toolbar if needed in future
# INSTALLED_APPS += ['debug_toolbar']
# MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']

# Disable HTTPS redirect in development
SECURE_SSL_REDIRECT = False

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
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
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}
