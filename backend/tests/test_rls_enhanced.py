"""
Test RLS Enhanced - Validação completa de Row Level Security (Fase R)

Testa isolamento multi-tenant em TODAS as tabelas com RLS:
1. public.ts_measure (já testado em test_rls_isolation.py)
2. public.cmd_ack (novo)
3. public.ingest_errors (novo)

Cenários:
--------
- Tenant A não vê dados de Tenant B
- Sem GUC setado, nenhum dado é visível (RLS bloqueia)
- Com GUC incorreto, nenhum dado é visível
- INSERT respeitando RLS (tenant_id setado via GUC)

IMPORTANTE: Estes testes são CRÍTICOS para segurança!
           Falha aqui = vazamento de dados entre tenants!

Autor: TrakSense Team
Data: 2025-10-08 (Fase R)
"""

import pytest
import uuid
from django.db import connection
from apps.tenancy.models import Client, Domain


@pytest.mark.django_db
class TestRLSEnhanced:
    """
    Testes de Row Level Security (isolamento entre tenants).
    
    Valida que RLS está habilitado e funcionando corretamente em:
    - public.cmd_ack
    - public.ingest_errors
    """
    
    def test_rls_enabled_on_cmd_ack(self):
        """Verifica que RLS está habilitado em cmd_ack."""
        with connection.cursor() as cur:
            cur.execute("""
                SELECT relrowsecurity 
                FROM pg_class 
                WHERE oid = 'public.cmd_ack'::regclass
            """)
            result = cur.fetchone()
            
            assert result is not None, "Tabela cmd_ack deve existir"
            assert result[0] is True, "RLS deve estar habilitado em cmd_ack"
    
    def test_rls_enabled_on_ingest_errors(self):
        """Verifica que RLS está habilitado em ingest_errors."""
        with connection.cursor() as cur:
            cur.execute("""
                SELECT relrowsecurity 
                FROM pg_class 
                WHERE oid = 'public.ingest_errors'::regclass
            """)
            result = cur.fetchone()
            
            assert result is not None, "Tabela ingest_errors deve existir"
            assert result[0] is True, "RLS deve estar habilitado em ingest_errors"
    
    def test_rls_blocks_cross_tenant_access_cmd_ack(self):
        """
        Testa que tenant A não vê ACKs de tenant B.
        
        Cenário:
        1. Criar 2 tenants (alpha e beta)
        2. Inserir ACK para cada tenant
        3. Setar GUC para tenant A → ver apenas ACK A
        4. Setar GUC para tenant B → ver apenas ACK B
        5. Sem GUC → ver nada (RLS bloqueia)
        """
        # Criar tenants
        tenant_a = Client.objects.create(
            schema_name='test_rls_alpha',
            name='Test RLS Alpha'
        )
        Domain.objects.create(
            domain='test-rls-alpha.localhost',
            tenant=tenant_a,
            is_primary=True
        )
        
        tenant_b = Client.objects.create(
            schema_name='test_rls_beta',
            name='Test RLS Beta'
        )
        Domain.objects.create(
            domain='test-rls-beta.localhost',
            tenant=tenant_b,
            is_primary=True
        )
        
        # IDs para teste
        device_a = uuid.uuid4()
        cmd_id_a = "CMD_ALPHA_001"
        
        device_b = uuid.uuid4()
        cmd_id_b = "CMD_BETA_002"
        
        # UUIDs de tenant para RLS (cmd_ack usa tenant_id UUID, não Client.pk integer)
        # Usar UUIDs fixos para testes (namespace para RLS testing)
        tenant_a_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, f'tenant-rls-alpha-{tenant_a.pk}')
        tenant_b_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, f'tenant-rls-beta-{tenant_b.pk}')
        
        # Inserir ACK para tenant A
        with connection.cursor() as cur:
            cur.execute("SET LOCAL app.tenant_id = %s", [str(tenant_a_uuid)])
            cur.execute("""
                INSERT INTO public.cmd_ack 
                (tenant_id, device_id, cmd_id, ok, ts_exec, payload)
                VALUES (%s, %s, %s, TRUE, NOW(), '{"result": "success_a"}'::jsonb)
            """, [str(tenant_a_uuid), str(device_a), cmd_id_a])
        
        # Inserir ACK para tenant B
        with connection.cursor() as cur:
            cur.execute("SET LOCAL app.tenant_id = %s", [str(tenant_b_uuid)])
            cur.execute("""
                INSERT INTO public.cmd_ack 
                (tenant_id, device_id, cmd_id, ok, ts_exec, payload)
                VALUES (%s, %s, %s, TRUE, NOW(), '{"result": "success_b"}'::jsonb)
            """, [str(tenant_b_uuid), str(device_b), cmd_id_b])
        
        # TESTE 1: Tenant A vê apenas seu ACK
        with connection.cursor() as cur:
            cur.execute("SET LOCAL app.tenant_id = %s", [str(tenant_a_uuid)])
            cur.execute("SELECT cmd_id, payload FROM public.cmd_ack")
            rows = cur.fetchall()
            
            assert len(rows) == 1, "Tenant A deve ver apenas 1 ACK"
            assert rows[0][0] == cmd_id_a, "Tenant A deve ver apenas cmd_id_a"
            assert rows[0][1]['result'] == 'success_a', "Payload deve ser do tenant A"
        
        # TESTE 2: Tenant B vê apenas seu ACK
        with connection.cursor() as cur:
            cur.execute("SET LOCAL app.tenant_id = %s", [str(tenant_b_uuid)])
            cur.execute("SELECT cmd_id, payload FROM public.cmd_ack")
            rows = cur.fetchall()
            
            assert len(rows) == 1, "Tenant B deve ver apenas 1 ACK"
            assert rows[0][0] == cmd_id_b, "Tenant B deve ver apenas cmd_id_b"
            assert rows[0][1]['result'] == 'success_b', "Payload deve ser do tenant B"
        
        # TESTE 3: Sem GUC, não vê nada (RLS bloqueia)
        with connection.cursor() as cur:
            cur.execute("RESET app.tenant_id")
            cur.execute("SELECT count(*) FROM public.cmd_ack")
            count = cur.fetchone()[0]
            
            assert count == 0, "Sem GUC, deve ver 0 ACKs (RLS bloqueia)"
        
        # Limpar dados
        with connection.cursor() as cur:
            cur.execute("SET LOCAL app.tenant_id = %s", [str(tenant_a_uuid)])
            cur.execute("DELETE FROM public.cmd_ack WHERE tenant_id = %s", [str(tenant_a_uuid)])
            cur.execute("SET LOCAL app.tenant_id = %s", [str(tenant_b_uuid)])
            cur.execute("DELETE FROM public.cmd_ack WHERE tenant_id = %s", [str(tenant_b_uuid)])
    
    def test_rls_blocks_cross_tenant_access_ingest_errors(self):
        """
        Testa que tenant A não vê erros de ingest de tenant B.
        
        Cenário:
        1. Criar 2 tenants (alpha e beta)
        2. Inserir erro para cada tenant
        3. Setar GUC para tenant A → ver apenas erro A
        4. Setar GUC para tenant B → ver apenas erro B
        5. Sem GUC → ver erros com tenant_id NULL (não isolados)
        """
        # Criar tenants
        tenant_a = Client.objects.create(
            schema_name='test_rls_err_alpha',
            name='Test RLS Error Alpha'
        )
        Domain.objects.create(
            domain='test-rls-err-alpha.localhost',
            tenant=tenant_a,
            is_primary=True
        )
        
        tenant_b = Client.objects.create(
            schema_name='test_rls_err_beta',
            name='Test RLS Error Beta'
        )
        Domain.objects.create(
            domain='test-rls-err-beta.localhost',
            tenant=tenant_b,
            is_primary=True
        )
        
        # UUIDs de tenant para RLS (ingest_errors usa tenant_id UUID, não Client.pk integer)
        tenant_a_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, f'tenant-rls-err-alpha-{tenant_a.pk}')
        tenant_b_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, f'tenant-rls-err-beta-{tenant_b.pk}')
        
        # Inserir erro para tenant A
        with connection.cursor() as cur:
            cur.execute("SET LOCAL app.tenant_id = %s", [str(tenant_a_uuid)])
            cur.execute("""
                INSERT INTO public.ingest_errors 
                (tenant_id, topic, payload, reason)
                VALUES (%s, 'traksense/alpha/site/device', '{"bad": "json"}', 'ValidationError: missing field ts')
            """, [str(tenant_a_uuid)])
        
        # Inserir erro para tenant B
        with connection.cursor() as cur:
            cur.execute("SET LOCAL app.tenant_id = %s", [str(tenant_b_uuid)])
            cur.execute("""
                INSERT INTO public.ingest_errors 
                (tenant_id, topic, payload, reason)
                VALUES (%s, 'traksense/beta/site/device', '{"bad": "data"}', 'ValidationError: invalid timestamp')
            """, [str(tenant_b_uuid)])
        
        # Inserir erro com tenant_id NULL (erro antes de parsear tópico)
        with connection.cursor() as cur:
            cur.execute("RESET app.tenant_id")
            cur.execute("""
                INSERT INTO public.ingest_errors 
                (tenant_id, topic, payload, reason)
                VALUES (NULL, 'invalid/topic', '{}', 'Topic parse error')
            """)
        
        # TESTE 1: Tenant A vê apenas seu erro
        with connection.cursor() as cur:
            cur.execute("SET LOCAL app.tenant_id = %s", [str(tenant_a_uuid)])
            cur.execute("SELECT topic, reason FROM public.ingest_errors WHERE tenant_id IS NOT NULL")
            rows = cur.fetchall()
            
            assert len(rows) == 1, "Tenant A deve ver apenas 1 erro"
            assert 'alpha' in rows[0][0], "Tópico deve ser do tenant A"
            assert 'missing field ts' in rows[0][1], "Reason deve ser do tenant A"
        
        # TESTE 2: Tenant B vê apenas seu erro
        with connection.cursor() as cur:
            cur.execute("SET LOCAL app.tenant_id = %s", [str(tenant_b_uuid)])
            cur.execute("SELECT topic, reason FROM public.ingest_errors WHERE tenant_id IS NOT NULL")
            rows = cur.fetchall()
            
            assert len(rows) == 1, "Tenant B deve ver apenas 1 erro"
            assert 'beta' in rows[0][0], "Tópico deve ser do tenant B"
            assert 'invalid timestamp' in rows[0][1], "Reason deve ser do tenant B"
        
        # TESTE 3: Sem GUC, vê apenas erros com tenant_id NULL
        with connection.cursor() as cur:
            cur.execute("RESET app.tenant_id")
            cur.execute("SELECT count(*) FROM public.ingest_errors")
            count = cur.fetchone()[0]
            
            # Deve ver apenas o erro com tenant_id NULL (policy permite NULL)
            assert count == 1, "Sem GUC, deve ver apenas erros com tenant_id NULL"
        
        # Limpar dados
        with connection.cursor() as cur:
            cur.execute("SET LOCAL app.tenant_id = %s", [str(tenant_a_uuid)])
            cur.execute("DELETE FROM public.ingest_errors WHERE tenant_id = %s", [str(tenant_a_uuid)])
            cur.execute("SET LOCAL app.tenant_id = %s", [str(tenant_b_uuid)])
            cur.execute("DELETE FROM public.ingest_errors WHERE tenant_id = %s", [str(tenant_b_uuid)])
            cur.execute("RESET app.tenant_id")
            cur.execute("DELETE FROM public.ingest_errors WHERE tenant_id IS NULL")
    
    def test_rls_policy_exists_cmd_ack(self):
        """Verifica que a policy RLS existe em cmd_ack."""
        with connection.cursor() as cur:
            cur.execute("""
                SELECT policyname, cmd, qual 
                FROM pg_policies 
                WHERE tablename = 'cmd_ack'
            """)
            policies = cur.fetchall()
            
            assert len(policies) > 0, "Deve existir pelo menos 1 policy em cmd_ack"
            
            policy_names = [p[0] for p in policies]
            assert 'cmd_ack_tenant_isolation' in policy_names, \
                "Policy 'cmd_ack_tenant_isolation' deve existir"
    
    def test_rls_policy_exists_ingest_errors(self):
        """Verifica que a policy RLS existe em ingest_errors."""
        with connection.cursor() as cur:
            cur.execute("""
                SELECT policyname, cmd, qual 
                FROM pg_policies 
                WHERE tablename = 'ingest_errors'
            """)
            policies = cur.fetchall()
            
            assert len(policies) > 0, "Deve existir pelo menos 1 policy em ingest_errors"
            
            policy_names = [p[0] for p in policies]
            assert 'ingest_errors_tenant_isolation' in policy_names, \
                "Policy 'ingest_errors_tenant_isolation' deve existir"
