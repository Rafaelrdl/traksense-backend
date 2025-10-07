"""
ASGI - Asynchronous Server Gateway Interface para TrakSense Backend

Este arquivo expõe a aplicação Django via protocolo ASGI para servidores async.

ASGI (Asynchronous Server Gateway Interface):
--------------------------------------------
Sucessor assíncrono do WSGI, suporta:
- HTTP/1.1 e HTTP/2
- WebSockets
- Long-polling
- Server-Sent Events (SSE)

Servidores compatíveis:
- Uvicorn (recomendado, baseado em uvloop)
- Daphne (Django Channels)
- Hypercorn

Quando usar ASGI vs WSGI:
-------------------------
WSGI (Gunicorn):
  ✓ Mais maduro e estável
  ✓ Melhor para APIs REST síncronas
  ✓ Menor consumo de memória
  ✓ Recomendado para TrakSense (atualmente)

ASGI (Uvicorn):
  ✓ Suporte a WebSockets (dashboards real-time)
  ✓ Melhor performance para I/O-bound tasks
  ✓ Necessário para Django Channels
  ✓ Futuro: streaming de telemetria real-time

Uso:
---
Desenvolvimento:
  python manage.py runserver  # Usa servidor built-in

Produção (Uvicorn):
  uvicorn core.asgi:application --host 0.0.0.0 --port 8000 --workers 4

Docker (produção com ASGI):
  CMD ["uvicorn", "core.asgi:application", "--host", "0.0.0.0", 
       "--port", "8000", "--workers", "4"]

Configuração Recomendada:
------------------------
  uvicorn core.asgi:application \\
    --host 0.0.0.0 \\
    --port 8000 \\
    --workers 4 \\
    --loop uvloop \\
    --log-level info \\
    --access-log

TODO (Fase 2+):
--------------
Se implementar WebSockets para dashboards real-time:
1. Instalar: pip install channels channels-redis
2. Configurar ASGI application com routing
3. Usar Redis como channel layer
4. Implementar consumers para streaming de telemetria

Autor: TrakSense Team
Data: 2025-10-07
"""

import os
from django.core.asgi import get_asgi_application

# Define módulo de settings padrão
# Pode ser sobrescrito via variável de ambiente DJANGO_SETTINGS_MODULE
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Obtém aplicação ASGI do Django
# Esta aplicação é chamada pelo servidor ASGI para cada requisição/conexão
application = get_asgi_application()

# TODO (Fase 2 - WebSockets):
# from channels.routing import ProtocolTypeRouter, URLRouter
# from channels.auth import AuthMiddlewareStack
# import timeseries.routing
#
# application = ProtocolTypeRouter({
#     "http": get_asgi_application(),
#     "websocket": AuthMiddlewareStack(
#         URLRouter(
#             timeseries.routing.websocket_urlpatterns
#         )
#     ),
# })
