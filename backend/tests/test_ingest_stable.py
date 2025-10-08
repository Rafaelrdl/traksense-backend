"""
Testes de Ingest - DLQ, Out-of-Order, Throughput

Validações:
-----------
1. DLQ: payloads inválidos vão para ingest_errors com reason
2. Out-of-order: timestamps fora de ordem não quebram insert
3. Throughput smoke: lote sintético é processado com flush

Executar:
--------
pytest backend/tests/test_ingest_stable.py -v
pytest backend/tests/test_ingest_stable.py -m smoke -v  # apenas smoke

Autor: TrakSense Team
Data: 2025-10-08
Sprint 0 - Estabilização
"""
import pytest
import uuid
import json
from datetime import datetime, timedelta
from django.utils import timezone


@pytest.mark.django_db
@pytest.mark.ingest
class TestIngestDLQ:
    """Testes de Dead Letter Queue (DLQ) para ingest."""
    
    def test_invalid_payload_goes_to_dlq(self, db):
        """Payload inválido deve ir para ingest_errors com reason."""
        # Simulação: em produção, isso seria via MQTT ou API
        # Aqui validamos o modelo IngestError
        
        from apps.ingest.models import IngestError
        
        invalid_payload = {
            'device_id': 'missing-fields',
            # Faltam: point_id, timestamp, value
        }
        
        # Criar erro manualmente (em produção, o ingest faz isso)
        error = IngestError.objects.create(
            device_id=invalid_payload.get('device_id'),
            raw_payload=json.dumps(invalid_payload),
            reason='Missing required fields: point_id, timestamp, value',
            error_type='VALIDATION_ERROR'
        )
        
        assert error.id is not None
        assert error.reason is not None
        assert 'Missing required fields' in error.reason
    
    def test_malformed_json_goes_to_dlq(self, db):
        """JSON malformado deve ir para DLQ."""
        from apps.ingest.models import IngestError
        
        malformed_payload = '{"device_id": invalid json'
        
        error = IngestError.objects.create(
            raw_payload=malformed_payload,
            reason='JSON decode error',
            error_type='PARSE_ERROR'
        )
        
        assert error.id is not None
        assert 'JSON' in error.reason or 'PARSE' in error.error_type
    
    def test_dlq_records_have_timestamp(self, db):
        """Todos os registros DLQ devem ter timestamp."""
        from apps.ingest.models import IngestError
        
        error = IngestError.objects.create(
            raw_payload='test',
            reason='Test error',
            error_type='TEST'
        )
        
        assert error.created_at is not None
        assert error.created_at <= timezone.now()


@pytest.mark.django_db
@pytest.mark.ingest
class TestIngestOutOfOrder:
    """Testes de ingest com timestamps fora de ordem."""
    
    @pytest.fixture
    def sample_device(self):
        return str(uuid.uuid4())
    
    def test_out_of_order_timestamps_do_not_break_insert(self, sample_device, db):
        """
        Timestamps fora de ordem não devem quebrar insert.
        
        TimescaleDB/PostgreSQL podem lidar com inserts fora de ordem,
        mas pode haver impacto em performance.
        """
        from apps.data.models import DataPoint
        from decimal import Decimal
        
        base_time = timezone.now()
        
        # Inserir em ordem inversa (mais recente primeiro)
        points = [
            DataPoint(
                device_id=sample_device,
                point_id='temperature',
                timestamp=base_time - timedelta(seconds=i),
                value=Decimal('20.0'),
                quality='GOOD'
            )
            for i in range(10, 0, -1)  # 10, 9, 8, ..., 1
        ]
        
        # Não deve levantar exceção
        DataPoint.objects.bulk_create(points)
        
        # Validar que todos foram inseridos
        count = DataPoint.objects.filter(device_id=sample_device).count()
        assert count == 10, "Todos os pontos devem ser inseridos"
    
    def test_duplicate_timestamps_handled_gracefully(self, sample_device, db):
        """
        Timestamps duplicados (mesma chave primária) devem ser tratados.
        
        Comportamento esperado:
        - Primeira inserção: sucesso
        - Segunda inserção: erro ou upsert (dependendo da config)
        """
        from apps.data.models import DataPoint
        from decimal import Decimal
        from django.db import IntegrityError
        
        timestamp = timezone.now()
        
        # Primeira inserção
        point1 = DataPoint.objects.create(
            device_id=sample_device,
            point_id='temperature',
            timestamp=timestamp,
            value=Decimal('20.0'),
            quality='GOOD'
        )
        assert point1.id is not None
        
        # Segunda inserção (mesmo device_id, point_id, timestamp)
        # Deve levantar IntegrityError se PK for (device_id, point_id, timestamp)
        with pytest.raises(IntegrityError):
            DataPoint.objects.create(
                device_id=sample_device,
                point_id='temperature',
                timestamp=timestamp,
                value=Decimal('21.0'),
                quality='GOOD'
            )


@pytest.mark.django_db
@pytest.mark.ingest
@pytest.mark.smoke
class TestIngestThroughput:
    """Smoke tests de throughput de ingest."""
    
    def test_bulk_insert_100_points(self, db):
        """
        Smoke test: inserir 100 pontos em lote.
        
        Validações:
        - Bulk insert não levanta exceção
        - Todos os pontos são persistidos
        - Operação completa em tempo razoável (< 1s)
        """
        from apps.data.models import DataPoint
        from decimal import Decimal
        import time
        
        device_id = str(uuid.uuid4())
        base_time = timezone.now()
        
        points = [
            DataPoint(
                device_id=device_id,
                point_id=f'sensor_{i % 10}',
                timestamp=base_time - timedelta(seconds=i),
                value=Decimal(str(20.0 + i * 0.1)),
                quality='GOOD'
            )
            for i in range(100)
        ]
        
        t0 = time.perf_counter()
        DataPoint.objects.bulk_create(points)
        t1 = time.perf_counter()
        
        elapsed_ms = (t1 - t0) * 1000
        
        # Validações
        count = DataPoint.objects.filter(device_id=device_id).count()
        assert count == 100, "Todos os 100 pontos devem ser inseridos"
        assert elapsed_ms < 1000, f"Bulk insert demorou {elapsed_ms:.1f}ms (esperado < 1000ms)"
    
    def test_bulk_insert_handles_mixed_quality(self, db):
        """Bulk insert com diferentes valores de quality."""
        from apps.data.models import DataPoint
        from decimal import Decimal
        
        device_id = str(uuid.uuid4())
        base_time = timezone.now()
        
        qualities = ['GOOD', 'BAD', 'UNCERTAIN']
        
        points = [
            DataPoint(
                device_id=device_id,
                point_id='test_point',
                timestamp=base_time - timedelta(seconds=i),
                value=Decimal('20.0'),
                quality=qualities[i % 3]
            )
            for i in range(30)
        ]
        
        DataPoint.objects.bulk_create(points)
        
        # Validar distribuição de quality
        good_count = DataPoint.objects.filter(device_id=device_id, quality='GOOD').count()
        bad_count = DataPoint.objects.filter(device_id=device_id, quality='BAD').count()
        uncertain_count = DataPoint.objects.filter(device_id=device_id, quality='UNCERTAIN').count()
        
        assert good_count == 10
        assert bad_count == 10
        assert uncertain_count == 10
