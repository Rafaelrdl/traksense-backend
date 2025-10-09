"""
Timeseries Models - Telemetria IoT (TimescaleDB)

Este arquivo está INTENCIONALMENTE VAZIO.

Por quê?
-------
A tabela public.ts_measure NÃO é definida via Django ORM (models.Model).
Em vez disso, é criada via SQL puro (RunSQL) na migration 0001_ts_schema.py.

Motivo:
------
TimescaleDB requer features SQL específicas que Django ORM não suporta:
1. Hypertables (create_hypertable)
2. Continuous aggregates (materialized views com refresh policies)
3. Compression policies
4. Retention policies
5. Row Level Security (RLS) com custom GUCs

Estrutura da tabela:
-------------------
CREATE TABLE public.ts_measure (
  tenant_id  uuid NOT NULL,
  device_id  uuid NOT NULL,
  point_id   uuid NOT NULL,
  ts         timestamptz NOT NULL,
  v_num      double precision,
  v_bool     boolean,
  v_text     text,
  unit       text,
  qual       smallint DEFAULT 0,
  meta       jsonb
);

-- Hypertable
SELECT create_hypertable('public.ts_measure', 'ts');

-- RLS
ALTER TABLE public.ts_measure ENABLE ROW LEVEL SECURITY;
CREATE POLICY ts_tenant_isolation ON public.ts_measure
USING (tenant_id = current_setting('app.tenant_id')::uuid);

-- Continuous Aggregates
CREATE MATERIALIZED VIEW public.ts_measure_1m ...;
CREATE MATERIALIZED VIEW public.ts_measure_5m ...;
CREATE MATERIALIZED VIEW public.ts_measure_1h ...;

-- Compression
SELECT add_compression_policy('public.ts_measure', INTERVAL '7 days');

-- Retention
SELECT add_retention_policy('public.ts_measure', INTERVAL '365 days');

ATUALIZAÇÃO - FASE R (Opção B):
-------------------------------
Com a implementação de Continuous Aggregates e isolamento via VIEWs + GUC,
agora temos models Django unmanaged para acesso às VIEWs tenant-scoped.

Ver models abaixo: TsMeasureTenant, TsMeasure1mTenant, etc.

Autor: TrakSense Team
Data: 2025-10-08 (atualizado Fase R)
"""

from django.db import models


# ============================================================================
# MODELS PARA VIEWs TENANT-SCOPED (Fase R - Opção B)
# ============================================================================

class TsMeasureTenant(models.Model):
    """
    MODEL unmanaged para VIEW ts_measure_tenant (dados raw).
    
    VIEW SQL:
    ---------
    CREATE VIEW ts_measure_tenant WITH (security_barrier = on) AS
    SELECT tenant_id, device_id, point_id, ts, v_num, v_bool, v_text, 
           unit, qual, meta
    FROM public.ts_measure
    WHERE tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid;
    
    Isolamento:
    -----------
    - Filtro automático por GUC app.tenant_id
    - Middleware TenantGucMiddleware configura GUC
    - security_barrier previne bypass via query rewrite
    
    Uso:
    ----
    # Django ORM (com middleware ativo):
    TsMeasureTenant.objects.filter(device_id=device_uuid, ts__gte=start)
    
    Retenção: 14 dias
    Compressão: Não
    API: GET /data/points?agg=raw
    """
    tenant_id = models.UUIDField()
    device_id = models.UUIDField()
    point_id = models.UUIDField()
    ts = models.DateTimeField()
    v_num = models.FloatField(null=True, blank=True)
    v_bool = models.BooleanField(null=True, blank=True)
    v_text = models.TextField(null=True, blank=True)
    unit = models.CharField(max_length=50, null=True, blank=True)
    qual = models.SmallIntegerField(default=0)
    meta = models.JSONField(null=True, blank=True)
    
    class Meta:
        managed = False  # VIEW criada em migration, Django não gerencia
        db_table = 'ts_measure_tenant'
        ordering = ['-ts']
        verbose_name = 'Telemetry (Raw, Tenant-Scoped)'
        verbose_name_plural = 'Telemetry (Raw, Tenant-Scoped)'
    
    def __str__(self):
        return f"{self.device_id}/{self.point_id} @ {self.ts}"


class TsMeasure1mTenant(models.Model):
    """
    MODEL unmanaged para VIEW ts_measure_1m_tenant (CAGG 1 minuto).
    
    VIEW SQL:
    ---------
    CREATE VIEW ts_measure_1m_tenant WITH (security_barrier = on) AS
    SELECT bucket, tenant_id, device_id, point_id, v_avg, v_max, v_min, n
    FROM public.ts_measure_1m
    WHERE tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid;
    
    CAGG Base:
    ----------
    - time_bucket('1 minute', ts) AS bucket
    - AVG(v_num), MAX(v_num), MIN(v_num), COUNT(v_num)
    - Refresh: a cada 1 minuto, janela [now()-14d, now()-1m]
    
    Uso:
    ----
    TsMeasure1mTenant.objects.filter(device_id=device_uuid, bucket__gte=start)
    
    Retenção: 365 dias (1 ano)
    Compressão: Sim (chunks > 7 dias)
    API: GET /data/points?agg=1m
    """
    bucket = models.DateTimeField(primary_key=True)  # time_bucket
    tenant_id = models.UUIDField()
    device_id = models.UUIDField()
    point_id = models.UUIDField()
    v_avg = models.FloatField(null=True)
    v_max = models.FloatField(null=True)
    v_min = models.FloatField(null=True)
    n = models.IntegerField()  # count
    
    class Meta:
        managed = False
        db_table = 'ts_measure_1m_tenant'
        ordering = ['-bucket']
        unique_together = ['bucket', 'tenant_id', 'device_id', 'point_id']
        verbose_name = 'Telemetry (1min Aggregate, Tenant-Scoped)'
        verbose_name_plural = 'Telemetry (1min Aggregates, Tenant-Scoped)'
    
    def __str__(self):
        return f"{self.device_id}/{self.point_id} @ {self.bucket} (1m agg)"


class TsMeasure5mTenant(models.Model):
    """
    MODEL unmanaged para VIEW ts_measure_5m_tenant (CAGG 5 minutos).
    
    Retenção: 730 dias (2 anos)
    Compressão: Sim (chunks > 7 dias)
    API: GET /data/points?agg=5m
    """
    bucket = models.DateTimeField(primary_key=True)
    tenant_id = models.UUIDField()
    device_id = models.UUIDField()
    point_id = models.UUIDField()
    v_avg = models.FloatField(null=True)
    v_max = models.FloatField(null=True)
    v_min = models.FloatField(null=True)
    n = models.IntegerField()
    
    class Meta:
        managed = False
        db_table = 'ts_measure_5m_tenant'
        ordering = ['-bucket']
        unique_together = ['bucket', 'tenant_id', 'device_id', 'point_id']
        verbose_name = 'Telemetry (5min Aggregate, Tenant-Scoped)'
        verbose_name_plural = 'Telemetry (5min Aggregates, Tenant-Scoped)'
    
    def __str__(self):
        return f"{self.device_id}/{self.point_id} @ {self.bucket} (5m agg)"


class TsMeasure1hTenant(models.Model):
    """
    MODEL unmanaged para VIEW ts_measure_1h_tenant (CAGG 1 hora).
    
    Retenção: 1825 dias (5 anos)
    Compressão: Sim (chunks > 14 dias)
    API: GET /data/points?agg=1h
    """
    bucket = models.DateTimeField(primary_key=True)
    tenant_id = models.UUIDField()
    device_id = models.UUIDField()
    point_id = models.UUIDField()
    v_avg = models.FloatField(null=True)
    v_max = models.FloatField(null=True)
    v_min = models.FloatField(null=True)
    n = models.IntegerField()
    
    class Meta:
        managed = False
        db_table = 'ts_measure_1h_tenant'
        ordering = ['-bucket']
        unique_together = ['bucket', 'tenant_id', 'device_id', 'point_id']
        verbose_name = 'Telemetry (1hour Aggregate, Tenant-Scoped)'
        verbose_name_plural = 'Telemetry (1hour Aggregates, Tenant-Scoped)'
    
    def __str__(self):
        return f"{self.device_id}/{self.point_id} @ {self.bucket} (1h agg)"
