# Generated manually - Debug - apenas CREATE CAGG
from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('timeseries', '0005_raw_no_compress_short_retention'),
    ]
    
    operations = [
        migrations.RunSQL(
            sql="""
            DROP VIEW IF EXISTS public.ts_measure_1m CASCADE;
            DROP MATERIALIZED VIEW IF EXISTS public.ts_measure_1m CASCADE;
            
            CREATE MATERIALIZED VIEW public.ts_measure_1m
            WITH (timescaledb.continuous) AS
            SELECT 
                time_bucket('1 minute', ts) AS bucket,
                tenant_id,
                device_id,
                point_id,
                AVG(v_num) AS v_avg,
                MAX(v_num) AS v_max,
                MIN(v_num) AS v_min,
                COUNT(v_num) AS n
            FROM public.ts_measure
            WHERE v_num IS NOT NULL
            GROUP BY bucket, tenant_id, device_id, point_id
            WITH NO DATA;
            """,
            reverse_sql="DROP MATERIALIZED VIEW IF EXISTS public.ts_measure_1m CASCADE;"
        ),
    ]
