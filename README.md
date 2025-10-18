# TrakSense / ClimaTrak Backend

Backend multi-tenant para monitoramento HVAC/IoT com Django REST Framework, TimescaleDB, MQTT e Celery.

## 🏗️ Arquitetura

- **Framework**: Django 5 + Django REST Framework
- **Multi-tenancy**: `django-tenants` com schema PostgreSQL por tenant
- **Database**: PostgreSQL 16 + TimescaleDB para séries temporais
- **Cache/Broker**: Redis
- **Storage**: MinIO (S3-compatible)
- **MQTT**: EMQX para ingestão de telemetria
- **Tasks**: Celery + Celery Beat
- **Email**: Mailpit (desenvolvimento)
- **Proxy**: Nginx
- **Docs**: OpenAPI 3 com drf-spectacular

## 🚀 Quick Start

### Pré-requisitos

- Docker & Docker Compose
- Make (opcional, mas recomendado)

### 1. Clone e Configure

```bash
# Clone o repositório
git clone <repo-url>
cd traksense-backend

# Copie o arquivo de ambiente
cp .env.example .env

# (Opcional) Ajuste as variáveis no .env
```

### 2. Inicie os Serviços

```bash
# Usando Make (recomendado)
make dev

# Ou diretamente com docker compose
docker compose -f docker/docker-compose.yml up -d
```

### 3. Execute Migrações e Seed

```bash
# Migrações (cria schemas de tenant)
make migrate

# Seed de desenvolvimento (cria tenant + usuário)
make seed
```

### 4. Provisionar EMQX (Rule Engine)

```bash
# Windows (PowerShell) - dê permissão de execução primeiro se necessário
bash docker/scripts/provision-emqx.sh

# Linux/Mac
chmod +x docker/scripts/provision-emqx.sh
./docker/scripts/provision-emqx.sh
```

Este script configura automaticamente:
- **Connector HTTP** para o backend Django
- **Action HTTP** que encaminha mensagens MQTT para `POST /ingest`
- **Rule SQL** que captura publicações em `tenants/{slug}/#`
- **Authorization rules** (dev) permitindo apenas tópicos do tenant

### 5. Acesse a Aplicação

- **API**: http://localhost
- **Swagger Docs**: http://localhost/api/docs/
- **ReDoc**: http://localhost/api/redoc/
- **Health Check**: http://localhost/health

**Tenant de Desenvolvimento:**
- **URL**: http://umc.localhost
- **Email**: owner@umc.localhost
- **Password**: Dev@123456

**Serviços Auxiliares:**
- **MinIO Console**: http://localhost:9001 (minioadmin / minioadmin123)
- **EMQX Dashboard**: http://localhost:18083 (admin / public)
- **Mailpit UI**: http://localhost:8025
- **PostgreSQL**: localhost:5432 (app / app / app)
- **Redis**: localhost:6379

> **💡 Dica EMQX**: Após provisionar, acesse o Dashboard em http://localhost:18083 para visualizar o Connector, Action e Rule criados. Use `admin/public` para login (dev).

## 📋 Comandos Make

```bash
make help      # Mostra todos os comandos disponíveis
make dev       # Inicia todos os serviços
make stop      # Para todos os serviços
make migrate   # Executa migrações do banco
make seed      # Popula dados de desenvolvimento
make check     # Valida health checks e configuração
make fmt       # Formata código (black + isort)
make lint      # Executa linters (ruff)
make test      # Executa testes (futuro)
make ci        # Executa lint + test
make clean     # Remove volumes e cache
```

## 🗄️ Estrutura do Projeto

```
traksense-backend/
├── apps/
│   ├── tenants/          # Multi-tenancy (Tenant, Domain)
│   ├── accounts/         # Usuários e autenticação (Fase 1)
│   ├── common/           # Utilitários compartilhados
│   └── ...               # Outros apps (fases futuras)
├── config/
│   ├── settings/         # Configurações Django
│   ├── urls.py           # Rotas principais
│   ├── wsgi.py           # WSGI entry point
│   ├── asgi.py           # ASGI entry point
│   └── celery.py         # Configuração Celery
├── docker/
│   ├── docker-compose.yml
│   ├── api/Dockerfile
│   ├── nginx/nginx.conf
│   └── scripts/
├── .env.example
├── requirements.txt
├── manage.py
├── Makefile
└── README.md
```

## 🔧 Desenvolvimento

### Acessar Shell do Django

```bash
docker compose -f docker/docker-compose.yml exec api python manage.py shell
```

### Criar Novo App

```bash
docker compose -f docker/docker-compose.yml exec api python manage.py startapp <app_name> apps/<app_name>
```

### Ver Logs

```bash
# Todos os serviços
docker compose -f docker/docker-compose.yml logs -f

# Serviço específico
docker compose -f docker/docker-compose.yml logs -f api
docker compose -f docker/docker-compose.yml logs -f worker
```

### Executar Comandos Custom

```bash
docker compose -f docker/docker-compose.yml exec api python manage.py <comando>
```

## 🧪 Testes

```bash
# Executar todos os testes (quando implementados)
make test

# Com cobertura
docker compose -f docker/docker-compose.yml exec api pytest --cov=apps
```

## 📚 API Documentation

A documentação da API está disponível em múltiplos formatos:

- **Swagger UI**: http://localhost/api/docs/
- **ReDoc**: http://localhost/api/redoc/
- **OpenAPI Schema**: http://localhost/api/schema/

## 🔐 Multi-Tenancy

O sistema usa `django-tenants` com **schema por tenant**:

1. Cada tenant tem seu próprio schema PostgreSQL
2. Dados completamente isolados entre tenants
3. Roteamento por domínio/subdomain (ex: `umc.localhost`)

### Criar Novo Tenant (Produção)

```python
from apps.tenants.models import Tenant, Domain

# Criar tenant
tenant = Tenant.objects.create(
    name="ACME Corp",
    slug="acme-corp",
    schema_name="acme_corp"
)

# Criar domain
Domain.objects.create(
    domain="acme.traksense.com",
    tenant=tenant,
    is_primary=True
)
```

## 🐛 Troubleshooting

### Erro: "relation does not exist"

```bash
# Execute as migrações
make migrate
```

### Erro: MinIO health check failed

```bash
# Aguarde alguns segundos para MinIO iniciar
# Ou reinicie o serviço
docker compose -f docker/docker-compose.yml restart minio
```

### Erro: Cannot resolve umc.localhost

**Opção 1 - Usar localhost com header:**
```bash
curl -H "Host: umc.localhost" http://localhost/health
```

**Opção 2 - Adicionar ao hosts (Windows):**
```
# C:\Windows\System32\drivers\etc\hosts
127.0.0.1 umc.localhost
```

**Opção 3 - Adicionar ao hosts (Linux/Mac):**
```
# /etc/hosts
127.0.0.1 umc.localhost
```

### Erro: TimescaleDB extension not found

```bash
# Conectar ao banco e criar extensão manualmente
docker compose -f docker/docker-compose.yml exec postgres psql -U app -d app -c "CREATE EXTENSION IF NOT EXISTS timescaledb;"
```

### Erro: EMQX provisioning falhou

```bash
# Verifique se o EMQX está rodando
docker compose -f docker/docker-compose.yml ps emqx

# Verifique os logs do EMQX
docker compose -f docker/docker-compose.yml logs emqx

# Aguarde alguns segundos para o EMQX iniciar completamente
sleep 10

# Execute o provisionamento novamente
bash docker/scripts/provision-emqx.sh
```

## 📡 EMQX & MQTT

O TrakSense usa EMQX como broker MQTT para ingestão de telemetria IoT.

### Fluxo de Dados

```
Dispositivo IoT → Publica MQTT → EMQX (broker)
                                    ↓
                              Rule Engine (SQL)
                                    ↓
                              HTTP Action (POST)
                                    ↓
                              Django API (/ingest)
```

### Tópicos MQTT

O padrão de tópicos segue a estrutura multi-tenant:

```
tenants/{tenant_slug}/devices/{device_id}/sensors/{sensor_type}
```

**Exemplos:**
- `tenants/umc/devices/hvac-001/sensors/temperature`
- `tenants/umc/devices/hvac-001/sensors/humidity`
- `tenants/acme/devices/chiller-42/sensors/pressure`

### Publicando Mensagens (Teste)

Você pode testar a ingestão usando qualquer cliente MQTT:

```bash
# Usando mosquitto_pub (instalar: apt install mosquitto-clients)
mosquitto_pub -h localhost -p 1883 \
  -t "tenants/umc/devices/test-001/sensors/temperature" \
  -m '{"value": 23.5, "unit": "celsius", "timestamp": "2025-10-17T10:30:00Z"}'
```

### Verificando Regras no Dashboard

1. Acesse http://localhost:18083 (admin / public)
2. Navegue até **Integration → Rules**
3. Você verá a regra `r_umc_ingest` com:
   - **SQL**: `SELECT clientid as client_id, topic, payload, timestamp as ts FROM "tenants/umc/#"`
   - **Action**: HTTP POST para `http://api:8000/ingest`
   - **Status**: Enabled ✅

### API Keys (Produção)

Em produção, configure API Keys seguras:

```bash
# Gere uma API key forte
openssl rand -base64 32

# Atualize docker/emqx/default_api_key.conf (não versionar)
prod-provisioner:SUA_API_KEY_FORTE:administrator

# Configure no .env
EMQX_API_KEY=prod-provisioner
EMQX_API_SECRET=SUA_API_KEY_FORTE
```

### Segurança EMQX (Produção)

Para ambiente de produção, ajuste no `docker-compose.yml`:

```yaml
environment:
  EMQX_ALLOW_ANONYMOUS: "false"        # Requer autenticação
  EMQX_NODE__COOKIE: "<cookie-forte>"  # Cookie Erlang único
  EMQX_LOADED_PLUGINS: "emqx_auth_http,emqx_management,emqx_dashboard"
```

E configure authentication externa (JWT/HTTP):
- **JWT**: Tokens assinados pelo backend Django
- **HTTP**: Callback para endpoint Django de autenticação
- **Database**: PostgreSQL com credenciais por dispositivo

## 🔄 Próximas Fases

- [x] **Fase 0**: Fundação (multi-tenant + infra)
- [ ] **Fase 1**: Auth & Usuário (JWT, login, perfil)
- [ ] **Fase 2**: Equipe & Convites (memberships, roles)
- [ ] **Fase 3**: Catálogo (sites, assets, devices, sensors)
- [ ] **Fase 4**: Telemetria (ingestão MQTT, queries)
- [ ] **Fase 5**: Regras & Alertas (rules engine)
- [ ] **Fase 6**: Dashboards & Widgets (visualização)
- [ ] **Fase 7**: Relatórios (PDF/CSV)
- [ ] **Fase 8**: Notificações (email, webhooks)

## 📝 License

[Incluir licença apropriada]

## 👥 Contributing

[Incluir guidelines de contribuição]
