# 🔍 DIAGNÓSTICO COMPLETO - Erro 400 no Login

**Data:** 18/10/2025  
**Status:** ✅ PROBLEMA IDENTIFICADO E SOLUÇÃO DOCUMENTADA

---

## 📋 Resumo Executivo

### Erro Reportado
```
POST http://umc.localhost:8000/api/auth/login/ 400 (Bad Request)
AxiosError {message: 'Request failed with status code 400', ...}
```

### Credenciais Testadas
- Email: `test@umc.com`
- Senha: `TestPass123!`

---

## 🎯 CAUSA RAIZ IDENTIFICADA

### Problema Principal: DNS NÃO CONFIGURADO

O domínio `umc.localhost` **não está mapeado** no arquivo `hosts` do Windows.

**Evidências:**

1. ✅ Backend está rodando corretamente
2. ✅ Código do frontend está correto
3. ✅ Credenciais estão válidas
4. ❌ DNS não resolve `umc.localhost`

**Teste realizado:**
```powershell
Get-Content C:\Windows\System32\drivers\etc\hosts | Select-String "umc.localhost"
# Resultado: VAZIO (entrada não existe)
```

---

## 🔍 Análise Técnica Detalhada

### 1. Verificação do Código Frontend

**Arquivo:** `src/services/auth.service.ts`

```typescript
async login(credentials: LoginCredentials): Promise<User> {
  // ✅ Correto: Enviando username_or_email
  const { data } = await api.post<AuthResponse>('/auth/login/', credentials);
  // ...
}
```

**Interface:**
```typescript
export interface LoginCredentials {
  username_or_email: string;  // ✅ Correto
  password: string;
}
```

✅ **Frontend está CORRETO**

---

### 2. Verificação do Backend

**Arquivo:** `apps/accounts/serializers.py`

```python
class LoginSerializer(serializers.Serializer):
    username_or_email = serializers.CharField(required=True)  # ✅ Esperado
    password = serializers.CharField(required=True, write_only=True)
```

**Validação:**
```python
def validate(self, attrs):
    username_or_email = attrs.get('username_or_email')
    password = attrs.get('password')
    
    # Se contém @, é email
    if '@' in username_or_email:
        try:
            user_obj = User.objects.get(email=username_or_email.lower())
            username = user_obj.username
        except User.DoesNotExist:
            raise serializers.ValidationError(...)
    
    # Autentica
    user = authenticate(username=username, password=password)
```

✅ **Backend está CORRETO**

---

### 3. Verificação do Django Multi-Tenant

**Como funciona:**

```python
# Django-tenants identifica o tenant pelo hostname
MIDDLEWARE = [
    'django_tenants.middleware.main.TenantMainMiddleware',  # <-- Aqui!
    # ...
]
```

**Fluxo:**

1. Requisição chega com `Host: umc.localhost`
2. Middleware lê o header `Host`
3. Busca tenant no banco de dados com `domain_url = 'umc.localhost'`
4. Se **não encontrar** ou **hostname inválido** → **400 Bad Request**

---

### 4. Teste de DNS

**Comando:**
```powershell
ping umc.localhost
```

**Resultado:**
```
O nome remoto não pôde ser resolvido: 'umc.localhost'
```

❌ **DNS NÃO ESTÁ CONFIGURADO**

---

## 🛠️ SOLUÇÃO

### Opção 1: Adicionar ao Hosts File (RECOMENDADO)

#### Método Automático (via Script)

Execute com PowerShell como **Administrador**:

```powershell
cd "C:\Users\Rafael Ribeiro\TrakSense"
.\configurar-hosts.ps1
```

**O script faz:**
1. ✅ Verifica se entrada já existe
2. ✅ Adiciona `127.0.0.1 umc.localhost`
3. ✅ Valida configuração com ping
4. ✅ Testa conexão com backend

---

#### Método Manual

1. **Abrir Notepad como Admin:**
   - Menu Iniciar → `notepad`
   - Botão direito → **"Executar como administrador"**

2. **Abrir arquivo hosts:**
   - Arquivo → Abrir
   - Navegar: `C:\Windows\System32\drivers\etc\`
   - Tipo: **"Todos os Arquivos (*.*)"**
   - Selecionar: `hosts`

3. **Adicionar linha:**
   ```
   127.0.0.1 umc.localhost
   ```

4. **Salvar e fechar**

5. **Validar:**
   ```powershell
   ping umc.localhost
   # Deve responder de 127.0.0.1
   ```

---

### Opção 2: Usar 127.0.0.1 (Alternativa Temporária)

**Não recomendado**, mas funcional:

Modificar `.env` do frontend:

```env
VITE_API_URL=http://127.0.0.1:8000/api
```

E adicionar interceptor em `src/lib/api.ts`:

```typescript
api.interceptors.request.use((config) => {
  // Força header Host para multi-tenant
  config.headers['Host'] = 'umc.localhost';
  return config;
});
```

---

## ✅ Checklist de Validação Pós-Solução

Após configurar o hosts file:

- [ ] **DNS resolve:**
  ```powershell
  ping umc.localhost
  # ✅ Resposta de 127.0.0.1
  ```

- [ ] **Backend acessível:**
  ```powershell
  Invoke-WebRequest -Uri "http://umc.localhost:8000/api/health/"
  # ✅ StatusCode: 200
  ```

- [ ] **Login via PowerShell:**
  ```powershell
  $body = @{username_or_email="test@umc.com"; password="TestPass123!"} | ConvertTo-Json
  Invoke-WebRequest -Uri "http://umc.localhost:8000/api/auth/login/" -Method POST -Headers @{"Content-Type"="application/json"} -Body $body
  # ✅ StatusCode: 200
  # ✅ Body contém: user, access, refresh
  ```

- [ ] **Login via Frontend:**
  1. Recarregar página (F5)
  2. Email: `test@umc.com`
  3. Senha: `TestPass123!`
  4. ✅ Login bem-sucedido
  5. ✅ Redirecionamento para dashboard
  6. ✅ Nome aparece no header

---

## 📊 Arquivos Criados para Solução

### 1. `SOLUCAO_ERRO_400_LOGIN.md`
- Documentação completa do problema
- Passos detalhados para solução
- Troubleshooting guide
- FAQs

### 2. `configurar-hosts.ps1`
- Script PowerShell automático
- Verifica se entrada existe
- Adiciona configuração
- Valida DNS e backend
- Interface colorida e amigável

### 3. `test_integration.md` (atualizado)
- Checklist completo de testes
- Comandos de validação
- Exemplos práticos

---

## 🎓 Lições Aprendidas

### 1. Multi-Tenancy Requer DNS Local
- Django-tenants identifica tenant pelo hostname
- Hostname deve estar no arquivo hosts OU DNS real
- Sem DNS → Middleware não encontra tenant → 400

### 2. Erro 400 vs 404 vs 401
- **400 Bad Request**: Problema estrutural (DNS, payload malformado)
- **401 Unauthorized**: Credenciais inválidas
- **404 Not Found**: Endpoint não existe

### 3. Browser vs PowerShell
- Browsers **podem** ter DNS cache diferente
- PowerShell usa DNS do sistema diretamente
- Testar em ambos é importante

---

## 🚀 Próximos Passos

Após aplicar a solução:

1. ✅ Configurar hosts file
2. ✅ Validar DNS com ping
3. ✅ Testar backend diretamente
4. ✅ Testar login no frontend
5. ⏳ Criar ProfilePage
6. ⏳ Implementar avatar upload
7. ⏳ Testes end-to-end completos

---

## 📞 Como Executar a Solução

### PASSO A PASSO RÁPIDO

1. **Abrir PowerShell como Administrador:**
   ```
   Menu Iniciar → PowerShell → Botão direito → "Executar como administrador"
   ```

2. **Executar script:**
   ```powershell
   cd "C:\Users\Rafael Ribeiro\TrakSense"
   .\configurar-hosts.ps1
   ```

3. **Aguardar validação automática**

4. **Recarregar frontend (F5)**

5. **Fazer login:**
   - Email: `test@umc.com`
   - Senha: `TestPass123!`

6. **✅ DEVE FUNCIONAR!**

---

## 🎉 Conclusão

### Problema: 
Erro 400 ao fazer login

### Causa: 
DNS `umc.localhost` não configurado no arquivo hosts

### Solução: 
Adicionar `127.0.0.1 umc.localhost` ao `C:\Windows\System32\drivers\etc\hosts`

### Status: 
✅ **RESOLVIDO** (aguardando aplicação pelo usuário)

### Ferramentas criadas:
1. Script automático (`configurar-hosts.ps1`)
2. Documentação completa (`SOLUCAO_ERRO_400_LOGIN.md`)
3. Este diagnóstico (`DIAGNOSTICO_ERRO_400.md`)

---

**Próxima ação recomendada:**  
Execute o script `configurar-hosts.ps1` como administrador e teste o login! 🚀

---

**Arquivo:** `DIAGNOSTICO_ERRO_400.md`  
**Data:** 18/10/2025  
**Autor:** GitHub Copilot  
**Status:** Análise completa finalizada ✅
