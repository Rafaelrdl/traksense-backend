"""
Timeseries URL Configuration - Rotas de telemetria IoT

Este módulo define as rotas HTTP para o app timeseries.

Rotas:
-----
1. GET /data/points:
   - Consulta telemetria de um ponto específico
   - Query params: device_id, point_id, from, to, agg
   - Suporta agregações: raw, 1m, 5m, 1h
   - RLS automático (isolamento por tenant)

2. GET /health/timeseries:
   - Health check do sistema de telemetria
   - Verifica RLS, continuous aggregates, tenant_id

Namespace:
---------
Registrado em core/urls.py:
- path('', include('timeseries.urls'))

URLs completas:
- http://localhost:8000/data/points
- http://localhost:8000/health/timeseries

TODO (Fase 2):
-------------
- POST /data/points: inserir telemetria via API (não apenas via ingest MQTT)
- GET /data/points/latest: última leitura de um ponto (cache Redis)
- GET /data/devices/{device_id}/summary: resumo de todos pontos do device
- WebSocket /ws/data/stream: streaming real-time (Django Channels)

Autor: TrakSense Team
Data: 2025-10-07
"""
from django.urls import path
from .views import data_points, health_ts, get_data_points

urlpatterns = [
    # Consulta de telemetria (endpoint principal - NOVO Fase R)
    # GET /data/points?device_id=xxx&point_id=yyy&start=...&end=...&agg=1m
    path('data/points', get_data_points, name='get_data_points'),
    
    # Health check do sistema de telemetria
    # GET /health/timeseries
    path('health/timeseries', health_ts, name='health_timeseries'),
]
