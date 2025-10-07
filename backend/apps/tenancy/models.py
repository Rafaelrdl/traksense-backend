"""
Tenant models for multi-tenancy using django-tenants.
Each tenant gets its own schema for metadata.
Telemetry data lives in public.ts_measure with RLS.
"""
from django.db import models
from django_tenants.models import TenantMixin, DomainMixin


class Client(TenantMixin):
    """
    Tenant model. Each client gets a dedicated schema.
    """
    name = models.CharField(max_length=200, help_text="Nome do tenant/cliente")
    
    # Auto-create schema on save (útil em dev)
    auto_create_schema = True
    
    # Additional metadata
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Tenant"
        verbose_name_plural = "Tenants"
    
    def __str__(self):
        return self.name


class Domain(DomainMixin):
    """
    Domain model for tenant routing.
    django-tenants uses domain to identify the tenant.
    """
    pass
