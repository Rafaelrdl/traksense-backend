# 🚀 Acesso Rápido aos Serviços - TrakSense

## 🌐 URLs dos Serviços

### API Backend (Django)
- **URL**: http://localhost:8000
- **Health Check**: http://localhost:8000/health
- **Admin Django**: http://localhost:8000/admin (após criar superuser)

### EMQX Dashboard
- **URL**: http://localhost:18083
- **Usuário**: `admin`
- **Senha**: `public`
- ⚠️ **IMPORTANTE**: Alterar senha em produção!

### PostgreSQL/TimescaleDB
- **Host**: `localhost`
- **Porta**: `5432`
- **Database**: `traksense`
- **Usuário**: `postgres`
- **Senha**: `postgres`

**Cliente GUI recomendado**: [pgAdmin](https://www.pgadmin.org/) ou [DBeaver](https://dbeaver.io/)

**String de conexão**:
```
postgresql://postgres:postgres@localhost:5432/traksense
```

### Redis
- **Host**: `localhost`
- **Porta**: `6379`
- **Sem senha** (dev)

**Cliente GUI recomendado**: [Redis Insight](https://redis.com/redis-enterprise/redis-insight/)

---

## 🔧 Comandos Úteis (PowerShell)

### Gerenciamento de Serviços
```powershell
# Subir todos os serviços
.\manage.ps1 up

# Ver logs em tempo real
.\manage.ps1 logs

# Status dos containers
.\manage.ps1 ps

# Derrubar serviços
.\manage.ps1 down

# Testar health check
.\manage.ps1 health
```

### Acesso aos Containers
```powershell
# Django shell (Python interativo)
.\manage.ps1 shell

# Bash no container da API
.\manage.ps1 bash

# PostgreSQL CLI
docker compose -f infra/docker-compose.yml exec db psql -U postgres -d traksense

# Redis CLI
docker compose -f infra/docker-compose.yml exec redis redis-cli
```

### Migrações Django
```powershell
# Executar migrações
.\manage.ps1 migrate

# Criar nova migração
docker compose -f infra/docker-compose.yml exec api python manage.py makemigrations

# Ver status das migrações
docker compose -f infra/docker-compose.yml exec api python manage.py showmigrations
```

### Criar Superusuário Django
```powershell
docker compose -f infra/docker-compose.yml exec api python manage.py createsuperuser
```

---

## 📊 Monitoramento

### Ver logs de um serviço específico
```powershell
# API
docker compose -f infra/docker-compose.yml logs api -f

# Ingest
docker compose -f infra/docker-compose.yml logs ingest -f

# EMQX
docker compose -f infra/docker-compose.yml logs emqx -f

# PostgreSQL
docker compose -f infra/docker-compose.yml logs db -f
```

### Verificar recursos dos containers
```powershell
# Uso de CPU/Memória
docker stats

# Apenas containers do TrakSense
docker stats api db emqx redis
```

---

## 🧪 Testes Rápidos

### Health Check da API
```powershell
# PowerShell
Invoke-WebRequest http://localhost:8000/health

# Navegador
# Abra: http://localhost:8000/health
```

### Teste MQTT (com mosquitto_pub - opcional)
```bash
# Publicar mensagem de teste
mosquitto_pub -h localhost -p 1883 -t "traksense/test/site1/dev1/telem" -m '{"temp":25.5}'
```

### Consulta SQL no PostgreSQL
```powershell
docker compose -f infra/docker-compose.yml exec db psql -U postgres -d traksense -c "
SELECT schemaname, tablename 
FROM pg_tables 
WHERE schemaname = 'public' 
ORDER BY tablename;
"
```

### Teste Redis
```powershell
docker compose -f infra/docker-compose.yml exec redis redis-cli << 'EOF'
PING
SET test:key "Hello TrakSense"
GET test:key
DEL test:key
EOF
```

---

## 🔍 Troubleshooting Rápido

### API não responde
```powershell
# Verificar logs
docker compose -f infra/docker-compose.yml logs api --tail=50

# Reiniciar API
docker compose -f infra/docker-compose.yml restart api
```

### Banco de dados não conecta
```powershell
# Verificar se PostgreSQL está rodando
docker compose -f infra/docker-compose.yml ps db

# Tentar conexão manual
docker compose -f infra/docker-compose.yml exec db psql -U postgres -d traksense
```

### EMQX não conecta
```powershell
# Verificar logs EMQX
docker compose -f infra/docker-compose.yml logs emqx --tail=50

# Verificar se porta está aberta
Test-NetConnection -ComputerName localhost -Port 1883
Test-NetConnection -ComputerName localhost -Port 18083
```

### Rebuild completo (limpar tudo)
```powershell
# Parar e remover tudo
docker compose -f infra/docker-compose.yml down -v

# Rebuild e iniciar
docker compose -f infra/docker-compose.yml up -d --build

# Aguardar inicialização (30-60s)
Start-Sleep -Seconds 45

# Testar health
.\manage.ps1 health
```

---

## 📱 Acesso Remoto (Dev/Teste)

Se precisar acessar de outra máquina na mesma rede:

1. **Descubra seu IP local**:
   ```powershell
   ipconfig | Select-String "IPv4"
   ```

2. **Acesse usando o IP**:
   - API: `http://<SEU_IP>:8000/health`
   - EMQX: `http://<SEU_IP>:18083`
   - MQTT: `mqtt://<SEU_IP>:1883`

3. **Firewall**: Pode ser necessário liberar as portas:
   ```powershell
   # Executar como Administrador
   New-NetFirewallRule -DisplayName "TrakSense API" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow
   New-NetFirewallRule -DisplayName "TrakSense EMQX" -Direction Inbound -LocalPort 18083 -Protocol TCP -Action Allow
   New-NetFirewallRule -DisplayName "TrakSense MQTT" -Direction Inbound -LocalPort 1883 -Protocol TCP -Action Allow
   ```

---

## 🎯 Próximos Passos (Desenvolvimento)

### 1. Criar Superusuário Django
```powershell
docker compose -f infra/docker-compose.yml exec api python manage.py createsuperuser
```

### 2. Acessar Admin Django
- URL: http://localhost:8000/admin
- Use as credenciais criadas acima

### 3. Explorar EMQX Dashboard
- URL: http://localhost:18083
- Navegar por: Overview → Clients → Topics → Subscriptions

### 4. Conectar DBeaver ao PostgreSQL
1. Criar nova conexão PostgreSQL
2. Host: `localhost`, Port: `5432`
3. Database: `traksense`
4. Username: `postgres`, Password: `postgres`

---

## 📚 Referências Rápidas

- [Django Admin](http://localhost:8000/admin)
- [EMQX Dashboard](http://localhost:18083)
- [Django REST Framework Docs](https://www.django-rest-framework.org/)
- [EMQX Documentation](https://www.emqx.io/docs/en/latest/)
- [TimescaleDB Docs](https://docs.timescale.com/)

---

**Última atualização**: 7 de outubro de 2025  
**Status**: ✅ Todos os serviços operacionais
