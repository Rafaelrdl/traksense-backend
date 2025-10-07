"""
Admin - Dashboards App

Interface administrativa para gerenciar templates e configurações de dashboards.

Regras RBAC:
-----------
- internal_ops: CRUD completo em todos os modelos
- customer_admin: somente leitura (view)
- viewer: somente leitura (view)

Imutabilidade:
-------------
- DashboardTemplates com superseded_by preenchido ficam read-only no admin

Autor: TrakSense Team
Data: 2025-10-07 (Fase 2)
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
import json
from .models import DashboardTemplate, DashboardConfig


# ==============================================================================
# DASHBOARD TEMPLATE ADMIN
# ==============================================================================

@admin.register(DashboardTemplate)
class DashboardTemplateAdmin(admin.ModelAdmin):
    """
    Admin para DashboardTemplate.
    
    Features:
    - Validação automática de JSON contra schema
    - Preview formatado do JSON
    - Status de depreciação
    - Campos read-only quando depreciado
    """
    
    list_display = ['device_template', 'schema', 'version', 'status_badge', 'created_at']
    list_filter = ['schema', 'device_template', 'created_at']
    search_fields = ['device_template__code', 'device_template__name']
    readonly_fields = ['id', 'json_preview', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Identificação', {
            'fields': ('id', 'device_template', 'schema', 'version')
        }),
        ('Estrutura JSON', {
            'fields': ('json', 'json_preview'),
            'description': 'JSON deve estar no formato do schema v1 (validação automática)'
        }),
        ('Versionamento', {
            'fields': ('superseded_by',),
            'classes': ('collapse',)
        }),
        ('Metadados', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        """Badge visual de status (ativo/depreciado)"""
        if obj.is_deprecated:
            return format_html(
                '<span style="color: red; font-weight: bold;">⚠ DEPRECIADO</span>'
            )
        return format_html(
            '<span style="color: green; font-weight: bold;">✓ ATIVO</span>'
        )
    status_badge.short_description = 'Status'
    
    def json_preview(self, obj):
        """Preview formatado do JSON (read-only)"""
        if obj.json:
            formatted = json.dumps(obj.json, indent=2, ensure_ascii=False)
            return mark_safe(f'<pre style="background: #f4f4f4; padding: 10px; border-radius: 4px;">{formatted}</pre>')
        return '-'
    json_preview.short_description = 'Preview JSON'
    
    def get_readonly_fields(self, request, obj=None):
        """Torna campos read-only se template está depreciado"""
        readonly = list(super().get_readonly_fields(request, obj))
        
        if obj and obj.is_deprecated:
            # Template depreciado - tudo read-only exceto superseded_by
            readonly.extend(['device_template', 'schema', 'version', 'json'])
        
        return readonly
    
    def has_change_permission(self, request, obj=None):
        """Permite edição apenas para internal_ops"""
        if not request.user.groups.filter(name='internal_ops').exists():
            return False
        return super().has_change_permission(request, obj)
    
    def has_delete_permission(self, request, obj=None):
        """Permite deleção apenas para internal_ops"""
        if not request.user.groups.filter(name='internal_ops').exists():
            return False
        return super().has_delete_permission(request, obj)
    
    def has_add_permission(self, request):
        """Permite criação apenas para internal_ops"""
        if not request.user.groups.filter(name='internal_ops').exists():
            return False
        return super().has_add_permission(request)


# ==============================================================================
# DASHBOARD CONFIG ADMIN
# ==============================================================================

@admin.register(DashboardConfig)
class DashboardConfigAdmin(admin.ModelAdmin):
    """
    Admin para DashboardConfig.
    
    Features:
    - Preview formatado do JSON
    - Link para o Device
    - Somente leitura (gerado automaticamente pelo serviço)
    """
    
    list_display = ['device', 'template_version', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['device__name']
    readonly_fields = ['id', 'device', 'template_version', 'json_preview', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Identificação', {
            'fields': ('id', 'device', 'template_version')
        }),
        ('Configuração JSON', {
            'fields': ('json', 'json_preview'),
            'description': 'JSON filtrado por pontos contratados (gerado automaticamente)'
        }),
        ('Metadados', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def json_preview(self, obj):
        """Preview formatado do JSON (read-only)"""
        if obj.json:
            formatted = json.dumps(obj.json, indent=2, ensure_ascii=False)
            return mark_safe(f'<pre style="background: #f4f4f4; padding: 10px; border-radius: 4px; max-height: 400px; overflow-y: auto;">{formatted}</pre>')
        return '-'
    json_preview.short_description = 'Preview JSON'
    
    def has_change_permission(self, request, obj=None):
        """DashboardConfig é gerado automaticamente - não permite edição"""
        # Apenas visualização permitida
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Apenas internal_ops pode deletar (para reprovisionar)"""
        if not request.user.groups.filter(name='internal_ops').exists():
            return False
        return super().has_delete_permission(request, obj)
    
    def has_add_permission(self, request):
        """DashboardConfig é gerado automaticamente - não permite criação manual"""
        return False
