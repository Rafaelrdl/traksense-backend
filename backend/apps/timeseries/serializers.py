"""
Serializers para API /data/points - Telemetria IoT

Serializers para dados raw e agregados (1m/5m/1h).
"""
from rest_framework import serializers
from .models import TsMeasureTenant, TsMeasure1mTenant, TsMeasure5mTenant, TsMeasure1hTenant


class TsMeasureRawSerializer(serializers.ModelSerializer):
    """
    Serializer para dados raw (agg=raw).
    
    Retorna todos os campos da VIEW ts_measure_tenant:
    - ts: timestamp da medição
    - v_num, v_bool, v_text: valores (apenas um preenchido)
    - unit: unidade de medida (ex: "°C", "bar")
    - qual: qualidade (0=ok, 1=suspeito, 2=falha)
    - meta: metadados adicionais (JSONB)
    """
    class Meta:
        model = TsMeasureTenant
        fields = ['ts', 'device_id', 'point_id', 'v_num', 'v_bool', 'v_text', 'unit', 'qual', 'meta']
        read_only_fields = fields


class TsMeasureAggSerializer(serializers.Serializer):
    """
    Serializer para dados agregados (agg=1m/5m/1h).
    
    Retorna estatísticas agregadas:
    - bucket: timestamp do bucket (ex: 2025-10-08 14:05:00)
    - v_avg: média do v_num no bucket
    - v_max: máximo do v_num no bucket
    - v_min: mínimo do v_num no bucket
    - n: quantidade de amostras no bucket
    
    Campos device_id e point_id não incluídos (vêm dos query params).
    """
    bucket = serializers.DateTimeField()
    v_avg = serializers.FloatField(allow_null=True)
    v_max = serializers.FloatField(allow_null=True)
    v_min = serializers.FloatField(allow_null=True)
    n = serializers.IntegerField()
