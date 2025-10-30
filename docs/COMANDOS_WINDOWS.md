# 🪟 COMANDOS WINDOWS POWERSHELL — Fase 0

## ⚡ Setup Inicial

### 1. Navegar para o Projeto
```powershell
cd "C:\Users\Rafael Ribeiro\TrakSense\traksense-backend"
```

### 2. Subir Todos os Serviços
```powershell
docker compose -f docker/docker-compose.yml up -d --build
```

### 3. Aguardar Health Checks (30-60s)
```powershell
# Verificar status
docker compose -f docker/docker-compose.yml ps

# Ver logs em tempo real
docker compose -f docker/docker-compose.yml logs -f
```

### 4. Criar Extensão TimescaleDB (primeira vez)
```powershell
docker compose -f docker/docker-compose.yml exec postgres psql -U app -d app -c "CREATE EXTENSION IF NOT EXISTS timescaledb;"
```

### 5. Executar Migrações
```powershell
docker compose -f docker/docker-compose.yml exec api python manage.py migrate_schemas --noinput
```

### 6. Popular Dados de Desenvolvimento
```powershell
docker compose -f docker/docker-compose.yml exec api python manage.py seed_dev
```

---

## ✅ Validação

### Health Check
```powershell
curl http://localhost/health
```

### OpenAPI Schema
```powershell
curl http://localhost/api/schema/
```

### Abrir Swagger UI
```powershell
start http://localhost/api/docs/
```

### Abrir Admin
```powershell
start http://localhost/admin/
# Login: owner / Dev@123456
```

---

## 🔧 Serviços Auxiliares

### MinIO Console (S3)
```powershell
start http://localhost:9001
# Login: minioadmin / minioadmin123
```

### Mailpit (Email UI)
```powershell
start http://localhost:8025
```

### EMQX Dashboard (MQTT)
```powershell
start http://localhost:18083
# Login: admin / public
```

---

## 🐛 Troubleshooting

### Ver Logs Específicos
```powershell
# API
docker compose -f docker/docker-compose.yml logs -f api

# Worker
docker compose -f docker/docker-compose.yml logs -f worker

# Postgres
docker compose -f docker/docker-compose.yml logs -f postgres

# Todos
docker compose -f docker/docker-compose.yml logs -f
```

### Reiniciar Serviço Específico
```powershell
docker compose -f docker/docker-compose.yml restart api
docker compose -f docker/docker-compose.yml restart postgres
```

### Acessar Shell Django
```powershell
docker compose -f docker/docker-compose.yml exec api python manage.py shell
```

### Acessar Bash do Container
```powershell
docker compose -f docker/docker-compose.yml exec api bash
```

### Verificar Tenant e Domain
```powershell
docker compose -f docker/docker-compose.yml exec api python manage.py shell -c "from apps.tenants.models import Tenant, Domain; print('Tenants:', list(Tenant.objects.values('name', 'schema_name'))); print('Domains:', list(Domain.objects.values('domain', 'tenant__name')))"
```

---

## 🧹 Limpeza

### Parar Serviços
```powershell
docker compose -f docker/docker-compose.yml down
```

### Parar e Remover Volumes
```powershell
docker compose -f docker/docker-compose.yml down -v
```

### Rebuild Completo
```powershell
docker compose -f docker/docker-compose.yml down -v
docker compose -f docker/docker-compose.yml build --no-cache
docker compose -f docker/docker-compose.yml up -d
```

---

## 🔍 Verificações Avançadas

### Checar Django
```powershell
docker compose -f docker/docker-compose.yml exec api python manage.py check
```

### Listar Schemas do Banco
```powershell
docker compose -f docker/docker-compose.yml exec postgres psql -U app -d app -c "\dn"
```

### Verificar TimescaleDB
```powershell
docker compose -f docker/docker-compose.yml exec postgres psql -U app -d app -c "SELECT extname FROM pg_extension WHERE extname = 'timescaledb';"
```

### Testar Redis
```powershell
docker compose -f docker/docker-compose.yml exec redis redis-cli ping
```

### Testar MinIO
```powershell
curl http://localhost:9000/minio/health/ready
```

---

## 📦 Comandos Úteis

### Ver Containers em Execução
```powershell
docker ps
```

### Ver Uso de Recursos
```powershell
docker stats
```

### Ver Volumes
```powershell
docker volume ls
```

### Limpar Docker (cuidado!)
```powershell
# Remove containers parados
docker container prune -f

# Remove imagens não usadas
docker image prune -f

# Remove volumes não usados
docker volume prune -f

# Remove tudo (CUIDADO!)
docker system prune -a --volumes -f
```

---

## 🔐 Adicionar umc.localhost ao Hosts (Opcional)

### Windows 10/11
```powershell
# 1. Abrir Notepad como Administrador
# 2. Abrir: C:\Windows\System32\drivers\etc\hosts
# 3. Adicionar linha:
127.0.0.1 umc.localhost

# 4. Salvar
```

Ou via PowerShell Admin:
```powershell
# Execute como Administrador
Add-Content -Path C:\Windows\System32\drivers\etc\hosts -Value "`n127.0.0.1 umc.localhost"
```

Depois testar:
```powershell
ping umc.localhost
curl http://umc.localhost/health
```

---

## 📊 Checklist Completo

Copie e cole no terminal para executar tudo:

```powershell
# 1. Navegar
cd "C:\Users\Rafael Ribeiro\TrakSense\traksense-backend"

# 2. Subir
docker compose -f docker/docker-compose.yml up -d --build

# 3. Aguardar (30s)
Start-Sleep -Seconds 30

# 4. TimescaleDB
docker compose -f docker/docker-compose.yml exec postgres psql -U app -d app -c "CREATE EXTENSION IF NOT EXISTS timescaledb;"

# 5. Migrar
docker compose -f docker/docker-compose.yml exec api python manage.py migrate_schemas --noinput

# 6. Seed
docker compose -f docker/docker-compose.yml exec api python manage.py seed_dev

# 7. Health Check
curl http://localhost/health

# 8. Abrir Swagger
start http://localhost/api/docs/

# 9. Abrir Admin
start http://localhost/admin/

Write-Host "`n✅ Setup completo!" -ForegroundColor Green
Write-Host "Acesse: http://localhost/admin/" -ForegroundColor Cyan
Write-Host "Login: owner / Dev@123456" -ForegroundColor Yellow
```

---

## 🎯 Comandos Diários

### Iniciar
```powershell
cd "C:\Users\Rafael Ribeiro\TrakSense\traksense-backend"
docker compose -f docker/docker-compose.yml up -d
```

### Ver Status
```powershell
docker compose -f docker/docker-compose.yml ps
```

### Parar
```powershell
docker compose -f docker/docker-compose.yml down
```

### Logs
```powershell
docker compose -f docker/docker-compose.yml logs -f api
```

---

**Pronto para usar! 🚀**

Salve este arquivo como referência para comandos do dia-a-dia.
