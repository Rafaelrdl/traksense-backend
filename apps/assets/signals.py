"""
Signals para app de Assets.

Responsável por:
- Atualizar cache de última leitura do Sensor quando TelemetryReading é criado
- Atualizar status de Device quando conecta/desconecta no EMQX
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone


# Signal será conectado quando integrarmos com apps.ingest
# @receiver(post_save, sender='ingest.TelemetryReading')
# def update_sensor_last_reading(sender, instance, created, **kwargs):
#     """
#     Atualiza cache da última leitura do Sensor.
#     Chamado automaticamente quando TelemetryReading é salvo.
#     """
#     if created and hasattr(instance, 'sensor'):
#         instance.sensor.update_last_reading(
#             value=instance.value,
#             timestamp=instance.timestamp
#         )
