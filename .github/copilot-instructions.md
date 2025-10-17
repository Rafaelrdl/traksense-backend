# GitHub Copilot – Instruções do Repositório (Backend TrakSense/ClimaTrak)

> Objetivo: orientar o Copilot (Claude Sonnet 4.5) a **planejar**, **gerar** e **evoluir** o backend multi-tenant de telemetria HVAC/IoT com qualidade de produção, seguindo fases e critérios de aceitação claros.

## 0) Contexto e visão
- Produto: plataforma B2B multi-tenant para monitorar HVAC/ambiente (sensores, regras/alertas, dashboards, relatórios).
- Frontend já existe (React/TS). Este repositório é o **backend**.
- Entregas por **fases** (fundação → auth/usuário → equipe → ativos/dispositivos/sensores → ingestão/telemetria → regras/alertas → dashboards/widgets → relatórios → notificações → integrações).

## 1) Stack e padrões arquiteturais
- **API**: Django 5 + Django REST Framework.
- **Multi-tenant**: `django-tenants` com **schema por tenant** (isolamento forte).
- **DB relacional**: PostgreSQL 16.
- **Time series**: TimescaleDB (extensão no Postgres) para leituras; usar hypertable + continuous aggregates.
- **Mensageria/IoT**: EMQX (MQTT). Tópico: `tenants/{tenant}/devices/{device_id}/sensors/{sensor_id}`.
- **Assíncronas**: Celery + Redis (filas, cache, rate limiting).
- **Arquivos**: S3-compatível (MinIO em dev) p/ avatares, relatórios.
- **Docs API**: OpenAPI 3 via `drf-spectacular` (Swagger/Redoc).
- **Auth**: JWT **em cookies HttpOnly** (access curto + refresh), CSRF habilitado.
- **Observabilidade**: Sentry, logs estruturados (JSON), métricas Prometheus.
- **Entrega local**: Docker Compose com serviços nomeados: `api`, `worker`, `scheduler`, `postgres`, `timescale`, `redis`, `minio`, `emqx`, `nginx`, `mailpit`.

### Estrutura de diretórios esperada
backend/
apps/
accounts/ # usuários, auth, convites, memberships, perfis
tenants/ # models/infra de tenant + middleware
inventory/ # sites, assets, devices, sensors
telemetry/ # ingestão + leitura (queries/aggregates)
rules/ # regras, avaliações, alertas
dashboards/ # dashboards, widgets, fórmulas
reports/ # templates e jobs (PDF/CSV)
notifications/ # inbox e canais (email/webhook)
audit/ # trilha de auditoria
common/ # utils, segurança, validações, config
config/ # settings, urls, celery, asgi/wsgi
migrations/ # migrações base (multi-tenant-aware)
tests/ # suíte de testes (pytest)
manage.py
docker/
docker-compose.yml
nginx.conf

markdown
Copiar código

## 2) Convenções de código e qualidade
- **Estilo**: Black, isort, Ruff (PEP8). Docstrings numpydoc.
- **Tipagem**: `pyright`/`mypy` pragmático (em apps core).
- **DRF**: ViewSets + Routers; paginação por cursor; filtros padronizados (`status`, `site`, `q`).
- **Validações**: serializers + validators (sem `eval`). Nunca parsear fórmulas sem sandbox.
- **Segurança**: 
  - JWT em cookies HttpOnly + rotas `login`, `refresh`, `logout`.
  - RBAC por `membership.role` (`owner|admin|member`) e scoping por tenant.
  - Limitar payloads de ingest, checar unidade/faixa, rejeitar out-of-schema.
  - Sanitizar uploads; assinar URLs S3 com expiração.
- **DB**: migrações idempotentes; chaves compostas onde fizer sentido (ex.: `(sensor_id, ts)`).
- **Tests**: pytest + pytest-django; fabricores `model_bakery`; cobertura alvo mínima 80%.
- **Commits/PRs**: Conventional Commits; PR com *plan → diff → testes → docs*; rodar `make ci` local.

### Makefile (comportamento esperado)
- `make dev` (subir stack), `make fmt` (format/ruff), `make test`, `make ci` (lint+test), `make migrate`, `make createsuperuser`.

## 3) Variáveis de ambiente (exemplo)
DJANGO_SECRET_KEY=...
DB_URL=postgres://postgres:postgres@postgres:5432/app
REDIS_URL=redis://redis:6379/0
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=dev
MINIO_SECRET_KEY=devsecret
MINIO_BUCKET=files
EMQX_HOST=emqx
EMQX_MQTT_URL=mqtt://emqx:1883
JWT_SECRET=...
ALLOWED_HOSTS=localhost,api.local
CORS_ORIGINS=http://localhost:5173
MULTITENANT_MODE=subdomain # ou header
SENTRY_DSN=

markdown
Copiar código

## 4) Modelo de dados (núcleo)
- `tenant(id, name, slug, created_at)`
- `user(id, email, name, password_hash, ...)`
- `membership(id, tenant_id, user_id, role, status)`
- `invitation(id, tenant_id, email, role, token, expires_at, accepted_at)`
- `site(id, tenant_id, name, address, ...)`
- `asset(id, tenant_id, site_id, type, tag, status, ...)`
- `device(id, tenant_id, asset_id, hardware_uid, model, fw, status, api_key_hash)`
- `sensor(id, tenant_id, device_id, kind, unit, min, max, calibration, ...)`
- `reading(tenant_id, sensor_id, ts timestamptz, value double, labels jsonb)`  ← **Timescale hypertable**
- `rule(id, tenant_id, name, def_json|expr, severity, enabled)`
- `alert(id, tenant_id, rule_id, device_id?, sensor_id?, status, opened_at, closed_at, payload)`
- `dashboard(id, tenant_id, name)` / `widget(id, dashboard_id, type, query, formula, options_json)`
- `report_template(...)` / `report_job(...)`
- `notification(...)`
- `audit_log(...)`

## 5) Endpoints mínimos por fase
**Fase 0 – Fundação**
- Health: `GET /health` (db/redis/s3/tenant ping).
- OpenAPI: `GET /schema` + Swagger/Redoc.
- Tenancy: middleware + criação de `public` + `default` tenant (seed de dev).

**Fase 1 – Auth & Usuário**
- `POST /auth/register` (cria primeiro tenant + usuário owner)
- `POST /auth/login` · `POST /auth/refresh` · `POST /auth/logout`
- `GET /users/me` · `PATCH /users/me` (avatar via S3)
- `POST /password/forgot` · `POST /password/reset`

**Fase 2 – Equipe & Convites**
- `GET /team/members` · `POST /team/invitations`
- `POST /team/invitations/{token}/accept`
- `PATCH /team/members/{id}` (papéis/estado)

**Fase 3 – Catálogo**
- `GET/POST/PATCH /sites`, `/assets`, `/devices`, `/sensors` com filtros (status/site/q) e paginação.

**Fase 4 – Telemetria**
- Ingestão MQTT (worker) + opcional `POST /ingest` (batch com API key do device).
- Consulta: `GET /telemetry/series?sensor_id=...&from=...&to=...&agg=avg|p95|last&bucket=5m`.

**Fase 5 – Regras & Alertas**
- `GET/POST/PATCH /rules`, `GET /alerts`, `PATCH /alerts/{id}` (ack/close).

**Fase 6 – Dashboards & Widgets**
- `GET/POST /dashboards`, `GET/POST /widgets`.
- **Fórmulas**: avaliador sandbox com lista branca (ex.: `+ - * / ^`, `min|max|avg|sum|pXX`, refs a séries do próprio tenant).

**Fase 7 – Relatórios**
- `GET /reports/templates`, `POST /reports/jobs`, `GET /reports/jobs/{id}` (URL assinada S3).

**Fase 8 – Notificações**
- `GET /notifications`, `PATCH /notifications/{id}` (lida) + e-mail via Mailpit em dev.

## 6) Regras de implementação para o agente Copilot
1. **Sempre planeje antes**: gere um *Plano de Mudanças* no corpo do PR, listando:
   - pastas/arquivos a criar/alterar, migrações, comandos `make`, dependências.
2. **Vertical slice**: implemente a fase atual ponta-a-ponta (model → serializer → viewset → rota → testes → docs).
3. **Migrations**: crie migrações determinísticas e compatíveis com multi-tenant (schema por tenant).
4. **Testes obrigatórios**:
   - unit (models/serializers/utils), API (pytest-django + APIClient), e de tarefas Celery quando aplicável.
5. **OpenAPI**: mantenha `drf-spectacular` em sincronia; gere exemplos de request/response reais.
6. **Segurança**:
   - cookies HttpOnly + CSRF; verificação de `X-Tenant-Id` (se modo header) ou subdomínio (se modo subdomain).
   - rate limit para ingestão e consultas pesadas; limite de janela e de pontos por tenant.
7. **Fórmulas**: **proibido `eval`**. Use parser seguro; só funções whitelisted; imponha timeout e limite de memória.
8. **Telemetria**:
   - crie hypertable e continuous aggregates para downsampling; use índices por `(sensor_id, ts)`.
   - consultas devem respeitar `from/to`, `bucket`, `agg`, fuso horário e limite de linhas.
9. **MQTT**:
   - fornecer exemplo de script/cliente p/ publicar leituras de teste; validar device API key no worker.
10. **Observabilidade**: adicionar Sentry, logs JSON, métricas (latência por rota, filas Celery, ingest rate).

## 7) Definition of Done por fase (checklist)
**Fase 0**
- [ ] Docker Compose sobe todos serviços (`make dev`).
- [ ] `GET /health` ok; OpenAPI publicado.
- [ ] Tenancy ativo; seed de dev cria `default` e usuário admin (opcional).

**Fase 1**
- [ ] Registro/login/logout/refresh funcionam com cookies HttpOnly + CSRF.
- [ ] `GET/PATCH /users/me` ok; upload avatar → S3.

**Fase 2**
- [ ] Convites por e-mail (Mailpit em dev) → aceitação cria membership.
- [ ] RBAC aplicado nas rotas (owner/admin/member).

*(Demais fases seguem o mesmo padrão DoD descrito acima.)*

## 8) Comandos e CI esperados
- `make fmt`, `make lint`, `make test`, `make ci`.
- GitHub Actions: pipeline com `setup-python`, `docker compose up -d`, `psql -c "CREATE EXTENSION timescaledb"`, migrations, testes, relatório de cobertura.

## 9) Modelos e prompts do Copilot
- **Modelo**: preferir *Claude Sonnet 4.5* para tarefas de planejamento, geração e refatoração complexa.
- **Estilo de prompt** (para issues/PRs/Chat):
  - Diga *o objetivo e a fase*; liste *critérios de aceitação*; declare *arquivos e comandos*; peça *plano → código → testes → docs → verificação*.
  - Exemplo: “Implemente **Fase 1 – Auth** conforme esta instrução do repositório; gere plano de mudanças, models/serializers/viewsets/rotas, migrações, testes com pytest e atualize OpenAPI.”

## 10) Itens “não faça”
- Não usar `eval`/`exec` para fórmulas.
- Não gravar secrets no repo; usar env/Secrets do Actions.
- Não quebrar compatibilidade multi-tenant (qualquer query deve isolar por tenant).
- Não aprovar PR sem testes e sem atualização do schema OpenAPI.

---