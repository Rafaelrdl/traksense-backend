"""
Admin configuration for Tenant models.
"""

from django.contrib import admin
from django.utils.html import format_html
from django_tenants.admin import TenantAdminMixin

from .models import Domain, Tenant


@admin.register(Tenant)
class TenantAdmin(TenantAdminMixin, admin.ModelAdmin):
    """Admin interface for Tenant model."""
    
    list_display = ['name', 'slug', 'schema_name', 'domain_count', 'status_badge', 'created_at']
    search_fields = ['name', 'slug', 'schema_name']
    readonly_fields = ['schema_name', 'created_at', 'updated_at']
    list_per_page = 25
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('name', 'slug'),
            'description': 'Nome e identificador único do tenant/organização.'
        }),
        ('Schema e Timestamps', {
            'fields': ('schema_name', 'created_at', 'updated_at'),
            'classes': ('collapse',),
            'description': 'Schema PostgreSQL e datas de criação/modificação (gerados automaticamente).'
        }),
    )
    
    def domain_count(self, obj):
        """Número de domínios associados."""
        count = obj.domains.count()
        return format_html('<span style="color: #0066cc; font-weight: bold;">{}</span>', count)
    domain_count.short_description = '🌐 Domínios'
    
    def status_badge(self, obj):
        """Badge de status visual."""
        return format_html(
            '<span style="background-color: #28a745; color: white; padding: 3px 10px; border-radius: 3px; font-size: 11px;">✓ ATIVO</span>'
        )
    status_badge.short_description = 'Status'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('domains')


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    """Admin interface for Domain model."""
    
    list_display = ['domain', 'tenant_link', 'schema_badge', 'primary_badge']
    list_filter = ['is_primary', 'tenant']
    search_fields = ['domain', 'tenant__name', 'tenant__slug']
    raw_id_fields = ['tenant']
    list_per_page = 50
    
    fieldsets = (
        ('Configuração do Domain', {
            'fields': ('domain', 'tenant', 'is_primary'),
            'description': 'Configure o hostname que será resolvido para este tenant.'
        }),
    )
    
    def tenant_link(self, obj):
        """Link para o tenant."""
        return format_html(
            '<a href="/admin/tenants/tenant/{}/change/" style="color: #0066cc; text-decoration: none;">'
            '🏢 {}</a>',
            obj.tenant.id,
            obj.tenant.name
        )
    tenant_link.short_description = 'Tenant'
    
    def schema_badge(self, obj):
        """Schema do tenant."""
        return format_html(
            '<code style="background-color: #f4f4f4; padding: 2px 6px; border-radius: 3px; font-size: 11px;">{}</code>',
            obj.tenant.schema_name
        )
    schema_badge.short_description = 'Schema'
    
    def primary_badge(self, obj):
        """Badge de domínio primário."""
        if obj.is_primary:
            return format_html('<span style="color: #28a745; font-weight: bold;">⭐ Primário</span>')
        return format_html('<span style="color: #999;">Secundário</span>')
    primary_badge.short_description = 'Tipo'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('tenant')
