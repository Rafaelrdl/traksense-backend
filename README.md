# TrakSense — Plataforma IoT Multi-Tenant

Plataforma de monitoramento IoT com EMQX, Django/DRF, TimescaleDB e serviço de ingest assíncrono.

## Visão Geral

Este monorepo contém:

- **Backend (Django/DRF)**: APIs REST, modelos multi-tenant, endpoint `/health`
- **Ingest (Python assíncrono)**: Consumidor MQTT que normaliza e persiste telemetria
- **Infra**: Docker Compose com EMQX, TimescaleDB, Redis
- **Frontend (Spark)**: Desligado por padrão — existe em outro repositório

## Stack Tecnológico

- **Broker MQTT**: EMQX 5
- **Backend**: Django 4+ / Django REST Framework
- **Banco de Dados**: PostgreSQL + TimescaleDB
- **Cache/Queue**: Redis
- **Ingest**: Python asyncio (asyncio-mqtt + asyncpg + Pydantic)

## Pré-requisitos

- Docker & Docker Compose
- (Opcional) Make para comandos auxiliares

## Setup Rápido

### 1. Clone o repositório

```bash
git clone <repo-url>
cd traksense-backend
```

### 2. Configure variáveis de ambiente

Os arquivos `.env.api` e `.env.ingest` já estão criados com valores para desenvolvimento. Para produção, copie dos templates:

```bash
cp infra/.env.api.example infra/.env.api
cp infra/.env.ingest.example infra/.env.ingest
```

Edite conforme necessário (secrets, TLS, etc.).

### 3. Suba os serviços

#### Usando Make:

```bash
make up
```

#### Ou diretamente com Docker Compose:

```bash
docker compose -f infra/docker-compose.yml up -d --build
```

### 4. Verifique os serviços

- **API Health Check**: http://localhost:8000/health
  ```bash
  curl http://localhost:8000/health
  # Resposta esperada: {"status":"ok"}
  ```

- **EMQX Dashboard**: http://localhost:18083
  - Usuário padrão: `admin`
  - Senha padrão: `public` (alterar em produção)

- **Banco de dados**: `localhost:5432` (postgres/postgres)
- **Redis**: `localhost:6379`

### 5. Logs

```bash
make logs
# Ou:
docker compose -f infra/docker-compose.yml logs -f --tail=200
```

## Comandos Úteis

```bash
make up        # Sobe todos os serviços (sem frontend)
make down      # Derruba e remove volumes
make logs      # Exibe logs em tempo real
make ps        # Lista status dos containers
make migrate   # Executa migrações do Django
make seed      # Roda script de seed (futuro)
make frontend  # Ativa o serviço frontend (profile)
```

## Estrutura do Projeto

```
traksense-backend/
├── backend/              # Django/DRF API
│   ├── apps/            # Apps Django (vazio por ora)
│   ├── core/            # Configuração do projeto
│   ├── health/          # App de health check
│   ├── manage.py
│   ├── requirements.txt
│   └── Dockerfile
├── ingest/              # Serviço de ingest MQTT
│   ├── adapters/        # Normalizadores de payload (futuro)
│   ├── main.py          # Entry point
│   ├── requirements.txt
│   └── Dockerfile
├── infra/               # Infraestrutura
│   ├── docker-compose.yml
│   ├── .env.api         # Variáveis do backend
│   └── .env.ingest      # Variáveis do ingest
├── scripts/             # Scripts auxiliares
│   └── seed_dev.py      # Seed de dados de desenvolvimento
├── .github/
│   └── workflows/
│       └── ci.yml       # Pipeline CI
├── Makefile
└── README.md
```

## Frontend (Spark)

O frontend **não está neste repositório**. Ele existe em um projeto React separado.

Para habilitar o serviço frontend no Docker Compose (quando o repo do Spark for plugado):

```bash
make frontend
# Ou:
docker compose -f infra/docker-compose.yml --profile frontend up -d --build
```

O frontend ficará disponível em http://localhost:5173.

## Desenvolvimento

### Migrações do Django

```bash
docker compose -f infra/docker-compose.yml exec api python manage.py makemigrations
docker compose -f infra/docker-compose.yml exec api python manage.py migrate
```

### Acessar shell do Django

```bash
docker compose -f infra/docker-compose.yml exec api python manage.py shell
```

### Testes (futuros)

```bash
# Backend
cd backend
pytest

# Ingest
cd ingest
pytest
```

## CI/CD

O workflow `.github/workflows/ci.yml` executa:

- Lint (Ruff)
- Format check (Black)
- Verificação de imports/dependências

## MQTT — Desenvolvimento

- **Porta MQTT (sem TLS)**: `1883`
- **Porta MQTT TLS**: `8883` (não usar no dev)
- **Dashboard EMQX**: `18083`

Em produção, ativar TLS e autenticação por device.

## Próximas Fases

- [ ] Implementar modelos Django (Tenant, Device, Point, DashboardTemplate, etc.)
- [ ] Configurar `django-tenants` para multi-tenancy
- [ ] Criar hypertable TimescaleDB com RLS
- [ ] Implementar adapters de ingest (Parsec, etc.)
- [ ] Provisionamento EMQX (Auth/ACL por device)
- [ ] APIs de dados e dashboards
- [ ] Sistema de comandos (ACK)
- [ ] Regras/alertas com Celery

## Suporte

Para dúvidas ou problemas, consulte a documentação interna ou abra uma issue.

---

**Nota**: Este README cobre a Fase 1 (infra + esqueleto de serviços). Funcionalidades de negócio serão implementadas nas próximas fases.
