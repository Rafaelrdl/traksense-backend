"""
WSGI config for TrakSense backend.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/wsgi/
"""

import os
import sys

print("🔵 [WSGI] Iniciando wsgi.py", file=sys.stderr, flush=True)

from django.core.wsgi import get_wsgi_application

print("🔵 [WSGI] Django importado, setando DJANGO_SETTINGS_MODULE", file=sys.stderr, flush=True)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

print("🔵 [WSGI] Chamando get_wsgi_application()...", file=sys.stderr, flush=True)
application = get_wsgi_application()
print("✅ [WSGI] application criada com sucesso!", file=sys.stderr, flush=True)
