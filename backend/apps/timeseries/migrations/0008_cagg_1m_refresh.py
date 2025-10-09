# Generated manually - Debug - operação 3: REFRESH POLICY
from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('timeseries', '0007_cagg_1m_index'),
    ]
    
    operations = [
        migrations.RunSQL(
            sql="""
            -- Remover policy existente (se houver)
            DO $$ 
            BEGIN
                PERFORM remove_continuous_aggregate_policy('public.ts_measure_1m', if_exists => true);
            EXCEPTION 
                WHEN OTHERS THEN
                    RAISE NOTICE 'Nenhuma refresh policy para remover';
            END $$;
            
            -- Adicionar refresh policy
            SELECT add_continuous_aggregate_policy(
                'public.ts_measure_1m',
                start_offset => INTERVAL '14 days',
                end_offset   => INTERVAL '1 minute',
                schedule_interval => INTERVAL '1 minute',
                if_not_exists => true
            );
            
            DO $$ BEGIN
                RAISE NOTICE 'Refresh policy configurada: ts_measure_1m refresh a cada 1min';
            END $$;
            """,
            reverse_sql="""
            DO $$ 
            BEGIN
                PERFORM remove_continuous_aggregate_policy('public.ts_measure_1m', if_exists => true);
            EXCEPTION 
                WHEN OTHERS THEN NULL;
            END $$;
            """
        ),
    ]
