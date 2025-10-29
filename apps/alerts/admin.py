"""
Admin para o sistema de Alertas e Regras
"""
from django.contrib import admin
from .models import Rule, Alert, NotificationPreference


@admin.register(Rule)
class RuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'equipment', 'severity', 'enabled', 'created_at']
    list_filter = ['enabled', 'severity', 'created_at']
    search_fields = ['name', 'description', 'equipment__name', 'equipment__tag']
    readonly_fields = ['created_at', 'updated_at', 'created_by']
    fieldsets = (
        ('Identificação', {
            'fields': ('name', 'description')
        }),
        ('Equipamento e Parâmetro', {
            'fields': ('equipment', 'parameter_key', 'variable_key')
        }),
        ('Condição', {
            'fields': ('operator', 'threshold', 'unit', 'duration')
        }),
        ('Severidade e Ações', {
            'fields': ('severity', 'actions')
        }),
        ('Estado', {
            'fields': ('enabled',)
        }),
        ('Informações do Sistema', {
            'fields': ('created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ['asset_tag', 'severity', 'message_preview', 'triggered_at', 'acknowledged', 'resolved']
    list_filter = ['severity', 'acknowledged', 'resolved', 'triggered_at']
    search_fields = ['asset_tag', 'message', 'parameter_key']
    readonly_fields = ['triggered_at', 'acknowledged_at', 'acknowledged_by', 'resolved_at', 'resolved_by']
    fieldsets = (
        ('Alerta', {
            'fields': ('rule', 'message', 'severity')
        }),
        ('Dados', {
            'fields': ('asset_tag', 'parameter_key', 'parameter_value', 'threshold')
        }),
        ('Estado', {
            'fields': ('triggered_at',)
        }),
        ('Reconhecimento', {
            'fields': ('acknowledged', 'acknowledged_at', 'acknowledged_by')
        }),
        ('Resolução', {
            'fields': ('resolved', 'resolved_at', 'resolved_by')
        }),
        ('Notas', {
            'fields': ('notes',)
        }),
    )
    
    def message_preview(self, obj):
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    message_preview.short_description = 'Mensagem'


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'email_enabled', 'push_enabled', 'sms_enabled', 'whatsapp_enabled']
    list_filter = ['email_enabled', 'push_enabled', 'sms_enabled', 'whatsapp_enabled']
    search_fields = ['user__email', 'phone_number', 'whatsapp_number']
    readonly_fields = ['updated_at']
    fieldsets = (
        ('Usuário', {
            'fields': ('user',)
        }),
        ('Canais de Notificação', {
            'fields': ('email_enabled', 'push_enabled', 'sound_enabled', 'sms_enabled', 'whatsapp_enabled')
        }),
        ('Severidades', {
            'fields': ('critical_alerts', 'high_alerts', 'medium_alerts', 'low_alerts')
        }),
        ('Contatos', {
            'fields': ('phone_number', 'whatsapp_number')
        }),
        ('Informações do Sistema', {
            'fields': ('updated_at',),
            'classes': ('collapse',)
        }),
    )

