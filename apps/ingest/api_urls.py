"""
URL routing for Telemetry API.
"""
from django.urls import path
from .api_views import (
    TelemetryListView,
    ReadingListView,
    TimeSeriesAggregateView
)

app_name = 'telemetry'

urlpatterns = [
    # Raw telemetry data (MQTT messages)
    path('raw/', TelemetryListView.as_view(), name='telemetry-raw'),
    
    # Structured sensor readings
    path('readings/', ReadingListView.as_view(), name='readings-list'),
    
    # Aggregated time-series (Continuous Aggregates)
    path('series/', TimeSeriesAggregateView.as_view(), name='series-aggregate'),
]
