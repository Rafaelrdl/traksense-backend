"""
Pytest Conftest - Fixtures globais para testes

Este arquivo define fixtures compartilhadas por todos os testes.

Fixtures:
--------
1. django_db_setup (session):
   - Configura banco de dados de teste
   - Roda uma vez por sessão de teste
   - Usa mesma configuração de settings.py

2. api_client:
   - APIClient do DRF para testes de API
   - Usado em testes de endpoints REST
   - Suporta autenticação (session, token, JWT)

Uso:
---
# Em test files
def test_example(django_db_setup, api_client):
    response = api_client.get('/health')
    assert response.status_code == 200

Executar testes:
---------------
# Todos os testes
pytest

# Com coverage
pytest --cov=. --cov-report=html

# Específico
pytest tests/test_rls_isolation.py -v

# Paralelo (mais rápido)
pytest -n auto

Autor: TrakSense Team
Data: 2025-10-07
"""
import pytest
from django.conf import settings


@pytest.fixture(scope='session')
def django_db_setup():
    """
    Configura banco de dados para testes (session scope).
    
    Roda uma vez no início da sessão de testes.
    Usa mesma configuração de settings.DATABASES.
    """
    settings.DATABASES['default'] = {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': settings.DATABASES['default']['NAME'],
        'USER': settings.DATABASES['default']['USER'],
        'PASSWORD': settings.DATABASES['default']['PASSWORD'],
        'HOST': settings.DATABASES['default']['HOST'],
        'PORT': settings.DATABASES['default']['PORT'],
    }


@pytest.fixture
def api_client():
    """
    APIClient do DRF para testes de endpoints.
    
    Usa:
    - GET/POST/PUT/DELETE requests
    - Autenticação: client.force_authenticate(user=user)
    - Headers customizados: client.get('/path', HTTP_HOST='alpha.localhost')
    
    Example:
        def test_endpoint(api_client):
            response = api_client.get('/data/points?device_id=...')
            assert response.status_code == 200
    """
    from rest_framework.test import APIClient
    return APIClient()
