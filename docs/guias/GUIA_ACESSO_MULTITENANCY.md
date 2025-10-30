# 🌐 Guia de Acesso - Multi-Tenancy

**Data:** 19/10/2025 23:55  
**Status:** 📘 DOCUMENTAÇÃO  

---

## 🎯 URL Correta de Acesso

### ✅ Acesso CORRETO

```
http://umc.localhost:5000
```

**Exemplos de páginas:**
- Dashboard: `http://umc.localhost:5000/`
- Ativos: `http://umc.localhost:5000/assets`
- Sensores: `http://umc.localhost:5000/sensors`
- Relatórios: `http://umc.localhost:5000/reports`

---

### ❌ Acesso INCORRETO

```
http://localhost:5000
```

**O que acontece:**
- ✅ Página carrega visualmente
- ❌ Todas as chamadas de API retornam **404 Not Found**
- ❌ Dados não aparecem (só mockados)
- ❌ Console mostra erros de rede

---

## 🔍 Por Que Precisa do Domínio?

### Arquitetura Multi-Tenant

O TrakSense usa **django-tenants** para isolamento de dados por cliente:

```
┌─────────────────────────────────────────┐
│  PostgreSQL Database                    │
├─────────────────────────────────────────┤
│  Schema: public                         │
│    - Tenants (umc, hospital, etc)       │
│    - Admin centralizado                 │
├─────────────────────────────────────────┤
│  Schema: umc                            │
│    - Assets (ativos da UMC)             │
│    - Sensors (sensores da UMC)          │
│    - Readings (leituras da UMC)         │
├─────────────────────────────────────────┤
│  Schema: hospital                       │
│    - Assets (ativos do Hospital)        │
│    - Sensors (sensores do Hospital)     │
│    - Readings (leituras do Hospital)    │
└─────────────────────────────────────────┘
```

### Como Funciona

1. **Requisição chega ao backend:**
   ```
   GET http://umc.localhost:8000/api/assets/
   ```

2. **Django-Tenants identifica tenant:**
   ```python
   # Middleware extrai domínio da requisição
   hostname = "umc.localhost"
   tenant = Tenant.objects.get(domain_url="umc.localhost")
   # Define schema da conexão
   connection.set_schema(tenant.schema_name)  # "umc"
   ```

3. **Query usa schema correto:**
   ```sql
   SELECT * FROM umc.assets;  -- ✅ Dados da UMC
   -- NÃO: SELECT * FROM public.assets;  -- ❌ Schema errado
   ```

4. **Response retorna dados isolados**

---

## 🛠️ Configuração Atual

### Backend (.env)

```bash
# Domínios permitidos
ALLOWED_HOSTS=localhost,umc.localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://umc.localhost:5000,http://localhost:5000

# Tenant criado
TENANT_DOMAIN=umc.localhost
```

### Frontend (.env)

```bash
# API URL com domínio do tenant
VITE_API_URL=http://umc.localhost:8000/api
```

### URL Routing

| Domínio | Schema | URLConf | Endpoints |
|---------|--------|---------|-----------|
| `localhost:8000` | `public` | `config.urls_public.py` | `/admin`, `/ops`, `/health`, `/ingest` |
| `umc.localhost:8000` | `umc` | `config.urls.py` | `/api/auth`, `/api/assets`, `/api/telemetry` |

---

## 🧪 Teste de Conectividade

### 1. Verificar Tenant (Backend)

```bash
# PowerShell
Invoke-RestMethod -Uri "http://localhost:8000/health" -Method GET

# Esperado: {"status": "healthy"}
```

### 2. Verificar API Tenant

```bash
# PowerShell (vai dar 401 sem auth, mas é OK - significa que rota existe)
Invoke-RestMethod -Uri "http://umc.localhost:8000/api/assets/" -Method GET

# Esperado: 401 Unauthorized (rota existe)
# NÃO esperado: 404 Not Found (rota não existe)
```

### 3. Verificar Frontend

1. Abrir DevTools (F12)
2. Acessar: `http://umc.localhost:5000/sensors`
3. Aba Network → Filtrar por "summary"
4. Verificar requisição:
   ```
   Request URL: http://umc.localhost:8000/api/telemetry/device/GW-1760908415/summary/
   Status Code: 200 OK
   ```

---

## 🚨 Troubleshooting

### Problema: "Page not found (404)"

**Sintomas:**
- Console mostra: `404 Client Error: Not Found for url: http://localhost:8000/api/telemetry/...`
- Dados não carregam
- Só aparecem dados mockados

**Causa:**
Acessando `localhost` sem tenant domain

**Solução:**
Acesse via `http://umc.localhost:5000`

---

### Problema: "DNS_PROBE_FINISHED_NXDOMAIN"

**Sintomas:**
- Navegador não resolve `umc.localhost`
- Erro de DNS

**Causa:**
Hosts file não configurado

**Solução (Windows):**
1. Abrir PowerShell como Administrador
2. Editar hosts:
   ```powershell
   notepad C:\Windows\System32\drivers\etc\hosts
   ```
3. Adicionar linha:
   ```
   127.0.0.1 umc.localhost
   ```
4. Salvar e fechar
5. Flush DNS:
   ```powershell
   ipconfig /flushdns
   ```

**Solução (Linux/Mac):**
```bash
sudo nano /etc/hosts
# Adicionar:
127.0.0.1 umc.localhost

# Flush DNS (Mac):
sudo dscacheutil -flushcache
```

---

### Problema: "Mixed Content" (HTTP/HTTPS)

**Sintomas:**
- Alguns recursos bloqueados
- Avisos de segurança

**Causa:**
Frontend em HTTPS tentando acessar API HTTP

**Solução:**
Use HTTP para ambos (desenvolvimento):
- Frontend: `http://umc.localhost:5000`
- Backend: `http://umc.localhost:8000`

---

## 📋 Checklist de Validação

Antes de reportar bugs, verifique:

- [ ] Acessando via `http://umc.localhost:5000` (não `localhost`)
- [ ] Hosts file configurado (`127.0.0.1 umc.localhost`)
- [ ] Backend rodando (`docker ps` mostra `traksense-api`)
- [ ] Frontend rodando (processo Node na porta 5000)
- [ ] DevTools → Network mostra 200 OK (não 404)
- [ ] Console sem erros de CORS ou autenticação

---

## 🎓 Referências

### Documentação Oficial

- **Django-Tenants:** https://django-tenants.readthedocs.io/
- **Multi-Tenancy Patterns:** https://www.postgresql.org/docs/current/ddl-schemas.html

### Arquivos de Configuração

- Backend URLs (Public): `config/urls_public.py`
- Backend URLs (Tenant): `config/urls.py`
- Frontend API Client: `src/lib/api.ts`
- Tenant Middleware: Automático (django-tenants)

---

**Criado:** 19/10/2025 23:55  
**Atualizado:** 19/10/2025 23:55  
**Responsável:** GitHub Copilot
