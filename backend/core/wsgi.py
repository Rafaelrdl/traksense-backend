"""
WSGI - Web Server Gateway Interface para TrakSense Backend

Este arquivo expõe a aplicação Django via protocolo WSGI para servidores web.

WSGI (Web Server Gateway Interface):
-----------------------------------
Padrão Python para comunicação entre servidor web e aplicação.

Servidores compatíveis:
- Gunicorn (recomendado para produção)
- uWSGI
- mod_wsgi (Apache)

Uso:
---
Desenvolvimento:
  python manage.py runserver  # Usa servidor built-in (não WSGI)

Produção (Gunicorn):
  gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 4

Docker (produção):
  CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000", 
       "--workers", "4", "--threads", "2", "--timeout", "60"]

Configuração Recomendada (Produção):
-----------------------------------
- Workers: 2-4 × núcleos de CPU
- Threads: 2-4 por worker
- Timeout: 60s (ou mais para queries longas)
- Max requests: 1000 (recicla workers para evitar memory leaks)

Exemplo completo:
  gunicorn core.wsgi:application \\
    --bind 0.0.0.0:8000 \\
    --workers 4 \\
    --threads 2 \\
    --timeout 60 \\
    --max-requests 1000 \\
    --max-requests-jitter 100 \\
    --access-logfile - \\
    --error-logfile - \\
    --log-level info

Autor: TrakSense Team
Data: 2025-10-07
"""

import os
from django.core.wsgi import get_wsgi_application

# Define módulo de settings padrão
# Pode ser sobrescrito via variável de ambiente DJANGO_SETTINGS_MODULE
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Obtém aplicação WSGI do Django
# Esta aplicação é chamada pelo servidor WSGI para cada requisição
application = get_wsgi_application()
