"""
Serializers para o sistema de Alertas e Regras
"""
from rest_framework import serializers
from django.utils import timezone
from .models import Rule, Alert, NotificationPreference


class RuleSerializer(serializers.ModelSerializer):
    """Serializer para Rule"""
    
    equipment_name = serializers.CharField(source='equipment.name', read_only=True)
    equipment_tag = serializers.CharField(source='equipment.tag', read_only=True)
    created_by_email = serializers.CharField(source='created_by.email', read_only=True)
    condition_display = serializers.CharField(source='get_condition_display', read_only=True)
    
    class Meta:
        model = Rule
        fields = [
            'id',
            'name',
            'description',
            'equipment',
            'equipment_name',
            'equipment_tag',
            'parameter_key',
            'variable_key',
            'operator',
            'threshold',
            'unit',
            'duration',
            'severity',
            'actions',
            'enabled',
            'created_at',
            'updated_at',
            'created_by',
            'created_by_email',
            'condition_display',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']
    
    def validate_actions(self, value):
        """Valida que actions seja uma lista de strings válidas"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Actions deve ser uma lista.")
        
        valid_actions = ['EMAIL', 'IN_APP', 'SMS', 'WHATSAPP']
        for action in value:
            if action not in valid_actions:
                raise serializers.ValidationError(
                    f"Ação '{action}' inválida. Opções: {', '.join(valid_actions)}"
                )
        
        if not value:
            raise serializers.ValidationError("Selecione pelo menos uma ação.")
        
        return value
    
    def validate_duration(self, value):
        """Valida que duration seja positivo"""
        if value <= 0:
            raise serializers.ValidationError("Duração deve ser maior que zero.")
        return value
    
    def validate_threshold(self, value):
        """Valida que threshold seja um número válido"""
        if not isinstance(value, (int, float)):
            raise serializers.ValidationError("Valor limite deve ser um número.")
        return value


class AlertSerializer(serializers.ModelSerializer):
    """Serializer para Alert"""
    
    rule_name = serializers.CharField(source='rule.name', read_only=True)
    equipment_name = serializers.CharField(source='rule.equipment.name', read_only=True)
    acknowledged_by_email = serializers.CharField(source='acknowledged_by.email', read_only=True)
    resolved_by_email = serializers.CharField(source='resolved_by.email', read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Alert
        fields = [
            'id',
            'rule',
            'rule_name',
            'equipment_name',
            'message',
            'severity',
            'asset_tag',
            'parameter_key',
            'parameter_value',
            'threshold',
            'triggered_at',
            'acknowledged',
            'acknowledged_at',
            'acknowledged_by',
            'acknowledged_by_email',
            'resolved',
            'resolved_at',
            'resolved_by',
            'resolved_by_email',
            'notes',
            'is_active',
        ]
        read_only_fields = [
            'id',
            'triggered_at',
            'acknowledged_at',
            'acknowledged_by',
            'resolved_at',
            'resolved_by',
        ]


class AcknowledgeAlertSerializer(serializers.Serializer):
    """Serializer para reconhecer um alerta"""
    notes = serializers.CharField(required=False, allow_blank=True)


class ResolveAlertSerializer(serializers.Serializer):
    """Serializer para resolver um alerta"""
    notes = serializers.CharField(required=False, allow_blank=True)


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    """Serializer para NotificationPreference"""
    
    user_email = serializers.CharField(source='user.email', read_only=True)
    enabled_channels = serializers.ListField(source='get_enabled_channels', read_only=True)
    
    class Meta:
        model = NotificationPreference
        fields = [
            'id',
            'user',
            'user_email',
            'email_enabled',
            'push_enabled',
            'sound_enabled',
            'sms_enabled',
            'whatsapp_enabled',
            'critical_alerts',
            'high_alerts',
            'medium_alerts',
            'low_alerts',
            'phone_number',
            'whatsapp_number',
            'updated_at',
            'enabled_channels',
        ]
        read_only_fields = ['id', 'user', 'updated_at']
    
    def validate_phone_number(self, value):
        """Valida formato do telefone"""
        if value and not value.startswith('+'):
            raise serializers.ValidationError(
                "Número de telefone deve começar com '+' e incluir código do país (ex: +5511999999999)"
            )
        return value
    
    def validate_whatsapp_number(self, value):
        """Valida formato do WhatsApp"""
        if value and not value.startswith('+'):
            raise serializers.ValidationError(
                "Número de WhatsApp deve começar com '+' e incluir código do país (ex: +5511999999999)"
            )
        return value
    
    def validate(self, data):
        """Validações cruzadas"""
        # Se SMS está habilitado, deve ter telefone
        if data.get('sms_enabled') and not data.get('phone_number'):
            raise serializers.ValidationError({
                'phone_number': 'Número de telefone é obrigatório quando SMS está ativado.'
            })
        
        # Se WhatsApp está habilitado, deve ter número
        if data.get('whatsapp_enabled') and not data.get('whatsapp_number'):
            raise serializers.ValidationError({
                'whatsapp_number': 'Número de WhatsApp é obrigatório quando WhatsApp está ativado.'
            })
        
        return data


class AlertStatisticsSerializer(serializers.Serializer):
    """Serializer para estatísticas de alertas"""
    total = serializers.IntegerField()
    active = serializers.IntegerField()
    acknowledged = serializers.IntegerField()
    resolved = serializers.IntegerField()
    by_severity = serializers.DictField()
