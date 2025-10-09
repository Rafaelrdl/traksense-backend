"""
Models - Rules App (TENANT_APPS)

Modelos de regras de alertas e eventos para dispositivos IoT.
Todos os modelos são criados por schema de tenant (multi-tenancy).

Estrutura:
---------
Rule: regra de alerta/monitoramento
  - id: uuid PK
  - device_id: uuid NULL FK device (NULL = regra global do tenant)
  - point_id: uuid NULL FK point (NULL = regra aplica a vários pontos)
  - type: text CHECK (type IN ('threshold','window','hysteresis'))
  - params: jsonb - parâmetros da regra
  - enabled: bool default true
  - created_at: timestamptz default now()

RuleEvent: evento gerado por uma regra
  - id: uuid PK
  - rule_id: uuid FK rule
  - state: text CHECK (state IN ('ACTIVE','CLEARED'))
  - reason: text NULL - razão da ativação/limpeza
  - ts: timestamptz default now()

Autor: TrakSense Team
Data: 2025-10-08 (Fase R)
"""

from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import uuid


class RuleType(models.TextChoices):
    """
    Tipos de regras de alerta suportados.
    
    - threshold: limite simples (ex: temp > 80°C)
    - window: janela de tempo (ex: valor fora de faixa por 5min)
    - hysteresis: histerese (ex: temp > 80°C para ativar, < 75°C para limpar)
    """
    THRESHOLD = 'threshold', _('Limite')
    WINDOW = 'window', _('Janela de Tempo')
    HYSTERESIS = 'hysteresis', _('Histerese')


class RuleState(models.TextChoices):
    """
    Estados de um evento de regra.
    
    - ACTIVE: regra foi ativada (alerta)
    - CLEARED: regra foi limpa (voltou ao normal)
    """
    ACTIVE = 'ACTIVE', _('Ativo')
    CLEARED = 'CLEARED', _('Limpo')


class Rule(models.Model):
    """
    Regra de alerta/monitoramento - Schema TENANT (isolado).
    
    Define uma regra de monitoramento para dispositivos ou pontos específicos.
    Quando a condição é satisfeita, um RuleEvent é gerado.
    
    Escopo:
    ------
    - device_id NULL + point_id NULL: regra global do tenant
    - device_id preenchido + point_id NULL: regra para todos os pontos do device
    - device_id preenchido + point_id preenchido: regra para ponto específico
    
    Campos:
    ------
    id: uuid PK
    device_id: uuid NULL FK device (NULL = regra global)
    point_id: uuid NULL FK point (NULL = aplica a vários pontos)
    type: text CHECK (type IN ('threshold','window','hysteresis'))
    params: jsonb - parâmetros da regra (ex: {"operator": ">", "value": 80, "duration": "5m"})
    enabled: bool default true - se a regra está ativa
    created_at: timestamptz default now()
    
    Exemplos params:
    ---------------
    Threshold: {"operator": ">", "value": 80}
    Window: {"operator": ">", "value": 80, "duration": "5m"}
    Hysteresis: {"high": 80, "low": 75}
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # FKs para Device e Point (tenant schema) - opcionais
    device = models.ForeignKey(
        'devices.Device',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='rules',
        help_text="Dispositivo ao qual esta regra pertence (NULL = global)"
    )
    
    point = models.ForeignKey(
        'devices.Point',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='rules',
        help_text="Ponto ao qual esta regra pertence (NULL = vários pontos)"
    )
    
    type = models.TextField(
        choices=RuleType.choices,
        help_text="Tipo da regra (threshold|window|hysteresis)"
    )
    
    params = models.JSONField(
        default=dict,
        help_text="Parâmetros da regra (JSON)"
    )
    
    enabled = models.BooleanField(
        default=True,
        help_text="Se a regra está ativa"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Momento da criação da regra"
    )
    
    class Meta:
        # Tabela no schema de tenant (TENANT_APPS)
        ordering = ['-created_at']
        verbose_name = _('Regra')
        verbose_name_plural = _('Regras')
        indexes = [
            models.Index(fields=['device', 'enabled'], name='rule_device_enabled_idx'),
            models.Index(fields=['point', 'enabled'], name='rule_point_enabled_idx'),
        ]
    
    def __str__(self):
        scope = "Global"
        if self.device:
            scope = f"Device {self.device.name}"
        if self.point:
            scope = f"Point {self.point.name}"
        status = "ATIVA" if self.enabled else "DESABILITADA"
        return f"{self.type} - {scope} ({status})"
    
    def clean(self):
        """
        Validação customizada.
        
        Regras:
        - Se point_id preenchido, device_id também deve estar
        - params deve conter campos obrigatórios conforme tipo
        """
        super().clean()
        
        errors = {}
        
        # Validar point_id requer device_id
        if self.point and not self.device:
            errors['device'] = _(
                "Campo 'device' é obrigatório quando 'point' está preenchido."
            )
        
        # Validar params conforme tipo (validação básica)
        if not isinstance(self.params, dict):
            errors['params'] = _(
                "Campo 'params' deve ser um objeto JSON."
            )
        
        if errors:
            raise ValidationError(errors)


class RuleEvent(models.Model):
    """
    Evento gerado por uma regra - Schema TENANT (isolado).
    
    Representa uma ocorrência de ativação ou limpeza de uma regra.
    
    Campos:
    ------
    id: uuid PK
    rule_id: uuid FK rule
    state: text CHECK (state IN ('ACTIVE','CLEARED'))
    reason: text NULL - razão da ativação/limpeza (ex: "Temperatura > 80°C por 5min")
    ts: timestamptz default now() - momento do evento
    
    Índices:
    -------
    - (rule_id, ts DESC): buscar eventos recentes por regra
    - (ts DESC): buscar eventos recentes globais
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    rule = models.ForeignKey(
        Rule,
        on_delete=models.CASCADE,
        related_name='events',
        help_text="Regra que gerou este evento"
    )
    
    state = models.TextField(
        choices=RuleState.choices,
        help_text="Estado do evento (ACTIVE|CLEARED)"
    )
    
    reason = models.TextField(
        null=True,
        blank=True,
        help_text="Razão da ativação/limpeza"
    )
    
    ts = models.DateTimeField(
        auto_now_add=True,
        help_text="Momento do evento"
    )
    
    class Meta:
        # Tabela no schema de tenant (TENANT_APPS)
        ordering = ['-ts']
        verbose_name = _('Evento de Regra')
        verbose_name_plural = _('Eventos de Regras')
        indexes = [
            models.Index(fields=['rule', '-ts'], name='rule_event_rule_ts_idx'),
            models.Index(fields=['-ts'], name='rule_event_ts_idx'),
        ]
    
    def __str__(self):
        return f"{self.rule} - {self.state} @ {self.ts}"
