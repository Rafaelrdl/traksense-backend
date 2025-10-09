# 🧪 Testes Manuais - API /data/points

**Status**: ✅ API implementada  
**Servidor**: http://127.0.0.1:8000

---

## 📋 Pré-requisitos

1. ✅ Migrations 0005-0028 aplicadas
2. ✅ VIEWs tenant-scoped criadas
3. ✅ Models Django criados (unmanaged)
4. ✅ Middleware TenantGucMiddleware ativo
5. ✅ Servidor Django rodando: `python manage.py runserver`

---

## 🔑 Autenticação

A API requer autenticação. Para testar, você precisa:

1. **Criar um superuser** (se não tiver):
   ```bash
   python manage.py create_superuser
   ```

2. **Obter token** (DRF Token ou JWT):
   ```bash
   # Se usar DRF Token:
   curl -X POST http://localhost:8000/api/token/ \
     -H "Content-Type: application/json" \
     -d '{"username": "admin", "password": "senha"}'
   ```

3. **Usar token** nos headers:
   ```
   Authorization: Bearer <token>
   ```

---

## 🧪 Testes com curl

### Teste 1: Inserir Dados de Teste

Primeiro, vamos inserir alguns dados de teste diretamente no banco:

```bash
# Acessar PostgreSQL
cd infra
docker compose exec db psql -U app_migrations -d traksense

# Inserir dados de teste (substituir UUIDs reais)
INSERT INTO ts_measure (tenant_id, device_id, point_id, ts, v_num, unit, qual)
VALUES 
  ('11111111-1111-1111-1111-111111111111', '22222222-2222-2222-2222-222222222222', '33333333-3333-3333-3333-333333333333', NOW() - INTERVAL '1 hour', 42.5, '°C', 0),
  ('11111111-1111-1111-1111-111111111111', '22222222-2222-2222-2222-222222222222', '33333333-3333-3333-3333-333333333333', NOW() - INTERVAL '2 hours', 43.2, '°C', 0),
  ('11111111-1111-1111-1111-111111111111', '22222222-2222-2222-2222-222222222222', '33333333-3333-3333-3333-333333333333', NOW() - INTERVAL '3 hours', 41.8, '°C', 0);

# Verificar dados inseridos
SELECT COUNT(*) FROM ts_measure;
```

### Teste 2: Query com agg=raw

```bash
curl -X GET "http://localhost:8000/api/data/points?device_id=22222222-2222-2222-2222-222222222222&point_id=33333333-3333-3333-3333-333333333333&start=2025-10-08T00:00:00Z&end=2025-10-09T00:00:00Z&agg=raw" \
  -H "Authorization: Bearer <seu_token>"
```

**Esperado**:
```json
{
  "data": [
    {
      "ts": "2025-10-08T19:26:00Z",
      "device_id": "22222222-2222-2222-2222-222222222222",
      "point_id": "33333333-3333-3333-3333-333333333333",
      "v_num": 41.8,
      "v_bool": null,
      "v_text": null,
      "unit": "°C",
      "qual": 0,
      "meta": null
    },
    ...
  ],
  "count": 3,
  "agg": "raw",
  "start": "2025-10-08T00:00:00Z",
  "end": "2025-10-09T00:00:00Z",
  "device_id": "22222222-2222-2222-2222-222222222222",
  "point_id": "33333333-3333-3333-3333-333333333333"
}
```

### Teste 3: Query com agg=1m

```bash
curl -X GET "http://localhost:8000/api/data/points?device_id=22222222-2222-2222-2222-222222222222&point_id=33333333-3333-3333-3333-333333333333&start=2025-10-08T00:00:00Z&end=2025-10-09T00:00:00Z&agg=1m" \
  -H "Authorization: Bearer <seu_token>"
```

**Esperado**:
```json
{
  "data": [
    {
      "bucket": "2025-10-08T19:26:00Z",
      "v_avg": 41.8,
      "v_max": 41.8,
      "v_min": 41.8,
      "n": 1
    },
    ...
  ],
  "count": 3,
  "agg": "1m",
  "start": "2025-10-08T00:00:00Z",
  "end": "2025-10-09T00:00:00Z"
}
```

### Teste 4: Degradação Automática (window > 14d)

```bash
curl -X GET "http://localhost:8000/api/data/points?device_id=22222222-2222-2222-2222-222222222222&point_id=33333333-3333-3333-3333-333333333333&start=2025-09-01T00:00:00Z&end=2025-10-09T00:00:00Z&agg=raw" \
  -H "Authorization: Bearer <seu_token>"
```

**Esperado** (Status 422):
```json
{
  "data": [...],
  "count": ...,
  "agg": "1m",
  "degraded_from": "raw",
  "degraded_to": "1m",
  "reason": "window (38d) exceeds raw retention (14d)",
  ...
}
```

### Teste 5: Erro - Parâmetros Faltando

```bash
curl -X GET "http://localhost:8000/api/data/points" \
  -H "Authorization: Bearer <seu_token>"
```

**Esperado** (Status 400):
```json
{
  "error": "device_id, point_id, start, end são obrigatórios",
  "required_params": ["device_id", "point_id", "start", "end"],
  "optional_params": ["agg (default: raw)"]
}
```

### Teste 6: Erro - agg Inválido

```bash
curl -X GET "http://localhost:8000/api/data/points?device_id=22222222-2222-2222-2222-222222222222&point_id=33333333-3333-3333-3333-333333333333&start=2025-10-08T00:00:00Z&end=2025-10-09T00:00:00Z&agg=10m" \
  -H "Authorization: Bearer <seu_token>"
```

**Esperado** (Status 400):
```json
{
  "error": "agg='10m' inválido",
  "valid_values": ["raw", "1m", "5m", "1h"]
}
```

---

## 🧪 Testes com Postman

### Configuração

1. **Criar Collection**: "TrakSense API"
2. **Adicionar Request**: "GET /data/points"
3. **URL**: `http://localhost:8000/api/data/points`
4. **Method**: GET
5. **Params**:
   - `device_id`: `22222222-2222-2222-2222-222222222222`
   - `point_id`: `33333333-3333-3333-3333-333333333333`
   - `start`: `2025-10-08T00:00:00Z`
   - `end`: `2025-10-09T00:00:00Z`
   - `agg`: `raw` (ou `1m`, `5m`, `1h`)
6. **Headers**:
   - `Authorization`: `Bearer <token>`

### Testes Recomendados

- [ ] agg=raw (últimas 24h)
- [ ] agg=1m (última semana)
- [ ] agg=5m (último mês)
- [ ] agg=1h (último ano)
- [ ] Degradação automática (window > 14d)
- [ ] Erro: device_id inválido (UUID mal formado)
- [ ] Erro: start > end
- [ ] Erro: sem autenticação (401)

---

## ✅ Checklist de Validação

- [ ] **Middleware ativo**: Verificar logs `TenantGucMiddleware: GUC configurado`
- [ ] **VIEWs acessíveis**: `SELECT * FROM ts_measure_tenant` funciona
- [ ] **Isolamento**: Dois tenants não vazam dados
- [ ] **Degradação**: window > 14d degrada para 1m
- [ ] **Errors**: Parâmetros inválidos retornam 400
- [ ] **Performance**: Query 1h com 30 dias < 300ms

---

## 🐛 Troubleshooting

### Problema: 500 Internal Server Error

**Causa**: Middleware não configurou GUC.

**Verificação**:
```python
# No shell Django:
from django.db import connection
with connection.cursor() as cur:
    cur.execute("SHOW app.tenant_id")
    print(cur.fetchone())  # deve retornar UUID, não vazio
```

**Solução**: Verificar se `TenantGucMiddleware` está ativo em `settings.py`.

---

### Problema: 0 linhas retornadas

**Causa**: GUC não configurado ou tenant_id errado.

**Verificação**:
```sql
-- No PostgreSQL:
SET app.tenant_id = '11111111-1111-1111-1111-111111111111';
SELECT COUNT(*) FROM ts_measure_tenant;  -- deve retornar > 0
```

---

### Problema: "relation does not exist"

**Causa**: VIEWs não criadas (migration 0027 não aplicada).

**Solução**:
```bash
python manage.py migrate timeseries 0027_tenant_scoped_views
```

---

## 📊 Próximos Passos

- [ ] **Testes automatizados**: `test_api_data_points.py`
- [ ] **Swagger/OpenAPI**: Documentação automática
- [ ] **Rate limiting**: Throttling por usuário/tenant
- [ ] **Cache**: Redis para queries frequentes
- [ ] **WebSocket**: Streaming real-time

---

**Última atualização**: 2025-10-08  
**Status**: ✅ API IMPLEMENTADA E PRONTA PARA TESTE
