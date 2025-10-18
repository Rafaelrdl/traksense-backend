from django.db import models
from django.utils import timezone


class Telemetry(models.Model):
    """
    Telemetry data from IoT devices via MQTT.
    
    This model stores time-series data from MQTT messages forwarded
    by EMQX Rule Engine. The table is converted to a TimescaleDB
    hypertable for efficient time-series queries.
    
    Note: Uses auto-incrementing BigAutoField as PK (not timestamp)
    to avoid TimescaleDB constraint issues. Indexes include timestamp.
    """
    
    # Auto-incrementing ID (standard Django)
    id = models.BigAutoField(primary_key=True)
    
    # Device identification
    device_id = models.CharField(
        max_length=255,
        db_index=True,
        help_text="MQTT client ID (device identifier)"
    )
    
    # MQTT topic where message was published
    topic = models.CharField(
        max_length=500,
        db_index=True,
        help_text="Full MQTT topic path (e.g., tenants/umc/devices/001/sensors/temp)"
    )
    
    # Message payload (JSON from MQTT)
    payload = models.JSONField(
        help_text="Original MQTT message payload (parsed JSON)"
    )
    
    # Timestamp from EMQX (Unix milliseconds) - used for TimescaleDB partitioning
    timestamp = models.DateTimeField(
        db_index=True,
        help_text="Timestamp from EMQX broker (when message was received)"
    )
    
    # Internal timestamp (when saved to DB)
    created_at = models.DateTimeField(
        default=timezone.now,
        help_text="When this record was created in the database"
    )
    
    class Meta:
        db_table = 'telemetry'
        ordering = ['-timestamp']
        verbose_name = 'Telemetry'
        verbose_name_plural = 'Telemetry'
        indexes = [
            models.Index(fields=['device_id', 'timestamp']),
            models.Index(fields=['topic', 'timestamp']),
        ]
        # Note: TimescaleDB hypertable will be created via migration RunSQL
    
    def __str__(self):
        return f"{self.device_id} - {self.topic} @ {self.timestamp}"
