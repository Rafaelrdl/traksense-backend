# 🔧 GUIA DE DIAGNÓSTICO - ERRO 400/403 NO LOGIN

## ❌ Problema Identificado

Você está recebendo os seguintes erros ao tentar fazer login:
- **403 (rate limit exceeded)** - Servidor bloqueando por excesso de requisições
- **400 (Bad Request)** - Requisição malformada ou backend não disponível  
- **401 (Unauthorized)** - Tentativas sem token válido

## 🎯 Causa Raiz

O **loop infinito de requisições** que estava acontecendo causou **rate limiting** no servidor. Mesmo após corrigir o loop, o servidor pode estar temporariamente bloqueando seu IP.

## ✅ Correções Aplicadas

1. ✅ Carregamento condicional de assets (só se tiver token)
2. ✅ Proteção na função `loadAssetsFromApi()`
3. ✅ Flag `isRedirecting` para prevenir múltiplos redirects
4. ✅ Ignorar requisições canceladas no interceptor
5. ✅ Debounce + AbortController no useEffect da telemetria
6. ✅ Logs melhorados (não loga warning para /auth/login)

## 🚀 Passos para Resolver

### 1. Verificar se o Backend Está Rodando

Abra um **NOVO terminal PowerShell** e execute:

```powershell
cd "C:\Users\Rafael Ribeiro\TrakSense\traksense-backend"
python manage.py runserver umc.localhost:8000
```

**Resultado esperado:**
```
Django version 4.x.x, using settings 'config.settings'
Starting development server at http://umc.localhost:8000/
Quit the server with CTRL-BREAK.
```

### 2. Testar o Endpoint de Login Diretamente

Em outro terminal, execute:

```powershell
cd "C:\Users\Rafael Ribeiro\TrakSense"
python test_login_direct.py
```

**Resultado esperado se backend estiver OK:**
```
✅ Login bem-sucedido!
👤 Usuário: admin@umc.local
🔑 Access Token: eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

**Se der erro de conexão:**
```
❌ Erro de conexão!
   Backend não está rodando em http://umc.localhost:8000/api
```
👉 **Solução:** Inicie o backend (passo 1)

### 3. Limpar Rate Limiting (se necessário)

Se o rate limit persistir, você precisa:

**Opção A: Esperar** (5-15 minutos geralmente resolve)

**Opção B: Reiniciar o Backend**
```powershell
# No terminal do backend, pressione Ctrl+C
# Depois reinicie:
python manage.py runserver umc.localhost:8000
```

**Opção C: Limpar Cache do Navegador**
1. Abra DevTools (F12)
2. Clique com botão direito no ícone de recarregar
3. Selecione "Limpar cache e recarregar"
4. Execute no console:
   ```javascript
   localStorage.clear()
   ```

### 4. Testar Login no Frontend

1. **Recarregue a página** (Ctrl+Shift+R)
2. **Tente fazer login** com credenciais demo:
   - Email: `admin@umc.local`
   - Senha: `admin123`

### 5. Verificar Logs do Console

Após carregar a página, você deve ver:
```
⚠️ Sem token - pulando carregamento automático de assets
```

Após fazer login bem-sucedido:
```
✅ Token encontrado - carregando assets da API
```

## 🔍 Diagnóstico por Erro

### Se ver: "403 rate limit exceeded"
**Causa:** Muitas requisições falharam
**Solução:** Aguarde 5-15 minutos OU reinicie o backend

### Se ver: "400 Bad Request"
**Causa:** Backend não está rodando OU endpoint incorreto
**Solução:** Verifique se backend está em `http://umc.localhost:8000`

### Se ver: "401 Unauthorized" continuamente
**Causa:** Loop de requisições ainda acontecendo
**Solução:** 
1. Limpe localStorage: `localStorage.clear()`
2. Recarregue página (Ctrl+Shift+R)
3. Verifique se ainda vê requisições repetidas no Network

### Se ver: "Failed to load resource"
**Causa:** DNS não resolve `umc.localhost`
**Solução:** Verifique arquivo `hosts`:
```
C:\Windows\System32\drivers\etc\hosts
```
Deve conter:
```
127.0.0.1    umc.localhost
```

## 📊 Checklist de Verificação

- [ ] Backend está rodando (`python manage.py runserver`)
- [ ] Teste direto funciona (`python test_login_direct.py`)
- [ ] LocalStorage limpo (`localStorage.clear()`)
- [ ] Cache do navegador limpo (Ctrl+Shift+R)
- [ ] Arquivo hosts configurado corretamente
- [ ] Não há requisições em loop (verificar Network tab)
- [ ] Frontend compilado (`npm run build` sem erros)

## 🎯 Próximos Passos

1. **Execute o passo 1** primeiro (iniciar backend)
2. **Execute o passo 2** para testar (script de teste)
3. **Se funcionar**, execute o passo 4 (teste no frontend)
4. **Se não funcionar**, me envie a saída completa do script de teste

## 📞 Se Precisar de Ajuda

Me envie:
1. Screenshot do erro no DevTools
2. Saída do comando `python test_login_direct.py`
3. Confirmação se o backend está rodando
4. Logs do console do navegador após carregar a página
