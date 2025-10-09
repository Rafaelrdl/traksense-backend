# Generated manually - Debug - operação 4: HABILITAR COMPRESSÃO
from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('timeseries', '0008_cagg_1m_refresh'),
    ]
    
    operations = [
        migrations.RunSQL(
            sql="""
            -- CAGGs NÃO têm RLS, portanto compressão é COMPATÍVEL
            ALTER MATERIALIZED VIEW public.ts_measure_1m
                SET (timescaledb.compress = true);
            
            DO $$ BEGIN
                RAISE NOTICE 'Compressão habilitada: ts_measure_1m (compatível - sem RLS)';
            END $$;
            """,
            reverse_sql="""
            ALTER MATERIALIZED VIEW public.ts_measure_1m
                SET (timescaledb.compress = false);
            """
        ),
    ]
