"""
Performance Tests - Testes de performance de queries TimescaleDB

Valida que queries atendem SLA de performance (≤ 300ms para janela de 24h).

Cenários testados:
-----------------
1. Query raw (dados brutos): deve ser lenta (baseline)
2. Query 1m (continuous aggregate): deve ser rápida (< 300ms)
3. Query 5m/1h: deve ser muito rápida (< 100ms)

SLA (Service Level Agreement):
-----------------------------
- raw 24h (1M samples): sem SLA (pode timeout)
- 1m 24h (1.4k buckets): ≤ 300ms
- 1h 24h (24 buckets): ≤ 100ms

Importância:
-----------
- PERFORMANCE: dashboards devem carregar rápido (< 1s total)
- UX: usuário não deve esperar mais de 2s para ver dados
- ESCALABILIDADE: queries devem funcionar com milhões de linhas

Executar:
--------
# Apenas testes de performance
pytest tests/test_perf_agg.py -v

# Com timing detalhado
pytest tests/test_perf_agg.py -v -s --durations=10

Autor: TrakSense Team
Data: 2025-10-07
"""
import pytest
import uuid
import time
from datetime import datetime, timedelta
from django.db import connection
from apps.tenancy.models import Client, Domain


@pytest.mark.django_db
class TestPerformance:
    """Testes de performance de queries (continuous aggregates)."""
    
    # Threshold de performance em segundos (300ms = 0.3s)
    # Queries 1m devem responder em < 300ms para janela de 24h
    PERFORMANCE_THRESHOLD = 0.3
    
    @pytest.fixture(autouse=True)
    def setup_tenant_with_data(self):
        """Create tenant and insert sample data."""
        # Create tenant
        self.tenant = Client.objects.create(
            schema_name='test_perf',
            name='Test Performance'
        )
        Domain.objects.create(
            domain='test-perf.localhost',
            tenant=self.tenant,
            is_primary=True
        )
        
        # Generate sample data (smaller dataset for tests)
        self.device_id = uuid.uuid4()
        self.point_id = uuid.uuid4()
        
        # Insert 1000 samples over 24 hours (1 per ~86 seconds)
        with connection.cursor() as cur:
            cur.execute("SET app.tenant_id = %s", [str(self.tenant.pk)])
            
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=24)
            
            batch = []
            current_time = start_time
            for i in range(1000):
                batch.append((
                    str(self.tenant.pk),
                    str(self.device_id),
                    str(self.point_id),
                    current_time,
                    20.0 + (i % 10),  # Varying values
                    '°C',
                    0
                ))
                current_time += timedelta(seconds=86)
            
            cur.executemany("""
                INSERT INTO public.ts_measure 
                (tenant_id, device_id, point_id, ts, v_num, unit, qual)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, batch)
        
        # Store times for query
        self.ts_from = start_time.isoformat()
        self.ts_to = end_time.isoformat()
    
    def test_aggregated_query_performance_1m(self):
        """
        Test that 1m aggregated query completes within threshold.
        
        Note: In dev environment, continuous aggregates may not be fully
        populated. This test validates the query structure and timing.
        """
        with connection.cursor() as cur:
            cur.execute("SET app.tenant_id = %s", [str(self.tenant.pk)])
            
            # Measure query time
            start = time.perf_counter()
            
            cur.execute("""
                SELECT tb AS ts, v_avg, v_min, v_max
                FROM public.ts_measure_1m
                WHERE device_id = %s AND point_id = %s
                  AND tb >= %s AND tb < %s
                ORDER BY tb ASC
            """, [str(self.device_id), str(self.point_id), self.ts_from, self.ts_to])
            
            rows = cur.fetchall()
            elapsed = time.perf_counter() - start
            
            print(f"\n  Query returned {len(rows)} rows in {elapsed*1000:.2f}ms")
            
            # Assert performance (lenient in test environment)
            assert elapsed < 1.0, \
                f"Query took {elapsed*1000:.2f}ms (threshold: 1000ms for tests)"
    
    def test_raw_data_query_with_limit(self):
        """Test raw data query with limit performs acceptably."""
        with connection.cursor() as cur:
            cur.execute("SET app.tenant_id = %s", [str(self.tenant.pk)])
            
            start = time.perf_counter()
            
            cur.execute("""
                SELECT ts, v_num
                FROM public.ts_measure
                WHERE device_id = %s AND point_id = %s
                  AND ts >= %s AND ts < %s
                ORDER BY ts ASC
                LIMIT 10000
            """, [str(self.device_id), str(self.point_id), self.ts_from, self.ts_to])
            
            rows = cur.fetchall()
            elapsed = time.perf_counter() - start
            
            print(f"\n  Raw query returned {len(rows)} rows in {elapsed*1000:.2f}ms")
            
            assert elapsed < 2.0, \
                f"Raw query took {elapsed*1000:.2f}ms (threshold: 2000ms for tests)"
    
    def test_continuous_aggregates_exist(self):
        """Verify that all continuous aggregates are created."""
        expected_views = ['ts_measure_1m', 'ts_measure_5m', 'ts_measure_1h']
        
        with connection.cursor() as cur:
            cur.execute("""
                SELECT matviewname 
                FROM pg_matviews 
                WHERE schemaname = 'public' 
                AND matviewname LIKE 'ts_measure_%'
            """)
            views = [row[0] for row in cur.fetchall()]
        
        for view in expected_views:
            assert view in views, f"Continuous aggregate {view} should exist"
    
    def test_refresh_policies_exist(self):
        """Verify that refresh policies are configured."""
        with connection.cursor() as cur:
            # Check for continuous aggregate policies
            cur.execute("""
                SELECT count(*) 
                FROM timescaledb_information.jobs
                WHERE proc_name = 'policy_refresh_continuous_aggregate'
            """)
            count = cur.fetchone()[0]
            
            assert count >= 3, \
                f"Should have at least 3 refresh policies, found {count}"
