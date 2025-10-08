"""
RLS Isolation Tests - Testes de segurança de isolamento entre tenants

TESTES CRÍTICOS para garantir que RLS funciona corretamente.

Cenários testados:
-----------------
1. Tenant A não pode ver dados de Tenant B (cross-tenant access)
2. Sem GUC configurado: queries retornam 0 linhas (RLS bloqueia tudo)
3. GUC configurado: queries retornam apenas dados do tenant atual

Importância:
-----------
- SEGURANÇA: se RLS falhar, dados vazam entre tenants
- COMPLIANCE: LGPD/GDPR exigem isolamento de dados
- CRÍTICO: esses testes NUNCA devem falhar

Executar:
--------
# Apenas testes de RLS
pytest tests/test_rls_isolation.py -v

# Com output detalhado
pytest tests/test_rls_isolation.py -v -s

Autor: TrakSense Team
Data: 2025-10-07
"""
import pytest
import uuid
from django.db import connection
from apps.tenancy.models import Client, Domain


@pytest.mark.django_db
class TestRLSIsolation:
    """Testes de Row Level Security (isolamento entre tenants)."""
    
    def test_rls_blocks_cross_tenant_access(self):
        """
        Test that tenant A cannot see tenant B's data.
        This is a CRITICAL security test.
        """
        # Create two tenants
        tenant_a = Client.objects.create(
            schema_name='test_alpha',
            name='Test Alpha'
        )
        Domain.objects.create(
            domain='test-alpha.localhost',
            tenant=tenant_a,
            is_primary=True
        )
        
        tenant_b = Client.objects.create(
            schema_name='test_beta',
            name='Test Beta'
        )
        Domain.objects.create(
            domain='test-beta.localhost',
            tenant=tenant_b,
            is_primary=True
        )
        
        # Insert data for tenant A
        device_a = uuid.uuid4()
        point_a = uuid.uuid4()
        
        with connection.cursor() as cur:
            cur.execute("SET app.tenant_id = %s", [str(tenant_a.pk)])
            cur.execute("""
                INSERT INTO public.ts_measure 
                (tenant_id, device_id, point_id, ts, v_num)
                VALUES (%s, %s, %s, NOW(), 42.0)
            """, [str(tenant_a.pk), str(device_a), str(point_a)])
        
        # Insert data for tenant B
        device_b = uuid.uuid4()
        point_b = uuid.uuid4()
        
        with connection.cursor() as cur:
            cur.execute("SET app.tenant_id = %s", [str(tenant_b.pk)])
            cur.execute("""
                INSERT INTO public.ts_measure 
                (tenant_id, device_id, point_id, ts, v_num)
                VALUES (%s, %s, %s, NOW(), 99.0)
            """, [str(tenant_b.pk), str(device_b), str(point_b)])
        
        # Now try to query as tenant A - should only see A's data
        with connection.cursor() as cur:
            cur.execute("SET app.tenant_id = %s", [str(tenant_a.pk)])
            cur.execute("SELECT v_num FROM public.ts_measure")
            rows = cur.fetchall()
            
            assert len(rows) == 1, "Tenant A should see only 1 row"
            assert rows[0][0] == 42.0, "Tenant A should see value 42.0"
        
        # Try to query as tenant B - should only see B's data
        with connection.cursor() as cur:
            cur.execute("SET app.tenant_id = %s", [str(tenant_b.pk)])
            cur.execute("SELECT v_num FROM public.ts_measure")
            rows = cur.fetchall()
            
            assert len(rows) == 1, "Tenant B should see only 1 row"
            assert rows[0][0] == 99.0, "Tenant B should see value 99.0"
        
        # Try to query without setting GUC - should see nothing (RLS blocks)
        with connection.cursor() as cur:
            cur.execute("RESET app.tenant_id")
            cur.execute("SELECT count(*) FROM public.ts_measure")
            count = cur.fetchone()[0]
            
            # Should be 0 because RLS requires GUC to be set
            assert count == 0, "Without GUC, should see no rows (RLS)"
    
    def test_rls_policy_exists(self):
        """Verify that RLS policy is active."""
        with connection.cursor() as cur:
            cur.execute("""
                SELECT polname, polcmd 
                FROM pg_policy 
                WHERE polrelid = 'public.ts_measure'::regclass
            """)
            policies = cur.fetchall()
            
            assert len(policies) > 0, "RLS policy should exist"
            policy_names = [p[0] for p in policies]
            assert 'ts_tenant_isolation' in policy_names, \
                "ts_tenant_isolation policy should exist"
    
    def test_rls_enabled_on_table(self):
        """Verify that RLS is enabled on ts_measure table."""
        with connection.cursor() as cur:
            cur.execute("""
                SELECT relrowsecurity 
                FROM pg_class 
                WHERE oid = 'public.ts_measure'::regclass
            """)
            result = cur.fetchone()
            
            assert result is not None, "ts_measure table should exist"
            assert result[0] is True, "RLS should be enabled on ts_measure"
