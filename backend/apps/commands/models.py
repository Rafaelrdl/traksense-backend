"""
Models - Commands App (TENANT_APPS)

Modelos de comandos MQTT para dispositivos IoT.
Todos os modelos são criados por schema de tenant (multi-tenancy).

Estrutura:
---------
Command: comando enviado para dispositivo via MQTT
  - id: uuid PK
  - device_id: uuid FK device
  - cmd_id: text UNIQUE - identificador do comando
  - op: text - operação (ex: "SET_PARAM", "REBOOT")
  - params: jsonb - parâmetros do comando
  - requested_by: uuid NULL - usuário que solicitou
  - requested_at: timestamptz default now()
  - status: text CHECK (status IN ('PENDING','ACK','TIMEOUT','ERROR'))
  - error_msg: text NULL

Autor: TrakSense Team
Data: 2025-10-08 (Fase R)
"""

from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import uuid


class CommandStatus(models.TextChoices):
    """
    Status do ciclo de vida de um comando.
    
    - PENDING: comando criado, aguardando envio/ACK
    - ACK: comando reconhecido pelo dispositivo
    - TIMEOUT: comando não reconhecido no tempo esperado
    - ERROR: erro ao processar comando
    """
    PENDING = 'PENDING', _('Pendente')
    ACK = 'ACK', _('Reconhecido')
    TIMEOUT = 'TIMEOUT', _('Timeout')
    ERROR = 'ERROR', _('Erro')


class Command(models.Model):
    """
    Comando MQTT para dispositivo IoT - Schema TENANT (isolado).
    
    Representa um comando enviado para um dispositivo via MQTT.
    O ACK é recebido via MQTT e registrado em public.cmd_ack (Fase 6).
    
    Campos:
    ------
    id: uuid PK
    device_id: uuid FK device (apps.devices.Device)
    cmd_id: text UNIQUE - identificador único do comando (ex: "CMD_20251008_123456")
    op: text - operação (ex: "SET_PARAM", "REBOOT", "UPDATE_FIRMWARE")
    params: jsonb - parâmetros do comando (ex: {"param": "value", "timeout": 30})
    requested_by: uuid NULL - ID do usuário que solicitou (FK para auth_user - Fase futura)
    requested_at: timestamptz default now() - momento da solicitação
    status: text CHECK (status IN ('PENDING','ACK','TIMEOUT','ERROR'))
    error_msg: text NULL - mensagem de erro (se status=ERROR)
    
    Índices:
    -------
    - (device_id, requested_at DESC): buscar comandos recentes por device
    - (cmd_id): buscar por ID único (para ACK)
    - (status, requested_at DESC): buscar comandos pendentes
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # FK para Device (tenant schema)
    # Nota: Usar string 'devices.Device' para evitar import circular
    device = models.ForeignKey(
        'devices.Device',
        on_delete=models.CASCADE,
        related_name='commands',
        help_text="Dispositivo ao qual este comando pertence"
    )
    
    cmd_id = models.TextField(
        unique=True,
        help_text="Identificador único do comando (ex: CMD_20251008_123456)"
    )
    
    op = models.TextField(
        help_text="Operação do comando (ex: SET_PARAM, REBOOT)"
    )
    
    params = models.JSONField(
        default=dict,
        blank=True,
        help_text="Parâmetros do comando (JSON)"
    )
    
    requested_by = models.UUIDField(
        null=True,
        blank=True,
        help_text="ID do usuário que solicitou o comando"
    )
    
    requested_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Momento da solicitação do comando"
    )
    
    status = models.TextField(
        choices=CommandStatus.choices,
        default=CommandStatus.PENDING,
        help_text="Status do comando (PENDING|ACK|TIMEOUT|ERROR)"
    )
    
    error_msg = models.TextField(
        null=True,
        blank=True,
        help_text="Mensagem de erro (se status=ERROR)"
    )
    
    class Meta:
        # Tabela no schema de tenant (TENANT_APPS)
        ordering = ['-requested_at']
        verbose_name = _('Comando')
        verbose_name_plural = _('Comandos')
        indexes = [
            models.Index(fields=['device', '-requested_at'], name='command_device_req_idx'),
            models.Index(fields=['status', '-requested_at'], name='command_status_req_idx'),
        ]
    
    def __str__(self):
        return f"{self.cmd_id} ({self.op}) - {self.status}"
    
    def clean(self):
        """
        Validação customizada.
        
        Regras:
        - cmd_id deve seguir padrão (ex: CMD_YYYYMMDD_HHMMSS)
        - error_msg só preenchido se status=ERROR
        """
        super().clean()
        
        errors = {}
        
        # Validar error_msg
        if self.error_msg and self.status != CommandStatus.ERROR:
            errors['error_msg'] = _(
                "Campo 'error_msg' só deve ser preenchido quando status=ERROR."
            )
        
        if errors:
            raise ValidationError(errors)
