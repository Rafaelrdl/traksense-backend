# Generated manually - Debug - operação 2: CREATE INDEX
from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('timeseries', '0006_cagg_1m_create'),
    ]
    
    operations = [
        migrations.RunSQL(
            sql="""
            -- Índice para queries típicas: filtro por tenant+device+point + range bucket
            CREATE INDEX IF NOT EXISTS ts_measure_1m_tenant_device_point_bucket_idx
                ON public.ts_measure_1m (tenant_id, device_id, point_id, bucket DESC);
            """,
            reverse_sql="""
            DROP INDEX IF EXISTS public.ts_measure_1m_tenant_device_point_bucket_idx;
            """
        ),
    ]
