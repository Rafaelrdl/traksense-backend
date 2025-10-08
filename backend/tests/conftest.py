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

3. db_tenant (function):
   - Helper para configurar tenant_id via GUC (SET LOCAL app.tenant_id)
   - Garante isolamento de testes RLS

4. reset_db (function):
   - Limpa dados do banco após cada teste
   - Garante isolamento entre testes

Uso:
---
# Em test files
def test_example(django_db_setup, api_client):
    response = api_client.get('/health')
    assert response.status_code == 200

# Com tenant específico
def test_rls(db_tenant):
    db_tenant.set('tenant-uuid-123')
    # queries agora filtradas por RLS

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

# Apenas smoke tests
pytest -m smoke

Autor: TrakSense Team
Data: 2025-10-07
"""
import pytest
import os
from django.conf import settings
from django.db import connection


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


class TenantContextManager:
    """Helper para gerenciar contexto de tenant em testes RLS."""
    
    def set(self, tenant_id: str):
        """Define o tenant_id para a conexão atual."""
        with connection.cursor() as cursor:
            cursor.execute("SET LOCAL app.tenant_id = %s", [tenant_id])
    
    def clear(self):
        """Remove o tenant_id da conexão atual."""
        with connection.cursor() as cursor:
            cursor.execute("RESET app.tenant_id")
    
    def get(self) -> str | None:
        """Obtém o tenant_id atual."""
        with connection.cursor() as cursor:
            cursor.execute("SHOW app.tenant_id")
            result = cursor.fetchone()
            return result[0] if result else None


@pytest.fixture
def db_tenant(django_db_setup, db):
    """
    Helper para configurar tenant_id via GUC.
    
    Permite testar RLS (Row Level Security) de forma isolada.
    
    Example:
        def test_tenant_isolation(db_tenant):
            db_tenant.set('tenant-123')
            # Queries agora retornam apenas dados do tenant-123
            
            db_tenant.clear()
            # RLS bloqueia tudo (nenhum tenant configurado)
    """
    manager = TenantContextManager()
    yield manager
    # Cleanup: remover tenant após teste
    manager.clear()


@pytest.fixture(autouse=True)
def reset_timezone():
    """
    Garante TZ=UTC para todos os testes (determinismo).
    
    Executado automaticamente antes de cada teste.
    """
    original_tz = os.environ.get('TZ')
    os.environ['TZ'] = 'UTC'
    
    # Reinicializar timezone do Django
    import time
    time.tzset()
    
    yield
    
    # Restaurar TZ original
    if original_tz:
        os.environ['TZ'] = original_tz
    else:
        os.environ.pop('TZ', None)
    time.tzset()


@pytest.fixture
def freezer():
    """
    Fixture para congelar tempo usando freezegun.
    
    Requer: pip install freezegun
    
    Example:
        def test_with_time(freezer):
            freezer.move_to('2025-01-01 00:00:00')
            # código que depende de tempo
    """
    try:
        from freezegun import freeze_time
        with freeze_time('2025-01-01 00:00:00') as frozen:
            yield frozen
    except ImportError:
        pytest.skip("freezegun não instalado")
