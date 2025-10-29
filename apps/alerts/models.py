"""
Models para o sistema de Alertas e Regras

Tenant isolation é automático via django-tenants (PostgreSQL schemas).
Todos os models herdam de models.Model e são isolados por schema.
"""
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Rule(models.Model):
    """
    Regra de monitoramento de equipamentos.
    Define condições que quando satisfeitas disparam alertas.
    """
    
    OPERATOR_CHOICES = [
        ('>', 'Maior que'),
        ('>=', 'Maior ou igual'),
        ('<', 'Menor que'),
        ('<=', 'Menor ou igual'),
        ('==', 'Igual'),
        ('!=', 'Diferente'),
    ]
    
    SEVERITY_CHOICES = [
        ('Critical', 'Crítico'),
        ('High', 'Alto'),
        ('Medium', 'Médio'),
        ('Low', 'Baixo'),
    ]
    
    # Identificação
    name = models.CharField(max_length=200, verbose_name='Nome da Regra')
    description = models.TextField(blank=True, verbose_name='Descrição')
    
    # Equipamento e Parâmetro
    equipment = models.ForeignKey(
        'assets.Asset',
        on_delete=models.CASCADE,
        related_name='rules',
        verbose_name='Equipamento'
    )
    parameter_key = models.CharField(max_length=100, verbose_name='Chave do Parâmetro')
    variable_key = models.CharField(max_length=100, blank=True, verbose_name='Chave da Variável')
    
    # Condição
    operator = models.CharField(max_length=10, choices=OPERATOR_CHOICES, verbose_name='Operador')
    threshold = models.FloatField(verbose_name='Valor Limite')
    unit = models.CharField(max_length=50, blank=True, verbose_name='Unidade')
    duration = models.IntegerField(default=5, verbose_name='Duração (minutos)')
    
    # Severidade e Ações
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='Medium', verbose_name='Severidade')
    actions = models.JSONField(
        default=list,
        verbose_name='Ações ao Disparar',
        help_text='Lista de canais de notificação: EMAIL, IN_APP, SMS, WHATSAPP'
    )
    
    # Estado
    enabled = models.BooleanField(default=True, verbose_name='Ativa')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_rules',
        verbose_name='Criado por'
    )
    
    class Meta:
        db_table = 'alerts_rule'
        verbose_name = 'Regra'
        verbose_name_plural = 'Regras'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['equipment', 'enabled']),
            models.Index(fields=['severity', 'enabled']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.equipment.name if self.equipment else 'N/A'}"
    
    def get_condition_display(self):
        """Retorna a condição formatada para exibição"""
        operator_symbols = {
            '>': '>',
            '>=': '≥',
            '<': '<',
            '<=': '≤',
            '==': '=',
            '!=': '≠',
        }
        symbol = operator_symbols.get(self.operator, self.operator)
        return f"{self.parameter_key} {symbol} {self.threshold} {self.unit}"


class Alert(models.Model):
    """
    Alerta disparado quando uma regra é violada.
    """
    
    # Regra que disparou o alerta
    rule = models.ForeignKey(
        Rule,
        on_delete=models.CASCADE,
        related_name='alerts',
        verbose_name='Regra'
    )
    
    # Dados do alerta
    message = models.TextField(verbose_name='Mensagem')
    severity = models.CharField(max_length=20, verbose_name='Severidade')
    asset_tag = models.CharField(max_length=100, verbose_name='Tag do Equipamento')
    parameter_key = models.CharField(max_length=100, verbose_name='Parâmetro')
    parameter_value = models.FloatField(verbose_name='Valor do Parâmetro')
    threshold = models.FloatField(verbose_name='Limite')
    
    # Estado do alerta
    triggered_at = models.DateTimeField(auto_now_add=True, verbose_name='Disparado em')
    
    acknowledged = models.BooleanField(default=False, verbose_name='Reconhecido')
    acknowledged_at = models.DateTimeField(null=True, blank=True, verbose_name='Reconhecido em')
    acknowledged_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='acknowledged_alerts',
        verbose_name='Reconhecido por'
    )
    
    resolved = models.BooleanField(default=False, verbose_name='Resolvido')
    resolved_at = models.DateTimeField(null=True, blank=True, verbose_name='Resolvido em')
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_alerts',
        verbose_name='Resolvido por'
    )
    
    # Notas
    notes = models.TextField(blank=True, verbose_name='Notas')
    
    class Meta:
        db_table = 'alerts_alert'
        verbose_name = 'Alerta'
        verbose_name_plural = 'Alertas'
        ordering = ['-triggered_at']
        indexes = [
            models.Index(fields=['rule', 'triggered_at']),
            models.Index(fields=['acknowledged', 'resolved']),
            models.Index(fields=['severity', 'triggered_at']),
            models.Index(fields=['asset_tag']),
        ]
    
    def __str__(self):
        status = 'Resolvido' if self.resolved else ('Reconhecido' if self.acknowledged else 'Ativo')
        return f"[{status}] {self.asset_tag} - {self.message[:50]}"
    
    @property
    def is_active(self):
        """Verifica se o alerta está ativo (não reconhecido e não resolvido)"""
        return not self.acknowledged and not self.resolved


class NotificationPreference(models.Model):
    """
    Preferências de notificação por usuário.
    Define como cada usuário deseja receber notificações de alertas.
    """
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='notification_preferences',
        verbose_name='Usuário'
    )
    
    # Canais de Notificação
    email_enabled = models.BooleanField(default=True, verbose_name='Email Ativo')
    push_enabled = models.BooleanField(default=True, verbose_name='Push Ativo')
    sound_enabled = models.BooleanField(default=True, verbose_name='Som Ativo')
    sms_enabled = models.BooleanField(default=False, verbose_name='SMS Ativo')
    whatsapp_enabled = models.BooleanField(default=False, verbose_name='WhatsApp Ativo')
    
    # Severidades
    critical_alerts = models.BooleanField(default=True, verbose_name='Alertas Críticos')
    high_alerts = models.BooleanField(default=True, verbose_name='Alertas Altos')
    medium_alerts = models.BooleanField(default=True, verbose_name='Alertas Médios')
    low_alerts = models.BooleanField(default=False, verbose_name='Alertas Baixos')
    
    # Contatos
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Número de Telefone',
        help_text='Para SMS (formato: +55XXXXXXXXXXX)'
    )
    whatsapp_number = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Número WhatsApp',
        help_text='Para WhatsApp (formato: +55XXXXXXXXXXX)'
    )
    
    # Timestamps
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    
    class Meta:
        db_table = 'alerts_notification_preference'
        verbose_name = 'Preferência de Notificação'
        verbose_name_plural = 'Preferências de Notificação'
    
    def __str__(self):
        return f"Preferências de {self.user.email}"
    
    def should_notify_severity(self, severity: str) -> bool:
        """Verifica se o usuário quer receber alertas desta severidade"""
        severity_map = {
            'Critical': self.critical_alerts,
            'High': self.high_alerts,
            'Medium': self.medium_alerts,
            'Low': self.low_alerts,
        }
        return severity_map.get(severity, True)
    
    def get_enabled_channels(self) -> list:
        """Retorna lista de canais de notificação habilitados"""
        channels = []
        if self.email_enabled:
            channels.append('EMAIL')
        if self.push_enabled:
            channels.append('IN_APP')
        if self.sms_enabled and self.phone_number:
            channels.append('SMS')
        if self.whatsapp_enabled and self.whatsapp_number:
            channels.append('WHATSAPP')
        return channels

