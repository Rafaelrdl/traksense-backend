# 🚀 GUIA DE EXECUÇÃO RÁPIDA — Fase 0

## ⚡ Comandos para Executar AGORA

### 1️⃣ Subir a Stack (primeira vez)

```powershell
# No diretório traksense-backend/
cd "C:\Users\Rafael Ribeiro\TrakSense\traksense-backend"

# Subir todos os serviços
docker compose -f docker/docker-compose.yml up -d --build
```

**⏱️ Aguarde 30-60 segundos** para todos os health checks passarem.

---

### 2️⃣ Verificar Status dos Serviços

```powershell
# Ver status de todos os containers
docker compose -f docker/docker-compose.yml ps

# Ver logs em tempo real
docker compose -f docker/docker-compose.yml logs -f
```

**✅ Esperado:** Todos com status `healthy` ou `running`

---

### 3️⃣ Executar Migrações

```powershell
# Criar schemas de tenant
docker compose -f docker/docker-compose.yml exec api python manage.py migrate_schemas --noinput
```

**✅ Esperado:** Mensagens de sucesso das migrações

---

### 4️⃣ Popular Dados de Desenvolvimento

```powershell
# Criar tenant UMC + usuário owner
docker compose -f docker/docker-compose.yml exec api python manage.py seed_dev
```

**✅ Esperado:**
```
=== Seeding Development Data ===
✓ Created tenant: Uberlandia Medical Center
✓ Created domain: umc.localhost
✓ Created owner user: owner@umc.localhost

=== Seed Complete ===
Access information:
  URL: http://umc.localhost
  Email: owner@umc.localhost
  Password: Dev@123456
```

---

### 5️⃣ Testar Endpoints

#### Health Check
```powershell
# Deve retornar: {"db": true, "redis": true, "s3": true, "healthy": true}
curl http://localhost/health
```

#### OpenAPI Schema
```powershell
# Abre o Swagger UI no navegador
start http://localhost/api/docs/
```

#### Admin Interface
```powershell
# Abre o Django Admin
start http://localhost/admin/

# Login:
# Username: owner
# Password: Dev@123456
```

---

### 6️⃣ Acessar Serviços Auxiliares

```powershell
# MinIO Console (S3)
start http://localhost:9001
# Login: minioadmin / minioadmin123

# Mailpit (Email UI)
start http://localhost:8025

# EMQX Dashboard (MQTT)
start http://localhost:18083
# Login: admin / public
```

---

## 🔧 Troubleshooting

### Erro: "Cannot connect to Docker daemon"
```powershell
# Certifique-se que o Docker Desktop está rodando
```

### Erro: "Port already in use"
```powershell
# Parar todos os containers
docker compose -f docker/docker-compose.yml down

# Remover containers órfãos
docker compose -f docker/docker-compose.yml down --remove-orphans
```

### Erro: "TimescaleDB extension not created"
```powershell
# Criar extensão manualmente
docker compose -f docker/docker-compose.yml exec postgres psql -U app -d app -c "CREATE EXTENSION IF NOT EXISTS timescaledb;"
```

### Erro: "Cannot resolve umc.localhost"
```powershell
# Opção 1: Usar header HTTP
curl -H "Host: umc.localhost" http://localhost/health

# Opção 2: Adicionar ao hosts
# Editar: C:\Windows\System32\drivers\etc\hosts
# Adicionar linha: 127.0.0.1 umc.localhost
```

---

## 🧹 Comandos de Limpeza

### Parar Serviços
```powershell
docker compose -f docker/docker-compose.yml down
```

### Limpar Tudo (incluindo volumes)
```powershell
docker compose -f docker/docker-compose.yml down -v
```

### Rebuild Completo
```powershell
docker compose -f docker/docker-compose.yml down -v
docker compose -f docker/docker-compose.yml up -d --build
```

---

## ✅ Checklist de Validação

- [ ] Docker Compose subiu sem erros
- [ ] 9 containers rodando (postgres, redis, minio, emqx, mailpit, api, worker, scheduler, nginx)
- [ ] Health checks todos em `healthy`
- [ ] Migrações executadas com sucesso
- [ ] Tenant "Uberlandia Medical Center" criado
- [ ] Domain "umc.localhost" criado
- [ ] Usuário owner criado
- [ ] `/health` retorna 200
- [ ] `/api/docs/` abre Swagger UI
- [ ] `/admin/` aceita login do owner
- [ ] MinIO Console acessível
- [ ] Mailpit UI acessível
- [ ] EMQX Dashboard acessível

---

## 📞 Próximos Passos

Após validar tudo:

1. ✅ **Fase 0 concluída**
2. 📋 Planejar **Fase 1** (Auth & Usuário)
3. 🔐 Implementar JWT em cookies HttpOnly
4. 👤 Criar endpoints de login/logout/refresh
5. 📸 Implementar upload de avatar

---

**Pronto para começar! 🚀**
