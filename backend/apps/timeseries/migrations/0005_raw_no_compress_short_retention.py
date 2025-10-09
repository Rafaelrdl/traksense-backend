# Generated manually - Fase R - Opção B
# Desabilita RLS em ts_measure para permitir CAGGs + retenção 14 dias

from django.db import migrations


class Migration(migrations.Migration):
    """
    Opção B: CAGGs comprimidos + Isolamento via VIEWs com security_barrier
    
    PROBLEMA DESCOBERTO:
    -------------------
    TimescaleDB NÃO permite criar Continuous Aggregates em hypertables com RLS habilitado.
    Erro: "cannot create continuous aggregate on hypertable with row security"
    
    DECISÃO ARQUITETURAL:
    --------------------
    - Desabilitar RLS na hypertable base (ts_measure)
    - Criar CAGGs 1m/5m/1h com compressão (economia massiva de storage)
    - Implementar isolamento multi-tenant via VIEWs + GUC:
      * VIEWs com security_barrier = on
      * Filtro: WHERE tenant_id = current_setting('app.tenant_id')::uuid
      * app_user só tem acesso às VIEWs (não às tabelas base)
    
    Esta migration:
    --------------
    1. Remove políticas RLS existentes
    2. DISABLE ROW LEVEL SECURITY em ts_measure
    3. Mantém retenção 14 dias (dados antigos nos CAGGs)
    
    Trade-off:
    ---------
    ❌ Perde: RLS nativo do PostgreSQL (isolamento no nível do banco)
    ✅ Ganha: CAGGs + compressão (~10x economia storage)
    ✅ Ganha: Performance queries agregadas (pré-computadas)
    ✅ Mantém: Isolamento via VIEWs + GUC (segurança efetiva)
    
    Próximos passos:
    ---------------
    - 0006/0007/0008: Criar CAGGs 1m/5m/1h
    - 0009: Criar VIEWs tenant-scoped com security_barrier
    - 0010: Restringir GRANTs (app_user só acessa VIEWs)
    """

    dependencies = [
        ('timeseries', '0004_compression_retention_policies'),
    ]

    operations = [
        # ============================================================================
        # 1. REMOVER POLÍTICAS RLS (se existirem)
        # ============================================================================
        migrations.RunSQL(
            sql="""
            -- Remover política RLS antiga (se existir)
            DO $$ 
            BEGIN
                DROP POLICY IF EXISTS ts_measure_tenant_isolation ON public.ts_measure;
                RAISE NOTICE 'Política RLS removida (se existia)';
            EXCEPTION 
                WHEN undefined_object THEN 
                    RAISE NOTICE 'Nenhuma política RLS para remover';
            END $$;
            """,
            reverse_sql="""
            -- ROLLBACK: Recriar política RLS (se necessário)
            -- NOTA: Isso bloqueará criação de CAGGs novamente
            CREATE POLICY ts_measure_tenant_isolation
                ON public.ts_measure
                FOR ALL
                TO app_user
                USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid);
            """
        ),
        
        # ============================================================================
        # 2. DESABILITAR RLS NA HYPERTABLE
        # ============================================================================
        migrations.RunSQL(
            sql="""
            -- Desabilitar RLS completamente
            -- CRÍTICO: Permite criação de CAGGs (continuous aggregates)
            ALTER TABLE public.ts_measure DISABLE ROW LEVEL SECURITY;
            ALTER TABLE public.ts_measure NO FORCE ROW LEVEL SECURITY;
            
            DO $$ BEGIN
                RAISE NOTICE 'RLS desabilitado em ts_measure - CAGGs agora permitidos';
            END $$;
            """,
            reverse_sql="""
            -- ROLLBACK: Reabilitar RLS
            ALTER TABLE public.ts_measure ENABLE ROW LEVEL SECURITY;
            ALTER TABLE public.ts_measure FORCE ROW LEVEL SECURITY;
            """
        ),
        
        # ============================================================================
        # 3. REDUZIR RETENÇÃO: 90d → 14d
        # ============================================================================
        migrations.RunSQL(
            sql="""
            -- Remover política de retenção antiga (90 dias)
            SELECT remove_retention_policy('public.ts_measure', if_exists => true);
            
            -- Adicionar política de retenção CURTA (14 dias)
            -- Dados com mais de 14 dias serão deletados automaticamente
            -- IMPORTANTE: CAGGs devem existir para preservar histórico agregado
            SELECT add_retention_policy(
                'public.ts_measure',
                INTERVAL '14 days',
                if_not_exists => true
            );
            
            -- Atualizar comentário explicativo
            COMMENT ON TABLE public.ts_measure IS 
            'Hypertable de telemetria IoT (raw data).
             
             ARQUITETURA: Opção B - CAGGs comprimidos + Isolamento via VIEWs
             ================================================================
             
             RLS: DESABILITADO (incompatível com CAGGs no TimescaleDB 2.x)
             - CAGGs não podem ser criados em hypertables com RLS
             - Isolamento garantido via VIEWs com security_barrier + GUC
             - app_user só acessa VIEWs (não tem acesso à tabela base)
             
             COMPRESSÃO: DESABILITADA no raw (apenas nos CAGGs)
             - Raw: sem compressão, retenção curta (14 dias)
             - CAGGs: COM compressão (~10x economia), retenção longa
             
             RETENÇÃO: 14 DIAS (raw data recente)
             - Dados > 14 dias deletados automaticamente
             - Histórico preservado em CAGGs (1m/5m/1h) com retenção longa
             - Queries de janelas longas devem usar CAGGs via VIEWs
             
             ISOLAMENTO: VIEWs + GUC app.tenant_id
             - ts_measure_tenant: VIEW com WHERE tenant_id = GUC
             - security_barrier = on (PostgreSQL valida filtro)
             - Middleware seta GUC por request (SET LOCAL app.tenant_id)
             
             STORAGE: ~10x maior sem compressão, mas retenção curta (14d) compensa
             ====================================================================';
            """,
            reverse_sql="""
            -- ROLLBACK: restaurar retenção de 90 dias
            -- ATENÇÃO: dados já deletados NÃO serão recuperados
            SELECT remove_retention_policy('public.ts_measure', if_exists => true);
            SELECT add_retention_policy(
                'public.ts_measure',
                INTERVAL '90 days',
                if_not_exists => true
            );
            
            COMMENT ON TABLE public.ts_measure IS 
            'Hypertable de telemetria IoT. Retenção: 90 dias.';
            """
        ),
        
        # ============================================================================
        # 4. VALIDAR: RLS está DESABILITADO (permite CAGGs)
        # ============================================================================
        migrations.RunSQL(
            sql="""
            -- Confirmar que RLS está DESABILITADO
            DO $$ 
            DECLARE
                rls_enabled BOOLEAN;
            BEGIN
                SELECT relrowsecurity
                INTO rls_enabled
                FROM pg_class
                WHERE relname = 'ts_measure' AND relnamespace = 'public'::regnamespace;
                
                IF NOT rls_enabled THEN
                    RAISE NOTICE '✅ RLS desabilitado em ts_measure - CAGGs agora podem ser criados';
                ELSE
                    RAISE WARNING '⚠️ RLS ainda está ativo - CAGGs falharão!';
                END IF;
            END $$;
            """,
            reverse_sql=migrations.RunSQL.noop
        ),
    ]
