# Guia de Testes - TrakSense Backend

## 🎯 Filosofia de Testes

Todos os testes devem ser:
- **Determinísticos**: Mesmo resultado em qualquer execução
- **Isolados**: Não dependem de ordem ou estado de outros testes
- **Rápidos**: Feedback em segundos, não minutos
- **Confiáveis**: Zero falsos negativos/positivos

## 🚀 Quick Start

```bash
# Todos os testes
pytest

# Com output detalhado
pytest -v -s

# Apenas smoke tests (rápidos)
pytest -m smoke

# Específico
pytest backend/tests/test_rls_isolation.py -v

# Com cobertura
pytest --cov=backend --cov-report=html
```

## 📁 Estrutura de Testes

```
backend/
├── tests/
│   ├── conftest.py                    # Fixtures globais
│   ├── test_rls_isolation.py          # Testes de segurança (RLS)
│   ├── test_aggregates_stable.py      # Testes de agregações
│   ├── test_ingest_stable.py          # Testes de ingest
│   └── test_provisioning_stable.py    # Testes de EMQX (mocado)
└── pytest.ini                         # Configuração do pytest
```

## 🔧 Fixtures Disponíveis

### `django_db_setup`
Configura banco de dados de teste (session scope).

```python
def test_example(django_db_setup):
    # Banco de dados disponível
    from apps.data.models import DataPoint
    DataPoint.objects.create(...)
```

### `api_client`
Cliente HTTP para testes de endpoints.

```python
def test_endpoint(api_client):
    response = api_client.get('/data/points?device_id=...')
    assert response.status_code == 200
```

### `db_tenant`
Helper para configurar tenant_id via GUC (RLS).

```python
def test_rls(db_tenant):
    db_tenant.set('tenant-uuid-123')
    # Queries agora filtradas por RLS
    
    db_tenant.clear()
    # RLS bloqueia tudo
```

### `freezer`
Congela tempo para testes determinísticos.

```python
def test_with_time(freezer):
    freezer.move_to('2025-01-01 00:00:00')
    # Código que depende de timezone.now()
```

## 🏷️ Marcadores (Markers)

Use marcadores para organizar testes:

```python
@pytest.mark.smoke
def test_basic_health():
    """Teste rápido de saúde."""
    pass

@pytest.mark.rls
def test_tenant_isolation():
    """Teste de segurança RLS."""
    pass

@pytest.mark.slow
def test_performance_benchmark():
    """Teste que demora >1s."""
    pass
```

Executar por marcador:
```bash
pytest -m smoke          # Apenas smoke tests
pytest -m "not slow"     # Todos exceto lentos
pytest -m "rls or ingest"  # RLS ou ingest
```

## 🛡️ Testes de Segurança (RLS)

**CRÍTICO**: Testes RLS nunca devem falhar. Se falharem, há vazamento de dados.

```python
@pytest.mark.rls
@pytest.mark.django_db
def test_tenant_isolation(db_tenant):
    """Tenant A não pode ver dados de Tenant B."""
    
    # Criar dados para Tenant A
    db_tenant.set('tenant-a')
    DataPoint.objects.create(device_id='dev-a', value=100)
    
    # Tenant B não deve ver dados de A
    db_tenant.set('tenant-b')
    count = DataPoint.objects.filter(device_id='dev-a').count()
    assert count == 0, "FALHA DE SEGURANÇA: Cross-tenant access!"
```

## ⏱️ Testes Determinísticos

### Fixar Timezone

```python
# Automático via conftest.py (TZ=UTC)
def test_timestamp():
    now = timezone.now()
    # Sempre UTC, sem surpresas
```

### Congelar Tempo

```python
def test_with_frozen_time(freezer):
    freezer.move_to('2025-01-01 00:00:00')
    
    # timezone.now() retorna sempre 2025-01-01
    assert timezone.now().year == 2025
```

### Dados Fixos

Use seeds/constantes, nunca valores aleatórios:

```python
# ❌ Errado - valor aleatório
value = random.random()

# ✅ Correto - valor fixo
value = Decimal('23.5')
```

## 🧪 Padrões de Teste

### Testes de Modelo (Unit)

```python
@pytest.mark.django_db
def test_datapoint_creation():
    """Testa criação básica de DataPoint."""
    point = DataPoint.objects.create(
        device_id='test-device',
        point_id='temperature',
        timestamp=timezone.now(),
        value=Decimal('23.5'),
        quality='GOOD'
    )
    
    assert point.id is not None
    assert point.value == Decimal('23.5')
```

### Testes de Endpoint (Integration)

```python
@pytest.mark.django_db
def test_data_points_endpoint(api_client):
    """Testa GET /data/points."""
    response = api_client.get(
        '/data/points',
        {
            'device_id': 'test-device',
            'point_id': 'temperature',
            'from': '2025-01-01T00:00:00Z',
            'to': '2025-01-01T01:00:00Z',
            'agg': '1h'
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert 'data' in data
    assert isinstance(data['data'], list)
```

### Testes com Mocks

```python
from unittest.mock import Mock, patch

@patch('apps.provisioning.EmqxClient')
def test_provisioning_with_mock(mock_client):
    """Testa provisioning sem conexão real ao EMQX."""
    mock_client.create_user.return_value = {
        'username': 'test',
        'password': 'secret'
    }
    
    # Código que usa EmqxClient
    result = provision_device('device-123')
    
    assert result['username'] == 'test'
    mock_client.create_user.assert_called_once()
```

## 🚨 Evitando Flakiness

### Isolamento de Banco

Cada teste deve limpar dados:

```python
@pytest.mark.django_db(transaction=True)
def test_isolated():
    # Dados criados aqui são rollback automaticamente
    DataPoint.objects.create(...)
```

### Timeout em Testes

Para testes que podem travar:

```python
@pytest.mark.timeout(5)  # Requer pytest-timeout
def test_with_timeout():
    # Falha se demorar >5s
    pass
```

### Evitar Race Conditions

```python
# ❌ Errado - assume ordem de criação
devices = Device.objects.all()
assert devices[0].name == 'first'

# ✅ Correto - explicita ordem
devices = Device.objects.order_by('created_at')
first = devices.first()
assert first.name == 'first'
```

## 📊 Cobertura de Código

```bash
# Gerar relatório HTML
pytest --cov=backend --cov-report=html

# Ver no terminal
pytest --cov=backend --cov-report=term-missing

# Falhar se cobertura < 80%
pytest --cov=backend --cov-fail-under=80
```

## 🐛 Troubleshooting

### Teste falhando aleatoriamente

1. Verificar se usa dados fixos (não aleatórios)
2. Verificar isolamento (rollback de transação)
3. Verificar TZ (deve ser UTC)
4. Adicionar `pytest -v -s` para ver output

### Erro "app.tenant_id not set"

```python
# Use fixture db_tenant
def test_with_tenant(db_tenant):
    db_tenant.set('tenant-uuid')
    # Agora queries funcionam
```

### Timeout em testes de integração

```python
# Marcar como slow
@pytest.mark.slow
def test_integration():
    pass

# Executar sem slow tests
pytest -m "not slow"
```

### Banco de dados não limpo entre testes

```python
# Usar transaction=True
@pytest.mark.django_db(transaction=True)
def test_clean():
    pass
```

## ✅ Checklist Antes de Commit

- [ ] `pytest` - Todos os testes passam
- [ ] `pytest -m smoke` - Smoke tests passam
- [ ] `pytest --cov` - Cobertura adequada
- [ ] Testes RLS passam (segurança crítica)
- [ ] Sem `skip` desnecessários
- [ ] Sem `print()` de debug esquecidos
- [ ] Docstrings explicam "por quê", não "o quê"

## 📚 Referências

- [Pytest Docs](https://docs.pytest.org/)
- [Django Testing](https://docs.djangoproject.com/en/stable/topics/testing/)
- [Freezegun](https://github.com/spulec/freezegun)
- [pytest-django](https://pytest-django.readthedocs.io/)

---

**🔥 Regra de Ouro**: Se um teste falha aleatoriamente, o bug está no teste, não no código.
