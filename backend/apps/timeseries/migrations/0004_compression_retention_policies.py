# Generated manually - Fase R
# Adiciona políticas de compressão, retenção e refresh para TimescaleDB

from django.db import migrations


class Migration(migrations.Migration):
    """
    Implementa políticas operacionais do TimescaleDB para otimização.
    
    Políticas:
    ---------
    1. Compressão: chunks com > 7 dias são comprimidos (save ~10x storage)
    2. Retenção: dados com > 90 dias são deletados automaticamente
    3. Continuous Aggregates: refresh policies para 1m/5m/1h views
    
    Performance:
    -----------
    - Compressão: reduz storage em ~90% (trade-off: queries mais lentas em chunks antigos)
    - Retenção: mantém apenas 90 dias de dados raw (aggregates podem ter retenção maior)
    - Refresh policies: mantém aggregates atualizados automaticamente
    
    Operação:
    --------
    - Compressão: job em background (timescaledb scheduler)
    - Retenção: job em background (timescaledb scheduler)
    - Refresh: job em background por aggregate view
    
    IMPORTANTE: Ajustar intervalos conforme necessidade de produção!
    """

    dependencies = [
        ('timeseries', '0003_rls_and_roles'),
    ]

    operations = [
        # ============================================================================
        # 1. SKIP COMPRESSÃO (incompatível com RLS desde TimescaleDB 2.x)
        # ============================================================================
        # NOTA: TimescaleDB columnstore compression NÃO é compatível com Row Level Security.
        # Limitação: https://github.com/timescale/timescaledb/issues/1759
        # 
        # Trade-off escolhido:
        # - Manter RLS (CRÍTICO para isolamento multi-tenant)
        # - Perder compressão (aceitar storage ~10x maior)
        # 
        # Alternativas consideradas:
        # - Particionamento por tenant (schema-per-tenant + ts_measure por schema): complexidade alta
        # - Compressão manual com pg_compress: não automático
        # - Upgrade TimescaleDB 3.x quando disponível com RLS+compress
        #
        migrations.RunSQL(
            sql="""
            -- COMENTÁRIO explicativo sobre limitação
            COMMENT ON TABLE public.ts_measure IS 
            'Hypertable de telemetria IoT.
             COMPRESSÃO: DESABILITADA (incompatível com RLS no TimescaleDB 2.x).
             Retenção: dados > 90 dias são deletados automaticamente.
             RLS: isolamento por tenant_id via GUC app.tenant_id (CRÍTICO - prioridade sobre compressão).
             Storage: ~10x maior sem compressão, mas segurança multi-tenant garantida.';
            """,
            reverse_sql="""
            COMMENT ON TABLE public.ts_measure IS NULL;
            """
        ),
        
        # ============================================================================
        # 2. POLÍTICA DE RETENÇÃO (90 dias)
        # ============================================================================
        migrations.RunSQL(
            sql="""
            -- Remover política existente (se houver)
            SELECT remove_retention_policy('public.ts_measure', if_exists => true);
            
            -- Adicionar política de retenção
            -- Dados com mais de 90 dias serão deletados automaticamente
            SELECT add_retention_policy(
                'public.ts_measure',
                INTERVAL '90 days',
                if_not_exists => true
            );
            
            -- Comentário explicativo
            COMMENT ON TABLE public.ts_measure IS 
            'Hypertable de telemetria IoT.
             Retenção: dados > 90 dias deletados automaticamente (economiza storage).
             RLS: isolamento por tenant_id via GUC app.tenant_id.';
            """,
            reverse_sql="""
            -- Remover política de retenção
            SELECT remove_retention_policy('public.ts_measure', if_exists => true);
            """
        ),
        
        # ============================================================================
        # 3. REFRESH POLICIES para continuous aggregates (se existirem)
        # ============================================================================
        migrations.RunSQL(
            sql="""
            -- Configurar refresh policies para continuous aggregates (apenas se existirem)
            DO $$ BEGIN
                -- ts_measure_1m (1 minuto)
                IF EXISTS (SELECT 1 FROM pg_matviews WHERE schemaname='public' AND matviewname='ts_measure_1m') THEN
                    PERFORM remove_continuous_aggregate_policy('public.ts_measure_1m', if_exists => true);
                    PERFORM add_continuous_aggregate_policy(
                        'public.ts_measure_1m',
                        start_offset => INTERVAL '7 days',
                        end_offset => INTERVAL '1 minute',
                        schedule_interval => INTERVAL '1 minute',
                        if_not_exists => true
                    );
                    COMMENT ON MATERIALIZED VIEW public.ts_measure_1m IS
                    'Aggregate 1 minuto (avg/min/max). Refresh: a cada 1min, janela [now()-7d, now()-1m].';
                END IF;
                
                -- ts_measure_5m (5 minutos)
                IF EXISTS (SELECT 1 FROM pg_matviews WHERE schemaname='public' AND matviewname='ts_measure_5m') THEN
                    PERFORM remove_continuous_aggregate_policy('public.ts_measure_5m', if_exists => true);
                    PERFORM add_continuous_aggregate_policy(
                        'public.ts_measure_5m',
                        start_offset => INTERVAL '7 days',
                        end_offset => INTERVAL '5 minutes',
                        schedule_interval => INTERVAL '5 minutes',
                        if_not_exists => true
                    );
                    COMMENT ON MATERIALIZED VIEW public.ts_measure_5m IS
                    'Aggregate 5 minutos (avg/min/max). Refresh: a cada 5min, janela [now()-7d, now()-5m].';
                END IF;
                
                -- ts_measure_1h (1 hora)
                IF EXISTS (SELECT 1 FROM pg_matviews WHERE schemaname='public' AND matviewname='ts_measure_1h') THEN
                    PERFORM remove_continuous_aggregate_policy('public.ts_measure_1h', if_exists => true);
                    PERFORM add_continuous_aggregate_policy(
                        'public.ts_measure_1h',
                        start_offset => INTERVAL '7 days',
                        end_offset => INTERVAL '1 hour',
                        schedule_interval => INTERVAL '1 hour',
                        if_not_exists => true
                    );
                    COMMENT ON MATERIALIZED VIEW public.ts_measure_1h IS
                    'Aggregate 1 hora (avg/min/max). Refresh: a cada 1h, janela [now()-7d, now()-1h].';
                END IF;
            END $$;
            """,
            reverse_sql="""
            -- Remover refresh policies (apenas se existirem)
            DO $$ BEGIN
                IF EXISTS (SELECT 1 FROM pg_matviews WHERE schemaname='public' AND matviewname='ts_measure_1h') THEN
                    PERFORM remove_continuous_aggregate_policy('public.ts_measure_1h', if_exists => true);
                END IF;
                IF EXISTS (SELECT 1 FROM pg_matviews WHERE schemaname='public' AND matviewname='ts_measure_5m') THEN
                    PERFORM remove_continuous_aggregate_policy('public.ts_measure_5m', if_exists => true);
                END IF;
                IF EXISTS (SELECT 1 FROM pg_matviews WHERE schemaname='public' AND matviewname='ts_measure_1m') THEN
                    PERFORM remove_continuous_aggregate_policy('public.ts_measure_1m', if_exists => true);
                END IF;
            END $$;
            """
        ),
    ]
