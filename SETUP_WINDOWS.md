# TrakSense — Guia de Setup para Windows

Este guia complementa o README.md com instruções específicas para Windows/PowerShell.

## Pré-requisitos Windows

1. **Docker Desktop for Windows**
   - Baixe e instale: https://www.docker.com/products/docker-desktop
   - Certifique-se de que está rodando no modo WSL 2 (recomendado)

2. **Git for Windows** (opcional, mas recomendado)
   - https://git-scm.com/download/win

3. **Make para Windows** (opcional)
   - Opção 1: Instalar via Chocolatey: `choco install make`
   - Opção 2: Usar comandos Docker Compose diretamente (veja abaixo)

## Setup Rápido (PowerShell)

### 1. Clone o repositório

```powershell
git clone <repo-url>
cd traksense-backend
```

### 2. Verifique os arquivos .env

Os arquivos `.env.api` e `.env.ingest` já estão configurados. Se precisar recriar:

```powershell
Copy-Item infra\.env.api.example infra\.env.api
Copy-Item infra\.env.ingest.example infra\.env.ingest
```

### 3. Suba os serviços

**Se você tem Make instalado:**

```powershell
make up
```

**Sem Make (usando Docker Compose diretamente):**

```powershell
docker compose -f infra/docker-compose.yml up -d --build
```

### 4. Verifique os serviços

**Health check da API:**

```powershell
Invoke-WebRequest -Uri http://localhost:8000/health | Select-Object -Expand Content
# Ou simplesmente abra no navegador: http://localhost:8000/health
```

**EMQX Dashboard:**
- Abra no navegador: http://localhost:18083
- Usuário: `admin` / Senha: `public`

### 5. Visualize os logs

```powershell
# Com Make
make logs

# Sem Make
docker compose -f infra/docker-compose.yml logs -f --tail=200
```

## Comandos Úteis (PowerShell)

### Usando Make

```powershell
make up        # Sobe todos os serviços
make down      # Derruba e remove volumes
make logs      # Exibe logs
make ps        # Status dos containers
make migrate   # Executa migrações Django
make frontend  # Ativa frontend (quando disponível)
```

### Sem Make (Docker Compose direto)

```powershell
# Subir serviços
docker compose -f infra/docker-compose.yml up -d --build

# Derrubar serviços
docker compose -f infra/docker-compose.yml down -v

# Ver logs
docker compose -f infra/docker-compose.yml logs -f --tail=200

# Status
docker compose -f infra/docker-compose.yml ps

# Executar migrações
docker compose -f infra/docker-compose.yml exec api python manage.py migrate

# Executar seed
docker compose -f infra/docker-compose.yml exec api python scripts/seed_dev.py

# Frontend (com profile)
docker compose -f infra/docker-compose.yml --profile frontend up -d --build
```

## Troubleshooting Windows

### Erro de permissão no Docker

Se você receber erros de permissão:

1. Certifique-se de que o Docker Desktop está rodando
2. Execute PowerShell como Administrador
3. Verifique se WSL 2 está habilitado

### Erro de line endings (CRLF vs LF)

Se houver problemas com scripts shell dentro dos containers:

```powershell
# Configure git para usar LF
git config --global core.autocrlf input
```

### Porta já em uso

Se a porta 8000, 5432, 6379, etc. já estiver em uso:

```powershell
# Verificar processos usando porta 8000
netstat -ano | findstr :8000

# Matar processo (substitua PID pelo número encontrado)
taskkill /PID <PID> /F
```

## Acesso aos containers

```powershell
# Shell do Django
docker compose -f infra/docker-compose.yml exec api python manage.py shell

# Shell do container (bash)
docker compose -f infra/docker-compose.yml exec api bash

# PostgreSQL
docker compose -f infra/docker-compose.yml exec db psql -U postgres -d traksense

# Redis CLI
docker compose -f infra/docker-compose.yml exec redis redis-cli
```

## Desenvolvimento Local (sem Docker)

Se preferir rodar localmente fora do Docker (não recomendado para iniciantes):

### Backend

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Ingest

```powershell
cd ingest
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

**Nota:** Você ainda precisará do Docker para EMQX, PostgreSQL e Redis.

## Próximos Passos

Após a validação da infraestrutura:

1. Implementar modelos Django (Tenant, Device, Point)
2. Configurar django-tenants
3. Criar hypertable TimescaleDB
4. Implementar adapters de ingest
5. Desenvolver APIs REST

---

**Suporte**: Para problemas específicos do Windows, consulte a documentação do Docker Desktop ou abra uma issue.
