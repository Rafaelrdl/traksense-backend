"""
Models - Devices App (TENANT_APPS)

Modelos de domínio para dispositivos IoT e seus pontos de telemetria.
Todos os modelos são criados por schema de tenant (multi-tenancy).

Estrutura:
---------
DeviceTemplate → PointTemplate (1:N)
    ↓                   ↓
  Device    →    Point (1:N)

Imutabilidade:
-------------
DeviceTemplate e PointTemplate usam versionamento (version + superseded_by).
Nunca alterar registros publicados; criar nova versão e marcar a antiga como supersedida.

Provisionamento:
---------------
A criação de Points e DashboardConfig é feita via serviço explícito
(provision_device_from_template), NÃO em signals pre_save.

Autor: TrakSense Team
Data: 2025-10-07 (Fase 2)
"""

from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import uuid
import json


# ==============================================================================
# CHOICES E CONSTANTES
# ==============================================================================

class PointType(models.TextChoices):
    """
    Tipos de ponto de telemetria suportados.
    
    - NUMERIC: valores numéricos (float) com unidade opcional
    - BOOL: valores booleanos (true/false)
    - ENUM: valores de enumeração (lista finita de strings)
    - TEXT: valores de texto livre
    """
    NUMERIC = 'NUMERIC', _('Numérico')
    BOOL = 'BOOL', _('Booleano')
    ENUM = 'ENUM', _('Enumeração')
    TEXT = 'TEXT', _('Texto')


class Polarity(models.TextChoices):
    """
    Polaridade do ponto (para alarmes e regras).
    
    - NORMAL: valor alto = alerta (ex: temperatura alta)
    - INVERTED: valor baixo = alerta (ex: pressão baixa)
    """
    NORMAL = 'NORMAL', _('Normal')
    INVERTED = 'INVERTED', _('Invertida')


class DeviceStatus(models.TextChoices):
    """
    Status do ciclo de vida de um dispositivo.
    
    - PENDING: criado mas não provisionado no EMQX ainda (Fase 3)
    - ACTIVE: ativo e operacional
    - DECOMMISSIONED: desativado/removido
    """
    PENDING = 'PENDING', _('Pendente')
    ACTIVE = 'ACTIVE', _('Ativo')
    DECOMMISSIONED = 'DECOMMISSIONED', _('Desativado')


# ==============================================================================
# DEVICE TEMPLATE (MODELO DE EQUIPAMENTO)
# ==============================================================================

class DeviceTemplate(models.Model):
    """
    Template (modelo) de dispositivo IoT.
    
    Define a família/tipo de equipamento (ex: inverter_v1_parsec, chiller_v1).
    Contém PointTemplates que especificam os pontos de telemetria padrão.
    
    Imutabilidade:
    -------------
    - Uma vez publicado, não deve ser alterado destrutivamente.
    - Para mudanças, criar nova versão (version += 1) e setar superseded_by.
    
    Campos:
    ------
    code: slug único por família (ex: inverter_v1_parsec)
    name: nome legível (ex: "Inversor Parsec v1")
    version: número de versão (inteiro, incrementa a cada mudança)
    superseded_by: FK para a versão mais nova (se depreciada)
    description: descrição textual do template
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.SlugField(
        max_length=100,
        help_text="Código único do template (ex: inverter_v1_parsec)"
    )
    name = models.CharField(
        max_length=200,
        help_text="Nome legível do template"
    )
    version = models.PositiveIntegerField(
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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        constraints = [
            # Garante que (code, version) seja único
            models.UniqueConstraint(
                fields=['code', 'version'],
                name='unique_device_template_code_version'
            )
        ]
        ordering = ['code', '-version']
        verbose_name = _('Template de Dispositivo')
        verbose_name_plural = _('Templates de Dispositivos')
    
    def __str__(self):
        status = " [DEPRECIADO]" if self.superseded_by else ""
        return f"{self.name} (v{self.version}){status}"
    
    def clean(self):
        """
        Validação customizada.
        
        Impede alterações destrutivas em templates já publicados.
        Recomenda-se criar nova versão ao invés de alterar.
        """
        super().clean()
        
        # Se o template já existe no BD (não é novo) e já tem devices associados
        if self.pk:
            # Poderia adicionar validação aqui para impedir mudanças
            # Ex: if Device.objects.filter(template=self).exists():
            #        raise ValidationError("Template já em uso. Crie nova versão.")
            pass
    
    @property
    def is_deprecated(self):
        """Verifica se este template foi substituído por uma versão mais nova."""
        return self.superseded_by is not None


# ==============================================================================
# POINT TEMPLATE (MODELO DE PONTO DE TELEMETRIA)
# ==============================================================================

class PointTemplate(models.Model):
    """
    Template de ponto de telemetria.
    
    Define um ponto padrão dentro de um DeviceTemplate (ex: temp_agua, status).
    Quando um Device é criado, Points são instanciados a partir destes templates.
    
    Validações:
    ----------
    - unit: permitido somente quando ptype=NUMERIC
    - enum_values: obrigatório quando ptype=ENUM
    - hysteresis: deve ser ≥ 0
    
    Campos:
    ------
    device_template: FK para o DeviceTemplate pai
    name: slug único dentro do template (ex: temp_agua)
    label: nome legível (ex: "Temperatura da água")
    ptype: tipo do ponto (NUMERIC|BOOL|ENUM|TEXT)
    unit: unidade (ex: °C, dBm) - só para NUMERIC
    enum_values: lista JSON de valores válidos (ex: ["RUN","STOP","FAULT"]) - só para ENUM
    polarity: polaridade para alarmes (NORMAL|INVERTED)
    hysteresis: histerese padrão para evitar flapping de alarmes
    default_limits: limites padrão (JSON) para aplicar em Points
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device_template = models.ForeignKey(
        DeviceTemplate,
        on_delete=models.CASCADE,
        related_name='point_templates',
        help_text="Template de dispositivo ao qual este ponto pertence"
    )
    name = models.SlugField(
        max_length=100,
        help_text="Nome único do ponto dentro do template (ex: temp_agua)"
    )
    label = models.CharField(
        max_length=200,
        help_text="Nome legível do ponto (ex: 'Temperatura da água')"
    )
    ptype = models.CharField(
        max_length=20,
        choices=PointType.choices,
        verbose_name="Tipo",
        help_text="Tipo de dado do ponto"
    )
    unit = models.CharField(
        max_length=20,
        blank=True,
        help_text="Unidade de medida (ex: °C, dBm) - apenas para NUMERIC"
    )
    enum_values = models.JSONField(
        null=True,
        blank=True,
        help_text="Lista de valores válidos para ENUM (ex: ['RUN','STOP','FAULT'])"
    )
    polarity = models.CharField(
        max_length=20,
        choices=Polarity.choices,
        default=Polarity.NORMAL,
        help_text="Polaridade para alarmes (NORMAL ou INVERTED)"
    )
    hysteresis = models.FloatField(
        null=True,
        blank=True,
        help_text="Histerese padrão para evitar flapping de alarmes (≥ 0)"
    )
    default_limits = models.JSONField(
        default=dict,
        blank=True,
        help_text="Limites padrão (JSON) para aplicar ao instanciar Point"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        constraints = [
            # Garante que (device_template, name) seja único
            models.UniqueConstraint(
                fields=['device_template', 'name'],
                name='unique_point_template_per_device'
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
        - unit só permitido para NUMERIC
        - enum_values obrigatório para ENUM
        - hysteresis ≥ 0
        """
        super().clean()
        
        errors = {}
        
        # Validar unit
        if self.unit and self.ptype != PointType.NUMERIC:
            errors['unit'] = _(
                "Campo 'unit' só é permitido quando tipo é NUMERIC."
            )
        
        # Validar enum_values
        if self.ptype == PointType.ENUM:
            if not self.enum_values or not isinstance(self.enum_values, list):
                errors['enum_values'] = _(
                    "Campo 'enum_values' é obrigatório para tipo ENUM e deve ser uma lista."
                )
        
        # Validar hysteresis
        if self.hysteresis is not None and self.hysteresis < 0:
            errors['hysteresis'] = _(
                "Campo 'hysteresis' deve ser maior ou igual a zero."
            )
        
        if errors:
            raise ValidationError(errors)


# ==============================================================================
# DEVICE (INSTÂNCIA DE EQUIPAMENTO IOT)
# ==============================================================================

class Device(models.Model):
    """
    Instância de dispositivo IoT.
    
    Representa um equipamento físico instalado em um site do cliente.
    É criado a partir de um DeviceTemplate e herda seus PointTemplates.
    
    Provisionamento:
    ---------------
    Após criar um Device, chamar devices.services.provision_device_from_template()
    para gerar Points e DashboardConfig automaticamente.
    
    Campos:
    ------
    template: FK para DeviceTemplate (define tipo de equipamento)
    name: nome único do device (ex: "Inversor 01 - Sala A")
    site_id: identificador do site (UUID/texto) - reservado para uso futuro
    topic_base: prefixo MQTT (ex: traksense/{tenant}/{site}/{device}) - Fase 3
    credentials_id: ID das credenciais EMQX - Fase 3
    status: status do ciclo de vida (PENDING|ACTIVE|DECOMMISSIONED)
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template = models.ForeignKey(
        DeviceTemplate,
        on_delete=models.PROTECT,  # Não permite deletar template se há devices
        related_name='devices',
        help_text="Template que define o tipo deste dispositivo"
    )
    name = models.CharField(
        max_length=200,
        help_text="Nome único do dispositivo (ex: 'Inversor 01 - Sala A')"
    )
    site_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="Identificador do site onde o device está instalado (reservado)"
    )
    topic_base = models.CharField(
        max_length=200,
        blank=True,
        help_text="Prefixo MQTT para este device (será usado na Fase 3)"
    )
    credentials_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="ID das credenciais EMQX (será usado na Fase 3)"
    )
    status = models.CharField(
        max_length=20,
        choices=DeviceStatus.choices,
        default=DeviceStatus.PENDING,
        help_text="Status do ciclo de vida do dispositivo"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = _('Dispositivo')
        verbose_name_plural = _('Dispositivos')
    
    def __str__(self):
        return f"{self.name} ({self.template.name})"


# ==============================================================================
# POINT (INSTÂNCIA DE PONTO DE TELEMETRIA)
# ==============================================================================

class Point(models.Model):
    """
    Instância de ponto de telemetria.
    
    Representa um ponto de dados específico de um Device (ex: temp_agua, status).
    É criado a partir de um PointTemplate via serviço de provisionamento.
    
    Contratação:
    -----------
    is_contracted: define se o ponto está ativo/contratado pelo cliente.
    Pontos não contratados não aparecem em dashboards.
    
    Campos:
    ------
    device: FK para Device pai
    template: FK para PointTemplate de origem (opcional, para rastreabilidade)
    name: nome único do ponto dentro do device
    label: nome legível
    unit: unidade (herdada do template)
    polarity: polaridade (herdada do template)
    limits: limites customizados (JSON) - pode ser editado pelo cliente (Fase futura)
    is_contracted: se o ponto está ativo/contratado
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,
        related_name='points',
        help_text="Device ao qual este ponto pertence"
    )
    template = models.ForeignKey(
        PointTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='instances',
        help_text="Template de origem (para rastreabilidade)"
    )
    name = models.SlugField(
        max_length=100,
        help_text="Nome único do ponto (ex: temp_agua)"
    )
    label = models.CharField(
        max_length=200,
        help_text="Nome legível do ponto"
    )
    unit = models.CharField(
        max_length=20,
        blank=True,
        help_text="Unidade de medida"
    )
    polarity = models.CharField(
        max_length=20,
        choices=Polarity.choices,
        default=Polarity.NORMAL,
        help_text="Polaridade para alarmes"
    )
    limits = models.JSONField(
        default=dict,
        blank=True,
        help_text="Limites customizados (JSON) - editável pelo cliente"
    )
    is_contracted = models.BooleanField(
        default=True,
        help_text="Se este ponto está ativo/contratado pelo cliente"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        constraints = [
            # Garante que (device, name) seja único
            models.UniqueConstraint(
                fields=['device', 'name'],
                name='unique_point_per_device'
            )
        ]
        ordering = ['device', 'name']
        verbose_name = _('Ponto')
        verbose_name_plural = _('Pontos')
    
    def __str__(self):
        contracted = "" if self.is_contracted else " [NÃO CONTRATADO]"
        return f"{self.device.name}.{self.name}{contracted}"
