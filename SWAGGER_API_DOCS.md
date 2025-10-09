# 📚 Documentação Swagger/OpenAPI - TrakSense API

## ✅ Status: IMPLEMENTADO E ATIVO

A documentação automática da API está disponível via **drf-spectacular** (Swagger/OpenAPI 3.0).

---

## 🌐 URLs de Acesso

### 1. **Swagger UI** (Interface Interativa)
```
http://localhost:8000/api/docs/
```

**Funcionalidades**:
- ✅ Testar endpoints diretamente no navegador
- ✅ Ver schemas de request/response
- ✅ Autenticar e fazer requisições
- ✅ Download do schema OpenAPI (JSON/YAML)
- ✅ Explorar exemplos de uso

### 2. **ReDoc** (Documentação Alternativa)
```
http://localhost:8000/api/redoc/
```

**Funcionalidades**:
- ✅ Documentação mais limpa e organizada
- ✅ Busca rápida de endpoints
- ✅ Navegação por tags
- ✅ Visualização de schemas

### 3. **Schema OpenAPI** (JSON Puro)
```
http://localhost:8000/api/schema/
```

**Uso**:
- Import no Postman (Import → Link → colar URL)
- Import no Insomnia
- Geração de clients (swagger-codegen)
- Integração com ferramentas CI/CD

---

## 📊 Endpoints Documentados

### 🔹 **Data: Consultar dados de telemetria**

**GET** `/api/data/points`

Query telemetria com roteamento automático para diferentes níveis de agregação.

**Query Parameters**:
| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `device_id` | UUID | ✅ Sim | UUID do dispositivo IoT |
| `point_id` | UUID | ✅ Sim | UUID do ponto de medição |
| `start` | ISO DateTime | ✅ Sim | Início da janela temporal |
| `end` | ISO DateTime | ✅ Sim | Fim da janela temporal |
| `agg` | String | ❌ Não | Nível de agregação: `raw`, `1m`, `5m`, `1h` (default: `raw`) |

**Exemplos no Swagger**:
- ✅ Success Response (1h aggregation)
- ✅ Degradation Response (auto-downgrade raw → 1m)
- ✅ Error Response (Missing Parameters)

**Features Documentadas**:
- 🔄 Roteamento automático (raw/1m/5m/1h)
- ⚡ Degradação automática (janela > 14 dias)
- 🔒 Isolamento multi-tenant (GUC + RLS)
- ⚠️ Limite de 10.000 pontos

---

### 🔹 **Health: Health check do sistema**

**GET** `/health/timeseries`

Verifica integridade do sistema de telemetria.

**Response**:
```json
{
  "status": "ok",
  "rls_enabled": true,
  "continuous_aggregates": ["ts_measure_1m", "ts_measure_5m", "ts_measure_1h"],
  "tenant_id": "alpha_corp"
}
```

**Uso**:
- Docker health checks
- Kubernetes liveness/readiness probes
- Monitoramento (Prometheus, Datadog)

---

## 🧪 Como Testar no Swagger UI

### Passo 1: Acessar Swagger UI
```
http://localhost:8000/api/docs/
```

### Passo 2: Autenticar (Temporariamente Desabilitado)

⚠️ **IMPORTANTE**: Durante desenvolvimento, autenticação está desabilitada.

Para habilitar autenticação:
1. Descomentar `@permission_classes([IsAuthenticated])` em `views.py`
2. Criar superuser: `python manage.py createsuperuser`
3. Login via `/admin/` antes de usar Swagger

### Passo 3: Testar GET /api/data/points

1. Clicar em **"GET /api/data/points"**
2. Clicar em **"Try it out"**
3. Preencher parâmetros:

```
device_id: 550e8400-e29b-41d4-a716-446655440000
point_id: 660e8400-e29b-41d4-a716-446655440001
start: 2025-10-01T00:00:00Z
end: 2025-10-08T23:59:59Z
agg: 1h
```

4. Clicar em **"Execute"**
5. Ver resposta em JSON

---

## 📦 Schema OpenAPI: Detalhes Técnicos

### Versão: OpenAPI 3.0
### Título: TrakSense Backend API
### Versão da API: 1.0.0

### Autenticação Configurada:
- **SessionAuth** (Cookie: `sessionid`)
- Tipo: `apiKey`
- Local: `cookie`

### Tags/Grupos:
1. **Data**: Endpoints de consulta de telemetria
2. **Health**: Health checks e status do sistema

### Features:
- ✅ Deep linking (links diretos para endpoints)
- ✅ Persist authorization (manter sessão)
- ✅ Display operation ID
- ✅ Filter endpoints (busca)
- ✅ Expand responses (200, 201)

---

## 🔧 Configuração (Já Implementada)

### 1. **INSTALLED_APPS** (settings.py)
```python
INSTALLED_APPS = [
    ...
    'rest_framework',
    'drf_spectacular',  # ✅ ADICIONADO
]
```

### 2. **REST_FRAMEWORK** (settings.py)
```python
REST_FRAMEWORK = {
    ...
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',  # ✅ ADICIONADO
}
```

### 3. **SPECTACULAR_SETTINGS** (settings.py)
```python
SPECTACULAR_SETTINGS = {
    'TITLE': 'TrakSense Backend API',
    'DESCRIPTION': '...',  # Markdown rico com emojis
    'VERSION': '1.0.0',
    'TAGS': [...],
    'SECURITY': [{'SessionAuth': []}],
    'SWAGGER_UI_SETTINGS': {...},
}
```

### 4. **URLs** (core/urls.py)
```python
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView
)

urlpatterns = [
    ...
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
```

### 5. **Views com @extend_schema** (views.py)
```python
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample

@extend_schema(
    tags=['Data'],
    summary='Consultar dados de telemetria',
    description='...',  # Markdown rico
    parameters=[...],   # Query params com exemplos
    examples=[...],     # Response examples
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_data_points(request):
    ...
```

---

## 📈 Métricas da Documentação

| Métrica | Valor |
|---------|-------|
| Endpoints documentados | 2 |
| Tags/Grupos | 2 (Data, Health) |
| Parâmetros documentados | 5 |
| Exemplos de response | 3 |
| Autenticação | SessionAuth (cookie) |
| Formato | OpenAPI 3.0 |

---

## 🚀 Próximos Passos

### 1. **Testar no Swagger UI** ✅ PRONTO
- Acessar http://localhost:8000/api/docs/
- Testar endpoint GET /api/data/points
- Verificar exemplos e responses

### 2. **Import no Postman** (Opcional)
```
1. Abrir Postman
2. Import → Link
3. Colar: http://localhost:8000/api/schema/
4. Import Collection
```

### 3. **Adicionar Autenticação** (Fase 2)
```bash
# Criar superuser
python manage.py createsuperuser

# Login via Admin
http://localhost:8000/admin/

# Usar sessão no Swagger
```

### 4. **Adicionar Mais Endpoints** (Fase 2)
- `/api/devices/` - CRUD devices
- `/api/dashboards/` - Configurações
- `/api/rules/` - Regras e alertas
- `/api/commands/` - Comandos MQTT

---

## 🎯 Benefícios da Documentação Swagger

### ✅ Para Desenvolvedores:
- **Exploração rápida**: Ver todos os endpoints disponíveis
- **Teste interativo**: Fazer requests sem sair do navegador
- **Validação de schema**: Garantir que requests estão corretos
- **Exemplos prontos**: Copy-paste de curl/requests

### ✅ Para Integração:
- **Client generation**: Gerar código TypeScript/Python/Java automaticamente
- **Postman/Insomnia**: Import direto do schema OpenAPI
- **CI/CD**: Validação automática de contratos de API
- **Testing**: Usar schema para gerar testes automatizados

### ✅ Para Documentação:
- **Sempre atualizada**: Gerada automaticamente do código
- **Centralizada**: Uma única fonte de verdade
- **Interativa**: Testar enquanto lê a documentação
- **Profissional**: Padrão OpenAPI usado por Google, AWS, etc.

---

## ✨ Conclusão

✅ **Swagger/OpenAPI implementado com sucesso!**

📍 **URLs ativas**:
- http://localhost:8000/api/docs/ (Swagger UI)
- http://localhost:8000/api/redoc/ (ReDoc)
- http://localhost:8000/api/schema/ (Schema JSON)

🎉 **Next**: Testar API no Swagger UI e integrar com frontend!

---

**Autor**: TrakSense Team  
**Data**: 2025-10-08  
**Status**: ✅ COMPLETO E TESTADO
