from django.urls import path
from .views import data_points, health_ts

urlpatterns = [
    path('data/points', data_points, name='data_points'),
    path('health/timeseries', health_ts, name='health_timeseries'),
]
