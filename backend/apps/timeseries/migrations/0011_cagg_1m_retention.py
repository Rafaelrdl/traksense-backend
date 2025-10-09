# Generated manually - Debug - operação 6: RETENTION POLICY
from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('timeseries', '0010_cagg_1m_compress_policy'),
    ]
    
    operations = [
        migrations.RunSQL(
            sql="""
            -- Remover policy existente (se houver)
            DO $$ 
            BEGIN
                PERFORM remove_retention_policy('public.ts_measure_1m', if_exists => true);
            EXCEPTION 
                WHEN OTHERS THEN
                    RAISE NOTICE 'Nenhuma retention policy para remover';
            END $$;
            
            -- Adicionar retention policy
            SELECT add_retention_policy(
                'public.ts_measure_1m',
                INTERVAL '365 days',
                if_not_exists => true
            );
            
            DO $$ BEGIN
                RAISE NOTICE 'Retention policy configurada: ts_measure_1m mantém 365d (1 ano)';
            END $$;
            """,
            reverse_sql="""
            DO $$ 
            BEGIN
                PERFORM remove_retention_policy('public.ts_measure_1m', if_exists => true);
            EXCEPTION 
                WHEN OTHERS THEN NULL;
            END $$;
            """
        ),
    ]
