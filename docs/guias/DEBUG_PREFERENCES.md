# Debug - Preferências não Salvando

**Data:** 2025-10-18  
**Problema:** Ao salvar preferências (idioma/timezone), as alterações não persistem

---

## 🔍 Diagnóstico Realizado

### 1. Estrutura das Respostas do Backend

**GET /api/users/me/**
```json
{
  "id": 1,
  "username": "testuser",
  "email": "test@umc.com",
  "language": "pt-br",
  "timezone": "America/Sao_Paulo",
  ...
}
```
✅ Retorna usuário diretamente

**PATCH /api/users/me/**
```json
{
  "user": {
    "id": 1,
    "username": "testuser",
    "email": "test@umc.com",
    "language": "en",
    "timezone": "America/New_York",
    ...
  },
  "message": "Perfil atualizado com sucesso!"
}
```
✅ Retorna objeto com `user` e `message`

### 2. Código Verificado

**✅ authService.updateProfile** - Correto
- Espera `data.user` (linha 188)
- Retorna `mapBackendUserToUser(data.user)`

**✅ authStore.updateUserProfile** - Correto
- Remove campos legacy antes de enviar
- Atualiza store com usuário retornado

**✅ PreferencesDialog.handleSave** - Correto
- Chama `updateUserProfile` com language e timezone
- Exibe toast de sucesso/erro

---

## 🛠️ Correções Aplicadas

### 1. Adicionados Logs de Debug

**authService.updateProfile:**
```typescript
console.log('updateProfile response:', data);
console.error('Response data:', error.response?.data);
```

**authStore.updateUserProfile:**
```typescript
console.log('🔄 Store: Atualizando perfil com:', updates);
console.log('📤 Store: Enviando para backend:', backendUpdates);
console.log('✅ Store: Usuário atualizado:', updatedUser);
console.error('❌ Store: Erro ao atualizar:', error);
```

**PreferencesDialog.handleSave:**
```typescript
console.log('🔄 Salvando preferências:', regionalization);
console.log('✅ Preferências salvas com sucesso!');
console.error('❌ Erro ao salvar preferências:', error);
```

---

## 🧪 Como Testar

### 1. Abrir DevTools
- Pressione **F12** no navegador
- Vá para aba **Console**
- **IMPORTANTE:** Limpe o console (botão 🚫 ou Ctrl+L)

### 2. Fazer Login
- Acesse http://localhost:5000/
- Login: test@umc.com / TestPass123!

### 3. Verificar localStorage ANTES
- No Console, digite:
```javascript
JSON.parse(localStorage.getItem('ts:auth'))
```
- Anote os valores de `language` e `timezone`

### 4. Abrir Preferências
- Clique no avatar no canto superior direito
- Clique em "Preferências"
- Vá para aba "Regionalização"
- **Observe os logs do useEffect:**
```
🔄 useEffect: Dialog abriu ou user mudou
📊 useEffect: open = true
👤 useEffect: user = {id: '...', language: 'pt-br', timezone: 'America/Sao_Paulo', ...}
🔄 useEffect: Sincronizando regionalization com user
🌍 useEffect: user.language = pt-br
⏰ useEffect: user.timezone = America/Sao_Paulo
✅ useEffect: Regionalization setado para: {language: 'pt-br', timezone: 'America/Sao_Paulo'}
```

### 5. Alterar Configurações
- Selecione idioma: **🇪🇸 Español**
- Selecione timezone: **Los Angeles (GMT-8)**

### 6. Clicar em "Salvar Preferências"

### 7. Observar Console (SEQUÊNCIA COMPLETA)
Você deve ver TODOS estes logs na ordem:
```
🔄 Salvando preferências: {language: 'es', timezone: 'America/Los_Angeles'}
🔄 Store: Atualizando perfil com: {language: 'es', timezone: 'America/Los_Angeles'}
📤 Store: Enviando para backend: {language: 'es', timezone: 'America/Los_Angeles'}
updateProfile response: {user: {...}, message: '...'}
✅ Store: Usuário atualizado: {id: '...', language: 'es', timezone: 'America/Los_Angeles', ...}
💾 Store: Salvando no state...
💾 Store: State atualizado!
🔍 Store: Verificando localStorage...
💾 localStorage ts:auth = {"state":{"user":{...},"isAuthenticated":true},"version":0}
👤 localStorage user.language = es
⏰ localStorage user.timezone = America/Los_Angeles
✅ Preferências salvas com sucesso!
```

### 8. Verificar localStorage DEPOIS
- No Console, digite novamente:
```javascript
JSON.parse(localStorage.getItem('ts:auth'))
```
- **✅ DEVE mostrar:** `language: 'es'` e `timezone: 'America/Los_Angeles'`

### 9. Fechar e Reabrir Dialog
- Clique em "Cancelar" para fechar
- Abra "Preferências" novamente
- **Observe os logs do useEffect novamente**
- **✅ DEVE mostrar:** `user.language = es` e `user.timezone = America/Los_Angeles`
- **✅ DEVE manter:** Español e Los Angeles selecionados

### 10. Recarregar Página (F5)
- Pressione **F5**
- **NÃO** precisa fazer login (token persiste)
- Abra "Preferências" → "Regionalização"
- **✅ Verificar:** Valores ainda estão "Español" e "Los Angeles"

---

## 🐛 Possíveis Causas do Problema

### Causa 1: localStorage NÃO Está Salvando
**Sintoma:** 
- Logs mostram `✅ Store: Usuário atualizado` 
- MAS `💾 localStorage user.language` está `undefined` ou com valor antigo

**Problema:** O `persist` middleware do Zustand não está funcionando

**Solução:**
```typescript
// Verificar em src/store/auth.ts se partialize está correto:
partialize: (state) => ({ 
  user: state.user,  // ← DEVE incluir user completo
  isAuthenticated: state.isAuthenticated 
})
```

### Causa 2: useEffect Está Sobrescrevendo com Valor Antigo
**Sintoma:**
- Na primeira abertura: valores corretos
- Ao fechar e reabrir: useEffect mostra `user.language = pt-br` (antigo)

**Problema:** O objeto `user` no store está com valor antigo

**Solução:** Verificar se `set({ user: updatedUser })` está realmente atualizando

### Causa 3: Backend Não Está Salvando
**Sintoma:** 
- Request retorna 200 OK
- Response mostra valores novos
- MAS ao recarregar página (F5), voltam os valores antigos

**Como verificar:**
```bash
docker exec -it traksense-api python manage.py shell
```
```python
from apps.accounts.models import User
user = User.objects.get(email='test@umc.com')
print(f"Language: {user.language}")
print(f"Timezone: {user.timezone}")
```

### Causa 4: Token JWT Expirado
**Sintoma:** Erro 401 Unauthorized no console

**Solução:** Fazer logout e login novamente

---

## 📝 Checklist de Validação

### Durante o Save:
- [ ] Console mostra "🔄 Salvando preferências"
- [ ] Console mostra "🔄 Store: Atualizando perfil com"
- [ ] Console mostra "📤 Store: Enviando para backend"
- [ ] Console mostra "updateProfile response"
- [ ] Console mostra "✅ Store: Usuário atualizado"
- [ ] Console mostra "💾 Store: Salvando no state..."
- [ ] Console mostra "💾 Store: State atualizado!"
- [ ] Console mostra "🔍 Store: Verificando localStorage..."
- [ ] Console mostra "💾 localStorage ts:auth = ..." (JSON completo)
- [ ] Console mostra "👤 localStorage user.language = es" (novo valor)
- [ ] Console mostra "⏰ localStorage user.timezone = America/Los_Angeles" (novo valor)
- [ ] Console mostra "✅ Preferências salvas com sucesso!"
- [ ] Toast verde aparece
- [ ] Network tab mostra PATCH com status 200

### Ao Reabrir Dialog:
- [ ] Console mostra "🔄 useEffect: Dialog abriu ou user mudou"
- [ ] Console mostra "👤 useEffect: user = ..." com valores NOVOS
- [ ] Console mostra "🌍 useEffect: user.language = es" (não pt-br!)
- [ ] Console mostra "⏰ useEffect: user.timezone = America/Los_Angeles" (não America/Sao_Paulo!)
- [ ] Dialog mostra Español selecionado
- [ ] Dialog mostra Los Angeles selecionado

### Após F5 (Recarregar):
- [ ] localStorage ainda tem language = es
- [ ] localStorage ainda tem timezone = America/Los_Angeles
- [ ] Ao abrir Preferências, valores estão corretos

---

## 🔬 Teste Rápido no Console

Cole este código no Console do DevTools para verificar o estado atual:

```javascript
// 1. Verificar localStorage
console.log('=== VERIFICAÇÃO localStorage ===');
const auth = JSON.parse(localStorage.getItem('ts:auth'));
console.log('Auth completo:', auth);
console.log('User:', auth?.state?.user);
console.log('Language:', auth?.state?.user?.language);
console.log('Timezone:', auth?.state?.user?.timezone);

// 2. Verificar Zustand store (se exposto)
console.log('\n=== VERIFICAÇÃO Zustand Store ===');
// Nota: Zustand não expõe store globalmente por padrão
// Os logs acima do localStorage devem ser suficientes

// 3. Fazer request manual para ver o que o backend retorna
console.log('\n=== VERIFICAÇÃO Backend ===');
const token = localStorage.getItem('access_token');
fetch('http://localhost:8000/api/users/me/', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
})
  .then(r => r.json())
  .then(data => {
    console.log('Backend user:', data);
    console.log('Backend language:', data.language);
    console.log('Backend timezone:', data.timezone);
  })
  .catch(err => console.error('Erro ao buscar do backend:', err));
```

**O que verificar:**
- ✅ localStorage deve ter `language` e `timezone` corretos
- ✅ Backend deve retornar `language` e `timezone` corretos
- ❌ Se localStorage está certo MAS backend está errado → problema no backend
- ❌ Se backend está certo MAS localStorage está errado → problema no persist do Zustand
- ❌ Se ambos estão errados → request de save falhou

---

## 🎯 Próximos Passos

1. **Executar teste acima** e anotar logs do console
2. **Verificar se há erros** na aba Console ou Network
3. **Copiar logs completos** para análise
4. **Verificar banco de dados** diretamente se necessário
5. **Remover logs de debug** após resolver o problema

---

**Status:** 🔍 Aguardando testes com logs de debug
