# ✅ CHECKLIST DE VALIDAÇÃO DA INTEGRAÇÃO

## 📋 Status Atual

- ✅ Backend rodando: `http://umc.localhost:8000`
- ✅ Frontend rodando: `http://localhost:5000`
- ✅ Axios instalado
- ✅ Sem erros TypeScript
- ✅ API client criado
- ✅ Auth service criado
- ✅ Store integrada

---

## 🧪 Testes a Executar

### 1. ✅ Teste de Conectividade Backend

**Objetivo:** Verificar se o backend está acessível

**Comando:**
```powershell
Invoke-WebRequest -Uri "http://umc.localhost:8000/api/health/" -Headers @{"Host"="umc.localhost"}
```

**Resultado esperado:**
```json
{"status": "ok", "message": "API is running"}
```

---

### 2. 🔐 Teste de Login via API Direta

**Objetivo:** Verificar autenticação no backend

**Comando:**
```powershell
$body = @{
    email = "test@umc.com"
    password = "TestPass123!"
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://umc.localhost:8000/api/auth/login/" `
    -Method POST `
    -Headers @{"Host"="umc.localhost"; "Content-Type"="application/json"} `
    -Body $body
```

**Resultado esperado:**
- Status: 200 OK
- Body contém: `user`, `access`, `refresh`

---

### 3. 🌐 Teste de Login via Frontend

**Passos:**

1. **Abrir navegador:** http://localhost:5000

2. **Verificar página de login:**
   - [ ] Formulário de login visível
   - [ ] Campos de email e senha
   - [ ] Botão "Entrar"

3. **Tentar login com credenciais de teste:**
   ```
   Email: test@umc.com
   Password: TestPass123!
   ```

4. **Abrir DevTools (F12):**
   - Aba: **Console**
   - Verificar se não há erros JavaScript
   
   - Aba: **Network**
   - Filtrar por: `XHR`
   - Procurar requisição para: `http://umc.localhost:8000/api/auth/login/`
   
   - Aba: **Application** > **Local Storage**
   - Verificar chaves: `access_token`, `refresh_token`

5. **Resultados esperados:**
   - [ ] Requisição POST para `/api/auth/login/` foi feita
   - [ ] Status da resposta: **200 OK**
   - [ ] Tokens salvos no localStorage
   - [ ] Usuário redirecionado para dashboard
   - [ ] Nome do usuário aparece no header

---

### 4. 👤 Teste de Profile (GET)

**Passos:**

1. **Com usuário logado**, abrir DevTools

2. **No Console**, executar:
   ```javascript
   // Ver se o store tem o user
   console.log('User no store:', useAuthStore.getState().user);
   ```

3. **Ir para página de perfil** (se existir)
   - OU no Console:
   ```javascript
   // Fazer requisição manual
   fetch('http://umc.localhost:8000/api/users/me/', {
     headers: {
       'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
       'Host': 'umc.localhost'
     }
   })
   .then(r => r.json())
   .then(d => console.log('Profile:', d));
   ```

4. **Resultados esperados:**
   - [ ] Requisição GET para `/api/users/me/` retorna 200
   - [ ] Dados do usuário são recebidos
   - [ ] Informações aparecem na UI (se tiver página)

---

### 5. 🖼️ Teste de Avatar Upload (POST)

**Passos:**

1. **Criar arquivo de teste:**
   - Qualquer imagem JPG/PNG menor que 5MB

2. **No Console do navegador:**
   ```javascript
   // Selecionar arquivo via input (criar temporário)
   const input = document.createElement('input');
   input.type = 'file';
   input.accept = 'image/*';
   input.onchange = async (e) => {
     const file = e.target.files[0];
     const formData = new FormData();
     formData.append('avatar', file);
     
     const response = await fetch('http://umc.localhost:8000/api/users/me/avatar/', {
       method: 'POST',
       headers: {
         'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
         'Host': 'umc.localhost'
       },
       body: formData
     });
     
     const result = await response.json();
     console.log('Upload result:', result);
   };
   input.click();
   ```

3. **Resultados esperados:**
   - [ ] Requisição POST para `/api/users/me/avatar/` retorna 200
   - [ ] Resposta contém URL do MinIO
   - [ ] Avatar atualizado no perfil

---

### 6. 🔄 Teste de Token Refresh

**Objetivo:** Verificar refresh automático quando token expira

**Método 1: Reduzir tempo de expiração (requer alteração backend)**

**Método 2: Simular token expirado**

No Console:
```javascript
// Salvar token atual
const currentToken = localStorage.getItem('access_token');
console.log('Token atual:', currentToken);

// Substituir por token inválido
localStorage.setItem('access_token', 'token_invalido_para_teste');

// Fazer qualquer requisição autenticada
fetch('http://umc.localhost:8000/api/users/me/', {
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
    'Host': 'umc.localhost'
  }
})
.then(r => {
  console.log('Status:', r.status);
  return r.json();
})
.then(d => console.log('Data:', d))
.catch(e => console.error('Error:', e));

// Verificar na aba Network se houve:
// 1. Request inicial com 401
// 2. Request automático para /api/auth/token/refresh/
// 3. Retry da request original com novo token
```

**Resultados esperados:**
- [ ] Primeira requisição retorna 401
- [ ] Interceptor detecta 401
- [ ] Faz POST para `/api/auth/token/refresh/`
- [ ] Recebe novo access_token
- [ ] Retenta requisição original
- [ ] Requisição original retorna 200

---

### 7. 🚪 Teste de Logout

**Passos:**

1. **Com usuário logado**, clicar em **"Sair"** (ou botão de logout)

2. **No DevTools:**
   - Aba **Network**: verificar requisição POST `/api/auth/logout/`
   - Aba **Application** > **Local Storage**: verificar se tokens foram removidos

3. **Resultados esperados:**
   - [ ] Requisição POST para `/api/auth/logout/` foi feita
   - [ ] `access_token` removido do localStorage
   - [ ] `refresh_token` removido do localStorage
   - [ ] Usuário redirecionado para página de login
   - [ ] Tentar acessar página protegida redireciona para login

---

### 8. ❌ Teste de Erro Handling

**Cenário 1: Login com credenciais inválidas**

```
Email: wrong@email.com
Password: wrongpass
```

**Resultados esperados:**
- [ ] Requisição retorna 401 ou 400
- [ ] Mensagem de erro aparece na UI
- [ ] Não salva tokens
- [ ] Permanece na página de login

---

**Cenário 2: Requisição sem autenticação**

No Console:
```javascript
fetch('http://umc.localhost:8000/api/users/me/', {
  headers: {
    'Host': 'umc.localhost'
  }
})
.then(r => {
  console.log('Status:', r.status);
  return r.json();
})
.then(d => console.log('Response:', d));
```

**Resultados esperados:**
- [ ] Retorna 401 Unauthorized
- [ ] Mensagem de erro apropriada

---

**Cenário 3: Upload de arquivo muito grande**

Tentar upload de imagem > 5MB

**Resultados esperados:**
- [ ] Backend rejeita com 400
- [ ] Mensagem de erro aparece
- [ ] Avatar não é atualizado

---

## 🎯 Resumo de Validação

### Backend (já validado)
- [x] 7/7 testes automatizados passando
- [x] Endpoints funcionando
- [x] JWT configurado
- [x] MinIO integrado

### Frontend
- [x] Servidor rodando (http://localhost:5000)
- [x] Axios instalado
- [x] Sem erros TypeScript
- [ ] Login funcionando (aguardando teste manual)
- [ ] Profile carregando (aguardando teste manual)
- [ ] Avatar upload funcionando (aguardando teste manual)
- [ ] Token refresh automático (aguardando teste manual)
- [ ] Logout funcionando (aguardando teste manual)

---

## 🚀 Próximos Passos

1. **Executar todos os testes acima** ✅
2. **Criar ProfilePage** se ainda não existir
3. **Implementar UI de avatar upload**
4. **Adicionar página de registro** (opcional)
5. **Melhorar UX de loading/errors**

---

**Data:** 18/10/2025  
**Status:** Frontend rodando, aguardando validação manual
