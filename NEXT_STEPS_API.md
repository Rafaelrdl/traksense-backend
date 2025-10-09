# 🚀 NEXT STEPS - Implementação API /data/points

**Pré-requisito**: Fase R completa (migrations 0005-0028 aplicadas) ✅

---

## 📋 Roadmap de Implementação

### **Fase S1: Middleware + GUC** (1-2 horas)

#### 1. Criar Middleware de Isolamento

**Arquivo**: `backend/apps/core/middleware.py`

```python
"""
Middleware para configurar GUC app.tenant_id baseado no tenant ativo.

CRÍTICO: Sem este middleware, as VIEWs *_tenant retornarão 0 linhas.
"""
from django.db import connection
from django_tenants.utils import get_tenant_model


class TenantIsolationMiddleware:
    """
    Configura GUC app.tenant_id para isolar queries multi-tenant via VIEWs.
    
    Fluxo:
    1. django-tenants identifica tenant do request (via domínio/schema)
    2. Este middleware configura SET LOCAL app.tenant_id = '<uuid>'
    3. VIEWs *_tenant filtram automaticamente por este GUC
    4. Queries retornam apenas dados do tenant correto
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Skip se não houver conexão DB ativa (ex: durante setup)
        if not hasattr(request, 'tenant'):
            return self.get_response(request)
        
        # Obter tenant_id do request (django-tenants)
        tenant = request.tenant
        
        # Configurar GUC para queries subsequentes neste request
        with connection.cursor() as cursor:
            cursor.execute(
                "SET LOCAL app.tenant_id = %s",
                [str(tenant.id)]  # converter UUID para string
            )
        
        # Continuar processamento do request
        response = self.get_response(request)
        
        return response
```

#### 2. Registrar Middleware

**Arquivo**: `backend/backend/settings.py`

```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
    # django-tenants (OBRIGATÓRIO antes do TenantIsolationMiddleware)
    'django_tenants.middleware.main.TenantMainMiddleware',
    
    # Nosso middleware de isolamento (ADICIONAR AQUI)
    'apps.core.middleware.TenantIsolationMiddleware',  # ← NOVO
]
```

#### 3. Testar Middleware

**Arquivo**: `backend/apps/core/tests/test_middleware_guc.py`

```python
"""
Teste para validar que middleware configura GUC corretamente.
"""
from django.test import TestCase, RequestFactory
from django.db import connection
from apps.core.middleware import TenantIsolationMiddleware


class TenantIsolationMiddlewareTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = TenantIsolationMiddleware(get_response=lambda r: None)
    
    def test_guc_configured_after_middleware(self):
        """GUC app.tenant_id deve ser configurado após middleware"""
        # Criar request fake com tenant
        request = self.factory.get('/')
        request.tenant = self.create_test_tenant()  # mock ou tenant real
        
        # Executar middleware
        self.middleware(request)
        
        # Verificar GUC configurado
        with connection.cursor() as cursor:
            cursor.execute("SHOW app.tenant_id")
            guc_value = cursor.fetchone()[0]
        
        self.assertEqual(guc_value, str(request.tenant.id))
```

**Comando**: `python manage.py test apps.core.tests.test_middleware_guc`

---

### **Fase S2: Models Django para VIEWs** (30 minutos)

#### 1. Criar Models Unmanaged

**Arquivo**: `backend/apps/timeseries/models.py`

```python
"""
Models Django para VIEWs tenant-scoped (unmanaged).

IMPORTANTE: 
- managed=False: Django não cria/altera estas tabelas (são VIEWs)
- db_table: nome exato da VIEW criada em migrations
"""
from django.db import models
import uuid


class TsMeasureTenant(models.Model):
    """
    VIEW tenant-scoped para dados raw.
    
    Filtro automático: WHERE tenant_id = current_setting('app.tenant_id')::uuid
    Retenção: 14 dias
    Uso: agg=raw
    """
    tenant_id = models.UUIDField()
    device_id = models.UUIDField()
    point_id = models.UUIDField()
    ts = models.DateTimeField()
    v_num = models.FloatField(null=True, blank=True)
    v_bool = models.BooleanField(null=True, blank=True)
    v_text = models.TextField(null=True, blank=True)
    unit = models.CharField(max_length=50, null=True, blank=True)
    qual = models.SmallIntegerField(default=0)
    meta = models.JSONField(null=True, blank=True)
    
    class Meta:
        managed = False
        db_table = 'ts_measure_tenant'
        ordering = ['-ts']
        indexes = []  # VIEWs não têm indexes próprios
    
    def __str__(self):
        return f"{self.device_id}/{self.point_id} @ {self.ts}"


class TsMeasure1mTenant(models.Model):
    """
    VIEW tenant-scoped para CAGG 1 minuto.
    
    Filtro automático: WHERE tenant_id = current_setting('app.tenant_id')::uuid
    Retenção: 365 dias
    Uso: agg=1m
    """
    bucket = models.DateTimeField(primary_key=True)  # time_bucket
    tenant_id = models.UUIDField()
    device_id = models.UUIDField()
    point_id = models.UUIDField()
    v_avg = models.FloatField(null=True)
    v_max = models.FloatField(null=True)
    v_min = models.FloatField(null=True)
    n = models.IntegerField()  # count
    
    class Meta:
        managed = False
        db_table = 'ts_measure_1m_tenant'
        ordering = ['-bucket']
        unique_together = ['bucket', 'tenant_id', 'device_id', 'point_id']
    
    def __str__(self):
        return f"{self.device_id}/{self.point_id} @ {self.bucket} (1m agg)"


class TsMeasure5mTenant(models.Model):
    """VIEW tenant-scoped para CAGG 5 minutos"""
    bucket = models.DateTimeField(primary_key=True)
    tenant_id = models.UUIDField()
    device_id = models.UUIDField()
    point_id = models.UUIDField()
    v_avg = models.FloatField(null=True)
    v_max = models.FloatField(null=True)
    v_min = models.FloatField(null=True)
    n = models.IntegerField()
    
    class Meta:
        managed = False
        db_table = 'ts_measure_5m_tenant'
        ordering = ['-bucket']


class TsMeasure1hTenant(models.Model):
    """VIEW tenant-scoped para CAGG 1 hora"""
    bucket = models.DateTimeField(primary_key=True)
    tenant_id = models.UUIDField()
    device_id = models.UUIDField()
    point_id = models.UUIDField()
    v_avg = models.FloatField(null=True)
    v_max = models.FloatField(null=True)
    v_min = models.FloatField(null=True)
    n = models.IntegerField()
    
    class Meta:
        managed = False
        db_table = 'ts_measure_1h_tenant'
        ordering = ['-bucket']
```

---

### **Fase S3: API /data/points** (2-3 horas)

#### 1. Serializers

**Arquivo**: `backend/apps/timeseries/serializers.py`

```python
from rest_framework import serializers
from .models import TsMeasureTenant, TsMeasure1mTenant, TsMeasure5mTenant, TsMeasure1hTenant


class TsMeasureRawSerializer(serializers.ModelSerializer):
    """Serializer para dados raw (agg=raw)"""
    class Meta:
        model = TsMeasureTenant
        fields = ['ts', 'v_num', 'v_bool', 'v_text', 'unit', 'qual', 'meta']


class TsMeasureAggSerializer(serializers.Serializer):
    """Serializer para dados agregados (agg=1m/5m/1h)"""
    bucket = serializers.DateTimeField(source='bucket')
    v_avg = serializers.FloatField()
    v_max = serializers.FloatField()
    v_min = serializers.FloatField()
    n = serializers.IntegerField()
```

#### 2. ViewSet

**Arquivo**: `backend/apps/timeseries/views.py`

```python
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils.dateparse import parse_datetime
from datetime import datetime, timedelta
from .models import (
    TsMeasureTenant, 
    TsMeasure1mTenant, 
    TsMeasure5mTenant, 
    TsMeasure1hTenant
)
from .serializers import TsMeasureRawSerializer, TsMeasureAggSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_data_points(request):
    """
    GET /api/data/points - Retorna dados de telemetria com roteamento automático.
    
    Query Params:
    - device_id: UUID (obrigatório)
    - point_id: UUID (obrigatório)
    - start: ISO datetime (obrigatório)
    - end: ISO datetime (obrigatório)
    - agg: 'raw' | '1m' | '5m' | '1h' (default: 'raw')
    
    Respostas:
    - 200: Dados retornados
    - 400: Parâmetros inválidos
    - 422: Degradação automática (raw → 1m)
    """
    # Validar parâmetros
    device_id = request.GET.get('device_id')
    point_id = request.GET.get('point_id')
    start_str = request.GET.get('start')
    end_str = request.GET.get('end')
    agg = request.GET.get('agg', 'raw')
    
    if not all([device_id, point_id, start_str, end_str]):
        return Response(
            {'error': 'device_id, point_id, start, end são obrigatórios'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        start = parse_datetime(start_str)
        end = parse_datetime(end_str)
    except ValueError:
        return Response(
            {'error': 'start/end devem ser ISO datetime válidos'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validar agg
    if agg not in ['raw', '1m', '5m', '1h']:
        return Response(
            {'error': f"agg='{agg}' inválido. Use: raw, 1m, 5m, 1h"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Calcular janela
    window_days = (end - start).days
    
    # Degradação automática: raw com window > 14d → usar 1m
    degraded = False
    if agg == 'raw' and window_days > 14:
        agg = '1m'
        degraded = True
    
    # Roteamento para VIEW correta
    if agg == 'raw':
        qs = TsMeasureTenant.objects.filter(
            device_id=device_id,
            point_id=point_id,
            ts__gte=start,
            ts__lte=end
        )
        serializer_class = TsMeasureRawSerializer
    elif agg == '1m':
        qs = TsMeasure1mTenant.objects.filter(
            device_id=device_id,
            point_id=point_id,
            bucket__gte=start,
            bucket__lte=end
        )
        serializer_class = TsMeasureAggSerializer
    elif agg == '5m':
        qs = TsMeasure5mTenant.objects.filter(
            device_id=device_id,
            point_id=point_id,
            bucket__gte=start,
            bucket__lte=end
        )
        serializer_class = TsMeasureAggSerializer
    elif agg == '1h':
        qs = TsMeasure1hTenant.objects.filter(
            device_id=device_id,
            point_id=point_id,
            bucket__gte=start,
            bucket__lte=end
        )
        serializer_class = TsMeasureAggSerializer
    
    # Executar query
    data = qs[:10000]  # limite 10k pontos
    serializer = serializer_class(data, many=True)
    
    # Montar response
    response_data = {
        'data': serializer.data,
        'count': len(serializer.data),
        'agg': agg,
        'start': start.isoformat(),
        'end': end.isoformat(),
    }
    
    if degraded:
        response_data['degraded_from'] = 'raw'
        response_data['degraded_to'] = '1m'
        response_data['reason'] = f'window ({window_days}d) exceeds raw retention (14d)'
    
    return Response(response_data, status=status.HTTP_200_OK)
```

#### 3. URLs

**Arquivo**: `backend/apps/timeseries/urls.py`

```python
from django.urls import path
from .views import get_data_points

urlpatterns = [
    path('data/points', get_data_points, name='data-points'),
]
```

**Registrar em `backend/backend/urls.py`**:
```python
urlpatterns = [
    ...
    path('api/', include('apps.timeseries.urls')),
]
```

---

### **Fase S4: Testes de Integração** (2-3 horas)

#### 1. Teste de Isolamento

**Arquivo**: `backend/apps/timeseries/tests/test_view_isolation.py`

```python
from django.test import TestCase
from apps.timeseries.models import TsMeasureTenant
from django.db import connection


class ViewIsolationTestCase(TestCase):
    def test_two_tenants_isolated(self):
        """Dados de tenant A não vazam para tenant B"""
        # Inserir dados para 2 tenants
        # ... (implementar)
        
        # Configurar GUC para tenant A
        with connection.cursor() as cursor:
            cursor.execute("SET app.tenant_id = %s", [tenant_a_id])
        
        # Query deve retornar apenas dados de A
        count_a = TsMeasureTenant.objects.count()
        self.assertEqual(count_a, expected_count_a)
        
        # Trocar para tenant B
        with connection.cursor() as cursor:
            cursor.execute("SET app.tenant_id = %s", [tenant_b_id])
        
        # Query deve retornar apenas dados de B
        count_b = TsMeasureTenant.objects.count()
        self.assertEqual(count_b, expected_count_b)
```

---

## ✅ Checklist de Implementação

- [ ] **S1.1**: Criar `apps/core/middleware.py`
- [ ] **S1.2**: Registrar middleware em `settings.py`
- [ ] **S1.3**: Testar middleware (`test_middleware_guc.py`)
- [ ] **S2.1**: Criar models unmanaged em `models.py`
- [ ] **S2.2**: Verificar models com `python manage.py check`
- [ ] **S3.1**: Criar serializers
- [ ] **S3.2**: Implementar view `get_data_points`
- [ ] **S3.3**: Registrar URLs
- [ ] **S3.4**: Testar API com Postman/curl
- [ ] **S4.1**: Escrever testes de isolamento
- [ ] **S4.2**: Escrever testes de CAGG correctness
- [ ] **S4.3**: Escrever testes de performance
- [ ] **S4.4**: CI/CD: todos os testes passando

---

## 🚀 Ordem de Execução

1. **Middleware primeiro** (S1) - essencial para tudo funcionar
2. **Models** (S2) - Django precisa conhecer as VIEWs
3. **API** (S3) - implementar endpoint
4. **Testes** (S4) - validar tudo funciona

---

**Estimativa Total**: 6-9 horas de desenvolvimento  
**Prioridade**: ALTA (bloqueia uso do sistema)  
**Owner**: TrakSense Backend Team
