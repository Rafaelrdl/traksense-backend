"""
Migração 0002: Tabelas DLQ e ACK Idempotente (Fase 4)

Cria tabelas de suporte ao serviço de ingest:
- ingest_errors: Dead Letter Queue para payloads inválidos
- cmd_ack: Confirmações de comandos com idempotência
"""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('timeseries', '0001_ts_schema'),
    ]

    operations = [
        # ========== DLQ (Dead Letter Queue) ==========
        migrations.RunSQL(
            sql="""
                -- Tabela de erros de ingest (DLQ)
                CREATE TABLE IF NOT EXISTS public.ingest_errors (
                    id BIGSERIAL PRIMARY KEY,
                    tenant_id UUID,
                    topic TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    ts TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                
                -- Índice para consultas por tempo
                CREATE INDEX IF NOT EXISTS ingest_errors_ts_idx 
                ON public.ingest_errors (ts DESC);
                
                -- Índice para consultas por tenant
                CREATE INDEX IF NOT EXISTS ingest_errors_tenant_idx 
                ON public.ingest_errors (tenant_id, ts DESC);
                
                -- Comentários
                COMMENT ON TABLE public.ingest_errors IS 
                'Dead Letter Queue - payloads MQTT que falharam validação/processamento';
                
                COMMENT ON COLUMN public.ingest_errors.tenant_id IS 
                'UUID do tenant (pode ser NULL se erro for antes de parsear tópico)';
                
                COMMENT ON COLUMN public.ingest_errors.topic IS 
                'Tópico MQTT completo (ex: traksense/tenant/site/device/telem)';
                
                COMMENT ON COLUMN public.ingest_errors.payload IS 
                'Payload bruto (JSON inválido ou que falhou validação Pydantic)';
                
                COMMENT ON COLUMN public.ingest_errors.reason IS 
                'Motivo do erro (ex: "ValidationError: missing field ts")';
            """,
            reverse_sql="""
                DROP INDEX IF EXISTS public.ingest_errors_tenant_idx;
                DROP INDEX IF EXISTS public.ingest_errors_ts_idx;
                DROP TABLE IF EXISTS public.ingest_errors;
            """
        ),
        
        # ========== ACK Idempotente ==========
        migrations.RunSQL(
            sql="""
                -- Tabela de ACKs de comandos (idempotência via cmd_id único)
                CREATE TABLE IF NOT EXISTS public.cmd_ack (
                    tenant_id UUID NOT NULL,
                    device_id UUID NOT NULL,
                    cmd_id TEXT NOT NULL,
                    ok BOOLEAN NOT NULL,
                    ts_exec TIMESTAMPTZ,
                    payload JSONB,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    
                    PRIMARY KEY (tenant_id, device_id, cmd_id)
                );
                
                -- Índice para consultas por device
                CREATE INDEX IF NOT EXISTS cmd_ack_device_idx 
                ON public.cmd_ack (tenant_id, device_id, created_at DESC);
                
                -- Índice para consultas recentes
                CREATE INDEX IF NOT EXISTS cmd_ack_recent_idx 
                ON public.cmd_ack (created_at DESC);
                
                -- Comentários
                COMMENT ON TABLE public.cmd_ack IS 
                'Confirmações de comandos enviados a devices (ACKs) com idempotência via cmd_id';
                
                COMMENT ON COLUMN public.cmd_ack.cmd_id IS 
                'ULID ou UUID único do comando (chave lógica para idempotência)';
                
                COMMENT ON COLUMN public.cmd_ack.ok IS 
                'true=sucesso, false=falha na execução';
                
                COMMENT ON COLUMN public.cmd_ack.ts_exec IS 
                'Timestamp da execução no device';
                
                COMMENT ON COLUMN public.cmd_ack.payload IS 
                'Payload completo do ACK (para auditoria/debug)';
            """,
            reverse_sql="""
                DROP INDEX IF EXISTS public.cmd_ack_recent_idx;
                DROP INDEX IF EXISTS public.cmd_ack_device_idx;
                DROP TABLE IF EXISTS public.cmd_ack;
            """
        ),
        
        # ========== Política de Retenção (DLQ) ==========
        migrations.RunSQL(
            sql="""
                -- Comentário sobre retenção (job manual ou cron externo)
                COMMENT ON INDEX public.ingest_errors_ts_idx IS 
                'Retenção sugerida: 14 dias. Executar periodicamente:
                DELETE FROM public.ingest_errors WHERE ts < NOW() - INTERVAL ''14 days'';';
            """,
            reverse_sql=migrations.RunSQL.noop
        ),
    ]
