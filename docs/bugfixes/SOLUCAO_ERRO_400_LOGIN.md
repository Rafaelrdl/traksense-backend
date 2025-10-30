# 🔧 SOLUÇÃO DO ERRO 400 - Bad Request

## 🎯 Problema Identificado

O erro **400 Bad Request** ao fazer login acontece porque:

### Causa Raiz: DNS não configurado

O domínio `umc.localhost` **não está configurado** no arquivo `hosts` do Windows, fazendo com que:

1. ❌ O navegador não consegue resolver `umc.localhost`
2. ❌ O backend Django **rejeita a requisição** porque o `Host` header não bate com nenhum tenant configurado
3. ❌ Retorna 400 Bad Request

---

## ✅ SOLUÇÃO 1: Adicionar umc.localhost ao arquivo hosts (RECOMENDADO)

### Passo 1: Abrir Notepad como Administrador

1. Clique no **Menu Iniciar**
2. Digite: `notepad`
3. **Clique com botão direito** em "Notepad"
4. Selecione: **"Executar como administrador"**

### Passo 2: Abrir o arquivo hosts

1. No Notepad, vá em: **Arquivo** → **Abrir**
2. Navegue até: `C:\Windows\System32\drivers\etc\`
3. No campo "Tipo de arquivo", selecione: **"Todos os Arquivos (*.*)"**
4. Selecione o arquivo: **`hosts`**
5. Clique em **Abrir**

### Passo 3: Adicionar a entrada

No **final do arquivo**, adicione a seguinte linha:

```
127.0.0.1 umc.localhost
```

### Passo 4: Salvar e fechar

1. Vá em: **Arquivo** → **Salvar**
2. Feche o Notepad

### Passo 5: Verificar

Abra um **novo terminal PowerShell** e execute:

```powershell
ping umc.localhost
```

**Resultado esperado:**
```
Disparando umc.localhost [127.0.0.1] com 32 bytes de dados:
Resposta de 127.0.0.1: bytes=32 tempo<1ms TTL=128
```

### Passo 6: Testar o login

1. **Recarregue a página** do frontend (F5)
2. Tente fazer login novamente com:
   - Email: `test@umc.com`
   - Senha: `TestPass123!`

✅ **Deve funcionar perfeitamente!**

---

## ✅ SOLUÇÃO 2: Usar 127.0.0.1 diretamente (Alternativa temporária)

Se não puder editar o arquivo hosts, modifique o `.env` do frontend:

### Opção A: Usar IP + Header customizado

**Arquivo:** `.env`

```env
VITE_API_URL=http://127.0.0.1:8000/api
VITE_API_HOST_HEADER=umc.localhost
```

Depois, atualizar `src/lib/api.ts` para adicionar o header `Host`:

```typescript
// Adicionar interceptor de request
api.interceptors.request.use((config) => {
  const hostHeader = import.meta.env.VITE_API_HOST_HEADER;
  
  if (hostHeader) {
    config.headers['Host'] = hostHeader;
  }
  
  // ... resto do código
  return config;
});
```

### Opção B: Desabilitar multi-tenant temporariamente

**NÃO RECOMENDADO** - Requer alterações no backend.

---

## 🧪 Como Testar se Está Funcionando

### Teste 1: Verificar hosts file

```powershell
Get-Content C:\Windows\System32\drivers\etc\hosts | Select-String "umc.localhost"
```

**Esperado:**
```
127.0.0.1 umc.localhost
```

### Teste 2: Ping

```powershell
ping umc.localhost
```

**Esperado:**
```
Resposta de 127.0.0.1
```

### Teste 3: Teste HTTP direto

```powershell
$body = @{
    username_or_email = "test@umc.com"
    password = "TestPass123!"
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://umc.localhost:8000/api/auth/login/" `
    -Method POST `
    -Headers @{
        "Host" = "umc.localhost"
        "Content-Type" = "application/json"
    } `
    -Body $body
```

**Esperado:**
```
StatusCode        : 200
StatusDescription : OK
Content           : {"user":{...},"access":"...","refresh":"..."}
```

### Teste 4: Login no frontend

1. Abrir: http://localhost:5000/login
2. Preencher:
   - Email: `test@umc.com`
   - Password: `TestPass123!`
3. Clicar em **Entrar**

**Esperado:**
- ✅ Sem erros no console
- ✅ Redirecionamento para dashboard
- ✅ Nome do usuário aparece no header

---

## 📊 Diagnóstico Completo

### Checklist de Verificação

- [ ] **Backend rodando:** `docker ps | Select-String traksense-api`
- [ ] **umc.localhost no hosts:** `Get-Content C:\Windows\System32\drivers\etc\hosts | Select-String "umc.localhost"`
- [ ] **DNS resolvendo:** `ping umc.localhost`
- [ ] **Frontend rodando:** Acessar http://localhost:5000
- [ ] **API acessível:** Testar http://umc.localhost:8000/api/health/
- [ ] **Login funciona:** Testar com test@umc.com

### Erros Comuns

| Erro | Causa | Solução |
|------|-------|---------|
| **400 Bad Request** | DNS não configurado | Adicionar ao hosts file |
| **O nome remoto não pôde ser resolvido** | DNS não configurado | Adicionar ao hosts file |
| **CORS Error** | CORS não habilitado | Verificar `CORS_ALLOWED_ORIGINS` no backend |
| **401 Unauthorized** | Credenciais inválidas | Verificar email e senha |
| **Network Error** | Backend não rodando | `docker-compose up -d` |

---

## 🎉 Após Aplicar a Solução

Depois de adicionar `127.0.0.1 umc.localhost` ao arquivo hosts:

1. ✅ Frontend pode acessar `http://umc.localhost:8000`
2. ✅ Django reconhece o tenant `umc`
3. ✅ Login funciona perfeitamente
4. ✅ Todas as APIs respondem corretamente

---

## 🔍 Por Que Aconteceu?

### Multi-Tenancy do Django-Tenants

O backend usa **django-tenants** que:

1. Identifica o tenant pelo **hostname** na requisição
2. Espera um `Host` header válido (ex: `umc.localhost`)
3. Rejeita requisições com hostname desconhecido

### Fluxo Normal

```
Frontend (localhost:5000)
    │
    ├─> Requisição: http://umc.localhost:8000/api/auth/login/
    │   Header: Host: umc.localhost
    │
    ├─> DNS resolve: umc.localhost → 127.0.0.1
    │
    ├─> Nginx recebe em 127.0.0.1:8000
    │
    ├─> Django lê Host header: "umc.localhost"
    │
    ├─> Django-tenants identifica tenant: "umc"
    │
    └─> ✅ Resposta 200 OK
```

### Fluxo com DNS não configurado

```
Frontend (localhost:5000)
    │
    ├─> Requisição: http://umc.localhost:8000/api/auth/login/
    │
    ├─> ❌ DNS não resolve: umc.localhost
    │
    └─> ❌ Erro: "O nome remoto não pôde ser resolvido"
```

---

## 📝 Resumo Executivo

### 🎯 Problema
Erro 400 ao fazer login porque `umc.localhost` não está configurado no DNS local.

### ✅ Solução
Adicionar `127.0.0.1 umc.localhost` ao arquivo `C:\Windows\System32\drivers\etc\hosts` como administrador.

### 🧪 Validação
```powershell
ping umc.localhost  # Deve responder de 127.0.0.1
```

### 🚀 Resultado
Login funcionando perfeitamente! ✨

---

**Arquivo:** `SOLUCAO_ERRO_400_LOGIN.md`  
**Data:** 18/10/2025  
**Status:** Problema identificado, solução documentada
