"""
Models - Templates App (SHARED_APPS - public schema)

Modelos globais de templates para dispositivos IoT e dashboards.
Estes models vivem no schema 'public' e são compartilhados por todos os tenants.

Estrutura:
---------
DeviceTemplate (global) → PointTemplate (1:N)
    ↓ instancia em tenant schema
  Device (tenant) → Point (1:N)

DashboardTemplate (global) → DashboardConfig (tenant)

Imutabilidade:
-------------
Templates usam versionamento (version + superseded_by).
Nunca alterar registros publicados; criar nova versão e marcar antiga como supersedida.

Tenancy:
-------
- is_global=True: template disponível para todos os tenants
- is_global=False + tenant_override: template customizado para tenant específico

Autor: TrakSense Team
Data: 2025-10-08 (Fase R)
"""

from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import uuid


# ==============================================================================
# CHOICES E CONSTANTES
# ==============================================================================

class PointType(models.TextChoices):
    """
    Tipos de ponto de telemetria suportados.
    
    Especificação Fase R:
    - num: valores numéricos (float) com unidade
    - bool: valores booleanos (true/false)
    - enum: valores de enumeração (lista finita)
    - text: valores de texto livre
    """
    NUM = 'num', _('Numérico')
    BOOL = 'bool', _('Booleano')
    ENUM = 'enum', _('Enumeração')
    TEXT = 'text', _('Texto')


class Polarity(models.TextChoices):
    """
    Polaridade do ponto (para alarmes e regras).
    
    - normal: valor alto = alerta (ex: temperatura alta)
    - inverted: valor baixo = alerta (ex: pressão baixa)
    """
    NORMAL = 'normal', _('Normal')
    INVERTED = 'inverted', _('Invertida')


# ==============================================================================
# DEVICE TEMPLATE (MODELO DE EQUIPAMENTO GLOBAL)
# ==============================================================================

class DeviceTemplate(models.Model):
    """
    Template (modelo) de dispositivo IoT - Schema PUBLIC (global).
    
    Define a família/tipo de equipamento (ex: chiller_v1, inverter_parsec_v1).
    Contém PointTemplates que especificam os pontos de telemetria padrão.
    
    Imutabilidade:
    -------------
    - Uma vez publicado, não deve ser alterado destrutivamente.
    - Para mudanças, criar nova versão (version += 1) e setar superseded_by.
    
    Tenancy:
    -------
    - is_global=True: template disponível para todos os tenants
    - is_global=False + tenant_override: template customizado para tenant específico
    
    Campos:
    ------
    id: uuid PK
    code: text UNIQUE - slug único (ex: chiller_v1)
    name: text - nome legível (ex: "Chiller Genérico v1")
    version: int - número de versão (incrementa a cada mudança)
    superseded_by: uuid NULL FK self - versão mais nova que substitui esta
    description: text - descrição detalhada do template
    is_global: bool default true - se disponível para todos os tenants
    tenant_override: uuid NULL - tenant específico (se is_global=false)
    created_at: timestamptz default now()
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.TextField(
        unique=True,
        help_text="Código único do template (ex: chiller_v1)"
    )
    name = models.TextField(
        help_text="Nome legível do template"
    )
    version = models.IntegerField(
        default=1,
        help_text="Número de versão (incrementa a cada mudança)"
    )
    superseded_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='supersedes',
        help_text="Versão mais nova que substitui esta (se depreciada)"
    )
    description = models.TextField(
        blank=True,
        help_text="Descrição detalhada do template"
    )
    is_global = models.BooleanField(
        default=True,
        help_text="Se este template está disponível para todos os tenants"
    )
    tenant_override = models.UUIDField(
        null=True,
        blank=True,
        help_text="Tenant específico (se is_global=false)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        # Tabela no schema public (SHARED_APPS)
        db_table = 'device_template'
        ordering = ['code', '-version']
        verbose_name = _('Template de Dispositivo')
        verbose_name_plural = _('Templates de Dispositivos')
    
    def __str__(self):
        status = " [DEPRECIADO]" if self.superseded_by else ""
        scope = "" if self.is_global else f" [TENANT {self.tenant_override}]"
        return f"{self.name} (v{self.version}){status}{scope}"
    
    def clean(self):
        """
        Validação customizada.
        
        Regras:
        - Se is_global=false, tenant_override deve estar preenchido
        - Código deve ser imutável após criação (não permitir mudança)
        """
        super().clean()
        
        errors = {}
        
        # Validar tenant_override
        if not self.is_global and not self.tenant_override:
            errors['tenant_override'] = _(
                "Campo 'tenant_override' é obrigatório quando is_global=false."
            )
        
        if self.is_global and self.tenant_override:
            errors['tenant_override'] = _(
                "Campo 'tenant_override' deve ser vazio quando is_global=true."
            )
        
        if errors:
            raise ValidationError(errors)
    
    @property
    def is_deprecated(self):
        """Verifica se este template foi substituído por uma versão mais nova."""
        return self.superseded_by is not None


# ==============================================================================
# POINT TEMPLATE (MODELO DE PONTO DE TELEMETRIA GLOBAL)
# ==============================================================================

class PointTemplate(models.Model):
    """
    Template de ponto de telemetria - Schema PUBLIC (global).
    
    Define um ponto padrão dentro de um DeviceTemplate (ex: temp_agua, status).
    Quando um Device é criado, Points são instanciados a partir destes templates.
    
    Validações (via CHECK constraints e clean()):
    ---------------------------------------------
    - unit: obrigatório se ptype='num'
    - enum_values: obrigatório se ptype='enum'
    - hysteresis: deve ser ≥ 0
    
    Campos:
    ------
    id: uuid PK
    device_template_id: uuid FK device_template
    name: text - slug único dentro do template (ex: temp_agua)
    ptype: text CHECK (ptype IN ('num','bool','enum','text'))
    unit: text NULL - unidade (ex: °C, dBm) - obrigatório se ptype='num'
    enum_values: jsonb NULL - lista de valores válidos (ex: ["RUN","STOP","FAULT"]) - obrigatório se ptype='enum'
    polarity: text NULL CHECK (polarity IN ('normal','inverted'))
    hysteresis: numeric NULL - histerese padrão (≥ 0)
    default_limits: jsonb NULL - limites padrão para aplicar em Points
    
    Constraints:
    -----------
    UNIQUE (device_template_id, name)
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device_template = models.ForeignKey(
        DeviceTemplate,
        on_delete=models.CASCADE,
        related_name='point_templates',
        help_text="Template de dispositivo ao qual este ponto pertence"
    )
    name = models.TextField(
        help_text="Nome único do ponto dentro do template (ex: temp_agua)"
    )
    ptype = models.TextField(
        choices=PointType.choices,
        verbose_name="Tipo",
        help_text="Tipo de dado do ponto: num|bool|enum|text"
    )
    unit = models.TextField(
        null=True,
        blank=True,
        help_text="Unidade de medida (ex: °C, dBm) - obrigatório para num"
    )
    enum_values = models.JSONField(
        null=True,
        blank=True,
        help_text="Lista de valores válidos para enum (ex: ['RUN','STOP','FAULT'])"
    )
    polarity = models.TextField(
        null=True,
        blank=True,
        choices=Polarity.choices,
        help_text="Polaridade para alarmes (normal ou inverted)"
    )
    hysteresis = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Histerese padrão para evitar flapping de alarmes (≥ 0)"
    )
    default_limits = models.JSONField(
        null=True,
        blank=True,
        default=dict,
        help_text="Limites padrão (JSON) para aplicar ao instanciar Point"
    )
    
    class Meta:
        # Tabela no schema public (SHARED_APPS)
        db_table = 'point_template'
        constraints = [
            # Garante que (device_template_id, name) seja único
            models.UniqueConstraint(
                fields=['device_template', 'name'],
                name='point_template_device_name_unique'
            )
        ]
        ordering = ['device_template', 'name']
        verbose_name = _('Template de Ponto')
        verbose_name_plural = _('Templates de Pontos')
    
    def __str__(self):
        return f"{self.device_template.code}.{self.name} ({self.ptype})"
    
    def clean(self):
        """
        Validações customizadas:
        - unit obrigatório se ptype='num'
        - enum_values obrigatório se ptype='enum'
        - hysteresis ≥ 0
        """
        super().clean()
        
        errors = {}
        
        # Validar unit
        if self.ptype == PointType.NUM and not self.unit:
            errors['unit'] = _(
                "Campo 'unit' é obrigatório quando tipo é 'num'."
            )
        
        # Validar enum_values
        if self.ptype == PointType.ENUM:
            if not self.enum_values or not isinstance(self.enum_values, list):
                errors['enum_values'] = _(
                    "Campo 'enum_values' é obrigatório para tipo 'enum' e deve ser uma lista."
                )
        
        # Validar hysteresis
        if self.hysteresis is not None and self.hysteresis < 0:
            errors['hysteresis'] = _(
                "Campo 'hysteresis' deve ser maior ou igual a zero."
            )
        
        if errors:
            raise ValidationError(errors)


# ==============================================================================
# DASHBOARD TEMPLATE (MODELO DE PAINEL GLOBAL)
# ==============================================================================

class DashboardTemplate(models.Model):
    """
    Template de dashboard - Schema PUBLIC (global).
    
    Define a configuração padrão de painéis para um DeviceTemplate.
    Quando um Device é criado, um DashboardConfig é gerado a partir deste template.
    
    Schema:
    ------
    O campo 'schema' deve ser 'v1' (versão do schema JSON do frontend).
    O campo 'json' contém a estrutura completa do dashboard conforme schema v1.
    
    Campos:
    ------
    id: uuid PK
    device_template_id: uuid FK device_template
    schema: text CHECK (schema='v1')
    version: int
    json: jsonb NOT NULL - estrutura completa do dashboard
    superseded_by: uuid NULL - versão mais nova que substitui esta
    created_at: timestamptz default now()
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device_template = models.ForeignKey(
        DeviceTemplate,
        on_delete=models.CASCADE,
        related_name='dashboard_templates',
        help_text="Template de dispositivo ao qual este dashboard pertence"
    )
    schema = models.TextField(
        default='v1',
        help_text="Versão do schema JSON (sempre 'v1')"
    )
    version = models.IntegerField(
        default=1,
        help_text="Número de versão do dashboard template"
    )
    json = models.JSONField(
        help_text="Estrutura completa do dashboard conforme schema v1"
    )
    superseded_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='supersedes',
        help_text="Versão mais nova que substitui esta"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        # Tabela no schema public (SHARED_APPS)
        db_table = 'dashboard_template'
        ordering = ['device_template', '-version']
        verbose_name = _('Template de Dashboard')
        verbose_name_plural = _('Templates de Dashboards')
    
    def __str__(self):
        status = " [DEPRECIADO]" if self.superseded_by else ""
        return f"Dashboard {self.device_template.code} (v{self.version}){status}"
    
    def clean(self):
        """
        Validação customizada.
        
        Regras:
        - schema deve ser 'v1'
        - json deve ser um dict válido (validação completa via JSON Schema será feita em validators.py)
        """
        super().clean()
        
        errors = {}
        
        # Validar schema
        if self.schema != 'v1':
            errors['schema'] = _(
                "Campo 'schema' deve ser 'v1'."
            )
        
        # Validar json é dict
        if not isinstance(self.json, dict):
            errors['json'] = _(
                "Campo 'json' deve ser um objeto JSON válido."
            )
        
        if errors:
            raise ValidationError(errors)
    
    @property
    def is_deprecated(self):
        """Verifica se este template foi substituído por uma versão mais nova."""
        return self.superseded_by is not None
