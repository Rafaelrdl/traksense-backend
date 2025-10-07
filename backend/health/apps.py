"""
Health App Config - Health check básico

App minimalista para endpoint /health (monitoramento).

Autor: TrakSense Team
Data: 2025-10-07
"""
from django.apps import AppConfig


class HealthConfig(AppConfig):
    """Config do app Health."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'health'
    verbose_name = 'Health Check'
