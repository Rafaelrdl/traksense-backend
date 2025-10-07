"""
Models - Dashboards App (TENANT_APPS)

Modelos de configuração de dashboards para dispositivos IoT.
Todos os modelos são criados por schema de tenant (multi-tenancy).

Estrutura:
---------
DashboardTemplate (vinculado a DeviceTemplate) → instancia → DashboardConfig (vinculado a Device)

O DashboardTemplate define painéis genéricos; o DashboardConfig é filtrado por pontos contratados.

Validação:
---------
DashboardTemplate.json é validado contra JSON Schema (dashboard_template_v1.json).

Autor: TrakSense Team
Data: 2025-10-07 (Fase 2)
"""

from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import uuid


# ==============================================================================
# DASHBOARD TEMPLATE (MODELO DE PAINEL)
# ==============================================================================

class DashboardTemplate(models.Model):
    """
    Template de dashboard para um tipo de dispositivo.
    
    Define a estrutura de painéis (timeseries, status, KPI, etc.) que serão exibidos
    para dispositivos deste tipo. O JSON é validado contra um schema JSON.
    
    Imutabilidade:
    -------------
    Assim como DeviceTemplate, DashboardTemplate usa versionamento.
    Para mudanças, criar nova versão e setar superseded_by.
    
    Campos:
    ------
    device_template: FK para DeviceTemplate (relacionamento 1:N)
    schema: versão do schema JSON (ex: "v1")
    version: número de versão (inteiro)
    json: estrutura JSON dos painéis (validado por jsonschema)
    superseded_by: FK para versão mais nova (se depreciada)
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device_template = models.ForeignKey(
        'devices.DeviceTemplate',
        on_delete=models.CASCADE,
        related_name='dashboard_templates',
        help_text="Template de dispositivo ao qual este dashboard pertence"
    )
    schema = models.CharField(
        max_length=20,
        default='v1',
        help_text="Versão do schema JSON (ex: v1)"
    )
    version = models.PositiveIntegerField(
        default=1,
        help_text="Número de versão do template de dashboard"
    )
    json = models.JSONField(
        help_text="Estrutura JSON dos painéis (validado contra schema)"
    )
    superseded_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='supersedes',
        help_text="Versão mais nova que substitui esta (se depreciada)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['device_template', '-version']
        verbose_name = _('Template de Dashboard')
        verbose_name_plural = _('Templates de Dashboards')
    
    def __str__(self):
        status = " [DEPRECIADO]" if self.superseded_by else ""
        return f"Dashboard {self.device_template.code} (v{self.version}){status}"
    
    def clean(self):
        """
        Validação customizada: valida JSON contra schema.
        """
        super().clean()
        
        # Importar validador aqui para evitar importação circular
        from .validators import validate_dashboard_template
        
        try:
            validate_dashboard_template(self.json)
        except Exception as e:
            raise ValidationError({
                'json': f"JSON inválido: {str(e)}"
            })
    
    @property
    def is_deprecated(self):
        """Verifica se este template foi substituído por uma versão mais nova."""
        return self.superseded_by is not None


# ==============================================================================
# DASHBOARD CONFIG (INSTÂNCIA DE PAINEL POR DEVICE)
# ==============================================================================

class DashboardConfig(models.Model):
    """
    Configuração instanciada de dashboard para um Device específico.
    
    É gerado automaticamente via serviço (instantiate_dashboard_config) ao criar
    um Device. O JSON é filtrado para conter apenas pontos contratados.
    
    Frontend:
    --------
    O frontend Spark (outro repositório) consome este JSON via API e renderiza
    os painéis (ECharts, Mantine, etc.). Este backend não renderiza UI.
    
    Campos:
    ------
    device: FK para Device (relacionamento 1:1)
    template_version: versão do DashboardTemplate de origem (rastreabilidade)
    json: estrutura JSON final dos painéis (filtrado por pontos contratados)
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device = models.OneToOneField(
        'devices.Device',
        on_delete=models.CASCADE,
        related_name='dashboard_config',
        help_text="Device ao qual esta configuração de dashboard pertence"
    )
    template_version = models.PositiveIntegerField(
        default=0,
        help_text="Versão do DashboardTemplate de origem (0 se sem template)"
    )
    json = models.JSONField(
        help_text="Estrutura JSON final dos painéis (filtrado por pontos contratados)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Configuração de Dashboard')
        verbose_name_plural = _('Configurações de Dashboards')
    
    def __str__(self):
        return f"Dashboard de {self.device.name}"
