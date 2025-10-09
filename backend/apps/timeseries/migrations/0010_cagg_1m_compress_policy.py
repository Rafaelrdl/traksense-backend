# Generated manually - Debug - operação 5: COMPRESSION POLICY
from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('timeseries', '0009_cagg_1m_compress'),
    ]
    
    operations = [
        migrations.RunSQL(
            sql="""
            -- Remover policy existente (se houver)
            DO $$ 
            BEGIN
                PERFORM remove_compression_policy('public.ts_measure_1m', if_exists => true);
            EXCEPTION 
                WHEN OTHERS THEN
                    RAISE NOTICE 'Nenhuma compression policy para remover';
            END $$;
            
            -- Adicionar compression policy
            SELECT add_compression_policy(
                'public.ts_measure_1m',
                INTERVAL '7 days',
                if_not_exists => true
            );
            
            DO $$ BEGIN
                RAISE NOTICE 'Compression policy configurada: ts_measure_1m comprime após 7d';
            END $$;
            """,
            reverse_sql="""
            DO $$ 
            BEGIN
                PERFORM remove_compression_policy('public.ts_measure_1m', if_exists => true);
            EXCEPTION 
                WHEN OTHERS THEN NULL;
            END $$;
            """
        ),
    ]
