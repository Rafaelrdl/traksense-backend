"""
Pytest configuration for TrakSense backend tests.
"""
import pytest
from django.conf import settings


@pytest.fixture(scope='session')
def django_db_setup():
    """Django database setup for tests."""
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
    """DRF API test client."""
    from rest_framework.test import APIClient
    return APIClient()
