"""
Admin - Devices App

Interface administrativa para gerenciar templates e dispositivos IoT.

Regras RBAC:
-----------
- internal_ops: CRUD completo em todos os modelos
- customer_admin: somente leitura (view)
- viewer: somente leitura (view)

Imutabilidade:
-------------
- Templates com superseded_by preenchido ficam read-only no admin

Provisionamento:
---------------
- Ao salvar um Device, provision_device_from_template() é chamado automaticamente

Autor: TrakSense Team
Data: 2025-10-07 (Fase 2)
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import DeviceTemplate, PointTemplate, Device, Point
from .services import provision_device_from_template


# ==============================================================================
# INLINE ADMINS
# ==============================================================================

class PointTemplateInline(admin.TabularInline):
    """Inline para exibir PointTemplates dentro de DeviceTemplate"""
    model = PointTemplate
    extra = 1
    fields = ['name', 'label', 'ptype', 'unit', 'enum_values', 'polarity', 'hysteresis']
    
    def has_delete_permission(self, request, obj=None):
        """Impede deletar PointTemplate se o DeviceTemplate está depreciado"""
        if obj and obj.superseded_by:
            return False
        return super().has_delete_permission(request, obj)


class PointInline(admin.TabularInline):
    """Inline para exibir Points dentro de Device (somente leitura)"""
    model = Point
    extra = 0
    fields = ['name', 'label', 'unit', 'polarity', 'is_contracted', 'limits']
    readonly_fields = ['name', 'label', 'unit', 'polarity']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        """Points são criados via provisionamento, não manualmente"""
        return False


# ==============================================================================
# DEVICE TEMPLATE ADMIN
# ==============================================================================

@admin.register(DeviceTemplate)
class DeviceTemplateAdmin(admin.ModelAdmin):
    """
    Admin para DeviceTemplate.
    
    Features:
    - Lista com status de depreciação
    - Inline de PointTemplates
    - Campos read-only quando depreciado
    """
    
    list_display = ['code', 'name', 'version', 'status_badge', 'created_at']
    list_filter = ['created_at']
    search_fields = ['code', 'name', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']
    inlines = [PointTemplateInline]
    
    fieldsets = (
        ('Identificação', {
            'fields': ('id', 'code', 'name', 'version')
        }),
        ('Versionamento', {
            'fields': ('superseded_by', 'description'),
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
    
    def get_readonly_fields(self, request, obj=None):
        """Torna campos read-only se template está depreciado"""
        readonly = list(super().get_readonly_fields(request, obj))
        
        if obj and obj.is_deprecated:
            # Template depreciado - tudo read-only exceto superseded_by
            readonly.extend(['code', 'name', 'version', 'description'])
        
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
# POINT TEMPLATE ADMIN
# ==============================================================================

@admin.register(PointTemplate)
class PointTemplateAdmin(admin.ModelAdmin):
    """Admin para PointTemplate (caso precisem editar fora do inline)"""
    
    list_display = ['name', 'device_template', 'ptype', 'unit', 'polarity']
    list_filter = ['ptype', 'polarity', 'device_template']
    search_fields = ['name', 'label']
    readonly_fields = ['id', 'created_at']
    
    fieldsets = (
        ('Identificação', {
            'fields': ('id', 'device_template', 'name', 'label')
        }),
        ('Tipo e Valores', {
            'fields': ('ptype', 'unit', 'enum_values')
        }),
        ('Configurações', {
            'fields': ('polarity', 'hysteresis', 'default_limits')
        }),
        ('Metadados', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
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
# DEVICE ADMIN
# ==============================================================================

@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    """
    Admin para Device.
    
    Features:
    - Provisionamento automático ao salvar (cria Points e DashboardConfig)
    - Inline de Points (read-only)
    - Status visual
    """
    
    list_display = ['name', 'template', 'status', 'site_id', 'created_at']
    list_filter = ['status', 'template', 'created_at']
    search_fields = ['name', 'site_id']
    readonly_fields = ['id', 'created_at', 'updated_at']
    inlines = [PointInline]
    
    fieldsets = (
        ('Identificação', {
            'fields': ('id', 'template', 'name', 'site_id')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('MQTT (Fase 3)', {
            'fields': ('topic_base', 'credentials_id'),
            'classes': ('collapse',),
            'description': 'Campos reservados para Fase 3 (provisionamento EMQX)'
        }),
        ('Metadados', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """
        Salva Device e executa provisionamento automático.
        
        Se é novo Device ou se foi alterado, chama provision_device_from_template()
        para gerar Points e DashboardConfig automaticamente.
        """
        is_new = obj.pk is None
        super().save_model(request, obj, form, change)
        
        # Provisionar apenas se é novo (evita reprovisionar a cada save)
        if is_new:
            provision_device_from_template(obj)
            
            # Mensagem de sucesso customizada
            self.message_user(
                request,
                f'Device "{obj.name}" criado e provisionado com sucesso! '
                f'Points e DashboardConfig gerados automaticamente.'
            )
    
    def has_change_permission(self, request, obj=None):
        """internal_ops: change completo; customer_admin: view only"""
        if request.user.groups.filter(name='internal_ops').exists():
            return True
        # customer_admin e viewer podem ver mas não editar (tratado em get_readonly_fields)
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Apenas internal_ops pode deletar"""
        if not request.user.groups.filter(name='internal_ops').exists():
            return False
        return super().has_delete_permission(request, obj)
    
    def has_add_permission(self, request):
        """Apenas internal_ops pode criar"""
        if not request.user.groups.filter(name='internal_ops').exists():
            return False
        return super().has_add_permission(request)


# ==============================================================================
# POINT ADMIN
# ==============================================================================

@admin.register(Point)
class PointAdmin(admin.ModelAdmin):
    """
    Admin para Point.
    
    Nota: Points normalmente são gerenciados via inline no DeviceAdmin.
    Este admin existe para casos de edição direta (ex: ajustar limites).
    """
    
    list_display = ['name', 'device', 'label', 'unit', 'is_contracted']
    list_filter = ['is_contracted', 'polarity', 'device']
    search_fields = ['name', 'label', 'device__name']
    readonly_fields = ['id', 'device', 'template', 'name', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Identificação', {
            'fields': ('id', 'device', 'template', 'name', 'label')
        }),
        ('Configurações', {
            'fields': ('unit', 'polarity', 'is_contracted')
        }),
        ('Limites', {
            'fields': ('limits',),
            'description': 'Limites customizados (JSON) - editável pelo cliente futuramente'
        }),
        ('Metadados', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_change_permission(self, request, obj=None):
        """internal_ops: change completo"""
        if request.user.groups.filter(name='internal_ops').exists():
            return True
        # No futuro, customer_admin poderá editar limits
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Apenas internal_ops pode deletar"""
        if not request.user.groups.filter(name='internal_ops').exists():
            return False
        return super().has_delete_permission(request, obj)
    
    def has_add_permission(self, request):
        """Points são criados via provisionamento, não manualmente"""
        return False
