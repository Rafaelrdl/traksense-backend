from django.contrib import admin
from .models import Telemetry


@admin.register(Telemetry)
class TelemetryAdmin(admin.ModelAdmin):
    list_display = ('device_id', 'topic', 'timestamp', 'created_at')
    list_filter = ('timestamp', 'created_at')
    search_fields = ('device_id', 'topic')
    readonly_fields = ('created_at',)
    ordering = ('-timestamp',)
    
    def has_add_permission(self, request):
        # Telemetry is added only via API
        return False
