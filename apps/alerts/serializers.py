"""
Serializers para o sistema de Alertas e Regras
"""
from rest_framework import serializers
from django.utils import timezone
from .models import Rule, RuleParameter, Alert, NotificationPreference


class RuleParameterSerializer(serializers.ModelSerializer):
    """Serializer para RuleParameter"""
    
    class Meta:
        model = RuleParameter
        fields = [
            'id',
            'parameter_key',
            'variable_key',
            'operator',
            'threshold',
            'unit',
            'duration',
            'severity',
            'message_template',
            'order',
        ]
        read_only_fields = ['id']
        # Tornar alguns campos opcionais para evitar erros
        extra_kwargs = {
            'variable_key': {'required': False, 'allow_blank': True},
            'unit': {'required': False, 'allow_blank': True},
            'order': {'required': False, 'default': 0},
        }
    
    def validate_duration(self, value):
        """Valida que duration seja positivo"""
        if value is not None and value <= 0:
            raise serializers.ValidationError("Duração deve ser maior que zero.")
        return value
    
    def validate_threshold(self, value):
        """Valida que threshold seja um número válido"""
        if value is None:
            raise serializers.ValidationError("Valor limite é obrigatório.")
        if not isinstance(value, (int, float)):
            raise serializers.ValidationError("Valor limite deve ser um número.")
        return value


class RuleSerializer(serializers.ModelSerializer):
    """Serializer para Rule com suporte a múltiplos parâmetros"""
    
    equipment_name = serializers.CharField(source='equipment.name', read_only=True)
    equipment_tag = serializers.CharField(source='equipment.tag', read_only=True)
    created_by_email = serializers.CharField(source='created_by.email', read_only=True)
    condition_display = serializers.CharField(source='get_condition_display', read_only=True)
    
    # Nested serializer para múltiplos parâmetros
    parameters = RuleParameterSerializer(many=True, required=False)
    
    class Meta:
        model = Rule
        fields = [
            'id',
            'name',
            'description',
            'equipment',
            'equipment_name',
            'equipment_tag',
            # Campo write_only para aceitar do frontend
            'parameters',
            # Campos antigos (mantidos para compatibilidade)
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
        if value is not None and value <= 0:
            raise serializers.ValidationError("Duração deve ser maior que zero.")
        return value
    
    def validate_threshold(self, value):
        """Valida que threshold seja um número válido"""
        if value is not None and not isinstance(value, (int, float)):
            raise serializers.ValidationError("Valor limite deve ser um número.")
        return value
    
    def validate(self, data):
        """Validação geral - deve ter parameters OU campos antigos"""
        parameters = data.get('parameters', [])
        has_old_format = data.get('parameter_key') is not None
        
        # Se veio parameters, validar que tem pelo menos um
        if 'parameters' in data and not parameters:
            raise serializers.ValidationError({
                'parameters': "Adicione pelo menos um parâmetro."
            })
        
        # Se não veio nem parameters nem formato antigo, erro
        if 'parameters' not in data and not has_old_format:
            raise serializers.ValidationError(
                "Forneça 'parameters' (novo formato) ou campos de parâmetro único (formato antigo)."
            )
        
        return data
    
    def create(self, validated_data):
        """Cria regra com parâmetros aninhados"""
        parameters_data = validated_data.pop('parameters', [])
        
        # Manter compatibilidade: se veio parameters, usar o primeiro nos campos antigos
        if parameters_data:
            first_param = parameters_data[0]
            validated_data['parameter_key'] = first_param.get('parameter_key')
            validated_data['variable_key'] = first_param.get('variable_key', '')
            validated_data['operator'] = first_param.get('operator')
            validated_data['threshold'] = first_param.get('threshold')
            validated_data['unit'] = first_param.get('unit', '')
            validated_data['duration'] = first_param.get('duration', 5)
            validated_data['severity'] = first_param.get('severity', 'Medium')
        
        # Criar a regra
        rule = Rule.objects.create(**validated_data)
        
        # Criar os parâmetros na tabela RuleParameter
        if parameters_data:
            for idx, param_data in enumerate(parameters_data):
                param_data['order'] = idx
                RuleParameter.objects.create(rule=rule, **param_data)
        
        return rule
    
    def update(self, instance, validated_data):
        """Atualiza regra e seus parâmetros"""
        parameters_data = validated_data.pop('parameters', None)
        
        # Manter compatibilidade: se veio parameters, atualizar campos antigos também
        if parameters_data:
            first_param = parameters_data[0]
            validated_data['parameter_key'] = first_param.get('parameter_key')
            validated_data['variable_key'] = first_param.get('variable_key', '')
            validated_data['operator'] = first_param.get('operator')
            validated_data['threshold'] = first_param.get('threshold')
            validated_data['unit'] = first_param.get('unit', '')
            validated_data['duration'] = first_param.get('duration', 5)
            validated_data['severity'] = first_param.get('severity', 'Medium')
        
        # Atualizar campos da regra
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Atualizar os parâmetros na tabela RuleParameter
        if parameters_data is not None:
            # Deletar parâmetros existentes
            instance.parameters.all().delete()
            
            # Criar novos parâmetros
            for idx, param_data in enumerate(parameters_data):
                param_data['order'] = idx
                RuleParameter.objects.create(rule=instance, **param_data)
        
        return instance


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
