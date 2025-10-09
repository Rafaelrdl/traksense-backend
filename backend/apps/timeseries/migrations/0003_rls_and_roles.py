# Generated manually - Fase R
# Adiciona Row Level Security (RLS) e Roles para isolamento multi-tenant

from django.db import migrations


class Migration(migrations.Migration):
    """
    Implementa Row Level Security (RLS) e Roles para isolamento multi-tenant.
    
    RLS:
    ---
    - Habilita RLS em public.cmd_ack
    - Habilita RLS em public.ingest_errors
    - Cria políticas usando current_setting('app.tenant_id')::uuid
    
    Roles:
    -----
    - app_migrations: role com LOGIN para executar migrations
    - app_user: role sem LOGIN para uso da aplicação (read/write)
    - app_readonly: role sem LOGIN para uso read-only (relatórios)
    
    Segurança:
    ---------
    - RLS garante que tenant A não vê dados de tenant B
    - Middleware TenantGucMiddleware seta app.tenant_id em cada request
    - Ingest service seta app.tenant_id antes de INSERTs
    
    IMPORTANTE: Senhas devem ser alteradas em produção via secret manager!
    """

    dependencies = [
        ('timeseries', '0002_ingest_dlq_ack'),
    ]

    operations = [
        # ============================================================================
        # 1. CRIAR ROLES (com senha dev - MUDAR EM PRODUÇÃO!)
        # ============================================================================
        migrations.RunSQL(
            sql="""
            -- Role para migrations (tem LOGIN, usado pelo Django)
            DO $$ BEGIN
                CREATE ROLE app_migrations LOGIN PASSWORD 'dev-change-me';
                EXCEPTION WHEN duplicate_object THEN 
                    RAISE NOTICE 'Role app_migrations já existe';
            END $$;
            
            -- Role para aplicação (sem LOGIN, herdado por usuários da app)
            DO $$ BEGIN
                CREATE ROLE app_user NOLOGIN;
                EXCEPTION WHEN duplicate_object THEN 
                    RAISE NOTICE 'Role app_user já existe';
            END $$;
            
            -- Role read-only (sem LOGIN, para relatórios e auditorias)
            DO $$ BEGIN
                CREATE ROLE app_readonly NOLOGIN;
                EXCEPTION WHEN duplicate_object THEN 
                    RAISE NOTICE 'Role app_readonly já existe';
            END $$;
            """,
            reverse_sql="""
            -- CUIDADO: Não dropar roles em produção! Apenas em dev.
            DROP ROLE IF EXISTS app_readonly;
            DROP ROLE IF EXISTS app_user;
            DROP ROLE IF EXISTS app_migrations;
            """
        ),
        
        # ============================================================================
        # 2. HABILITAR RLS em cmd_ack
        # ============================================================================
        migrations.RunSQL(
            sql="""
            -- Habilitar Row Level Security
            ALTER TABLE public.cmd_ack ENABLE ROW LEVEL SECURITY;
            
            -- FORCE RLS: aplica RLS até para table owner e superuser
            ALTER TABLE public.cmd_ack FORCE ROW LEVEL SECURITY;
            
            -- Policy: apenas dados do tenant atual (via GUC app.tenant_id)
            DROP POLICY IF EXISTS cmd_ack_tenant_isolation ON public.cmd_ack;
            CREATE POLICY cmd_ack_tenant_isolation
                ON public.cmd_ack
                USING (tenant_id = current_setting('app.tenant_id', TRUE)::uuid);
            
            -- Comentário explicativo
            COMMENT ON POLICY cmd_ack_tenant_isolation ON public.cmd_ack IS
            'Isola dados por tenant usando GUC app.tenant_id. 
             TenantGucMiddleware seta o GUC em cada request.
             Sem GUC setado, nenhuma linha é visível (segurança máxima).';
            """,
            reverse_sql="""
            DROP POLICY IF EXISTS cmd_ack_tenant_isolation ON public.cmd_ack;
            ALTER TABLE public.cmd_ack DISABLE ROW LEVEL SECURITY;
            """
        ),
        
        # ============================================================================
        # 3. HABILITAR RLS em ingest_errors
        # ============================================================================
        migrations.RunSQL(
            sql="""
            -- Habilitar Row Level Security
            ALTER TABLE public.ingest_errors ENABLE ROW LEVEL SECURITY;
            
            -- FORCE RLS: aplica RLS até para table owner e superuser
            ALTER TABLE public.ingest_errors FORCE ROW LEVEL SECURITY;
            
            -- Policy: apenas dados do tenant atual (via GUC app.tenant_id)
            -- Nota: tenant_id pode ser NULL (erro antes de parsear tópico)
            DROP POLICY IF EXISTS ingest_errors_tenant_isolation ON public.ingest_errors;
            CREATE POLICY ingest_errors_tenant_isolation
                ON public.ingest_errors
                USING (
                    tenant_id IS NULL 
                    OR tenant_id = current_setting('app.tenant_id', TRUE)::uuid
                );
            
            -- Comentário explicativo
            COMMENT ON POLICY ingest_errors_tenant_isolation ON public.ingest_errors IS
            'Isola dados por tenant usando GUC app.tenant_id.
             tenant_id NULL é visível (erros antes de parsear tópico).
             TenantGucMiddleware seta o GUC em cada request.';
            """,
            reverse_sql="""
            DROP POLICY IF EXISTS ingest_errors_tenant_isolation ON public.ingest_errors;
            ALTER TABLE public.ingest_errors DISABLE ROW LEVEL SECURITY;
            """
        ),
        
        # ============================================================================
        # 4. GRANTS para app_user (read/write)
        # ============================================================================
        migrations.RunSQL(
            sql="""
            -- Grants em public schema
            GRANT USAGE ON SCHEMA public TO app_user;
            
            -- Grants em public.ts_measure (hypertable)
            GRANT SELECT, INSERT, UPDATE, DELETE ON public.ts_measure TO app_user;
            
            -- Grants em continuous aggregates (views) - apenas se existirem
            DO $$ BEGIN
                IF EXISTS (SELECT 1 FROM pg_matviews WHERE schemaname='public' AND matviewname='ts_measure_1m') THEN
                    GRANT SELECT ON public.ts_measure_1m TO app_user;
                END IF;
                IF EXISTS (SELECT 1 FROM pg_matviews WHERE schemaname='public' AND matviewname='ts_measure_5m') THEN
                    GRANT SELECT ON public.ts_measure_5m TO app_user;
                END IF;
                IF EXISTS (SELECT 1 FROM pg_matviews WHERE schemaname='public' AND matviewname='ts_measure_1h') THEN
                    GRANT SELECT ON public.ts_measure_1h TO app_user;
                END IF;
            END $$;
            
            -- Grants em cmd_ack
            GRANT SELECT, INSERT, UPDATE ON public.cmd_ack TO app_user;
            
            -- Grants em ingest_errors
            GRANT SELECT, INSERT ON public.ingest_errors TO app_user;
            
            -- Grants em sequences
            GRANT USAGE, SELECT ON SEQUENCE ingest_errors_id_seq TO app_user;
            """,
            reverse_sql="""
            REVOKE ALL ON SEQUENCE ingest_errors_id_seq FROM app_user;
            REVOKE ALL ON public.ingest_errors FROM app_user;
            REVOKE ALL ON public.cmd_ack FROM app_user;
            REVOKE ALL ON public.ts_measure_1h FROM app_user;
            REVOKE ALL ON public.ts_measure_5m FROM app_user;
            REVOKE ALL ON public.ts_measure_1m FROM app_user;
            REVOKE ALL ON public.ts_measure FROM app_user;
            REVOKE USAGE ON SCHEMA public FROM app_user;
            """
        ),
        
        # ============================================================================
        # 5. GRANTS para app_readonly (somente leitura)
        # ============================================================================
        migrations.RunSQL(
            sql="""
            -- Grants em public schema
            GRANT USAGE ON SCHEMA public TO app_readonly;
            
            -- Grants SELECT em tabelas
            GRANT SELECT ON public.ts_measure TO app_readonly;
            GRANT SELECT ON public.cmd_ack TO app_readonly;
            GRANT SELECT ON public.ingest_errors TO app_readonly;
            
            -- Grants SELECT em continuous aggregates - apenas se existirem
            DO $$ BEGIN
                IF EXISTS (SELECT 1 FROM pg_matviews WHERE schemaname='public' AND matviewname='ts_measure_1m') THEN
                    GRANT SELECT ON public.ts_measure_1m TO app_readonly;
                END IF;
                IF EXISTS (SELECT 1 FROM pg_matviews WHERE schemaname='public' AND matviewname='ts_measure_5m') THEN
                    GRANT SELECT ON public.ts_measure_5m TO app_readonly;
                END IF;
                IF EXISTS (SELECT 1 FROM pg_matviews WHERE schemaname='public' AND matviewname='ts_measure_1h') THEN
                    GRANT SELECT ON public.ts_measure_1h TO app_readonly;
                END IF;
            END $$;
            """,
            reverse_sql="""
            REVOKE SELECT ON public.ingest_errors FROM app_readonly;
            REVOKE SELECT ON public.cmd_ack FROM app_readonly;
            REVOKE SELECT ON public.ts_measure_1h FROM app_readonly;
            REVOKE SELECT ON public.ts_measure_5m FROM app_readonly;
            REVOKE SELECT ON public.ts_measure_1m FROM app_readonly;
            REVOKE SELECT ON public.ts_measure FROM app_readonly;
            REVOKE USAGE ON SCHEMA public FROM app_readonly;
            """
        ),
        
        # ============================================================================
        # 6. GRANTS para templates (public schema)
        # ============================================================================
        migrations.RunSQL(
            sql="""
            -- Grants para device_template, point_template, dashboard_template
            GRANT SELECT ON public.device_template TO app_user;
            GRANT SELECT ON public.point_template TO app_user;
            GRANT SELECT ON public.dashboard_template TO app_user;
            
            GRANT SELECT ON public.device_template TO app_readonly;
            GRANT SELECT ON public.point_template TO app_readonly;
            GRANT SELECT ON public.dashboard_template TO app_readonly;
            """,
            reverse_sql="""
            REVOKE SELECT ON public.dashboard_template FROM app_readonly;
            REVOKE SELECT ON public.point_template FROM app_readonly;
            REVOKE SELECT ON public.device_template FROM app_readonly;
            REVOKE SELECT ON public.dashboard_template FROM app_user;
            REVOKE SELECT ON public.point_template FROM app_user;
            REVOKE SELECT ON public.device_template FROM app_user;
            """
        ),
    ]
