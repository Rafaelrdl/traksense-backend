"""
Admin configuration for Tenant models.
"""

from django.contrib import admin
from django_tenants.admin import TenantAdminMixin

from .models import Domain, Tenant


@admin.register(Tenant)
class TenantAdmin(TenantAdminMixin, admin.ModelAdmin):
    """Admin interface for Tenant model."""
    
    list_display = ['name', 'slug', 'schema_name', 'created_at']
    search_fields = ['name', 'slug', 'schema_name']
    readonly_fields = ['schema_name', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('name', 'slug')
        }),
        ('Schema e Timestamps', {
            'fields': ('schema_name', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    """Admin interface for Domain model."""
    
    list_display = ['domain', 'tenant', 'is_primary']
    list_filter = ['is_primary']
    search_fields = ['domain', 'tenant__name']
    
    fieldsets = (
        (None, {
            'fields': ('domain', 'tenant', 'is_primary')
        }),
    )
