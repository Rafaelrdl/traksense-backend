# 🧪 INSTRUÇÕES DE TESTE - DEBUG PREFERÊNCIAS

**Data:** 18/10/2025  
**Status:** ✅ Logs de debug adicionados - PRONTO PARA TESTE

---

## 📍 Contexto

Problema relatado:
- ✅ Preferências salvam (toast verde aparece)
- ❌ Ao fechar e reabrir, voltam aos valores padrão (pt-br, America/Sao_Paulo)
- ❌ Nenhum erro aparece no DevTools

---

## 🔧 O Que Foi Feito

### 1. Adicionados Logs Detalhados

**PreferencesDialog.tsx** - useEffect
```typescript
🔄 useEffect: Dialog abriu ou user mudou
📊 useEffect: open = true/false
👤 useEffect: user = {objeto completo}
🌍 useEffect: user.language = pt-br
⏰ useEffect: user.timezone = America/Sao_Paulo
✅ useEffect: Regionalization setado
```

**auth.ts** - updateUserProfile
```typescript
🔄 Store: Atualizando perfil com: {language, timezone}
📤 Store: Enviando para backend: {language, timezone}
✅ Store: Usuário atualizado: {objeto completo}
💾 Store: Salvando no state...
💾 Store: State atualizado!
🔍 Store: Verificando localStorage...
💾 localStorage ts:auth = {JSON completo}
👤 localStorage user.language = es
⏰ localStorage user.timezone = America/Los_Angeles
```

**auth.service.ts** - updateProfile
```typescript
updateProfile response: {user, message}
Response data: {detalhes do erro}
```

---

## 🎯 COMO TESTAR (PASSO A PASSO)

### 1️⃣ Preparar DevTools
```
1. Abra http://localhost:5000/
2. Pressione F12
3. Vá para aba Console
4. Limpe o console (Ctrl+L ou botão 🚫)
```

### 2️⃣ Verificar Estado Inicial
```javascript
// Cole no Console:
JSON.parse(localStorage.getItem('ts:auth'))
```
**Anote:** Valores atuais de `language` e `timezone`

### 3️⃣ Fazer Login
```
Email: test@umc.com
Senha: TestPass123!
```

### 4️⃣ Abrir Preferências (1ª VEZ)
```
1. Clique no avatar (canto superior direito)
2. Clique em "Preferências"
3. Vá para aba "Regionalização"
```

**Observe os logs:**
```
🔄 useEffect: Dialog abriu ou user mudou
📊 useEffect: open = true
👤 useEffect: user = {id: '...', language: 'pt-br', ...}
🔄 useEffect: Sincronizando regionalization com user
🌍 useEffect: user.language = pt-br
⏰ useEffect: user.timezone = America/Sao_Paulo
✅ useEffect: Regionalization setado para: {language: 'pt-br', timezone: 'America/Sao_Paulo'}
```

**✅ ANOTE:** Quais logs apareceram?

### 5️⃣ Alterar Valores
```
Idioma: 🇪🇸 Español
Timezone: Los Angeles (GMT-8)
```

### 6️⃣ Clicar em "Salvar Preferências"

**Observe TODA a sequência de logs:**
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

**✅ ANOTE:** 
- Quais logs apareceram?
- Qual foi o ÚLTIMO log antes de parar?
- Houve algum erro (❌)?

### 7️⃣ Verificar localStorage
```javascript
// Cole no Console novamente:
JSON.parse(localStorage.getItem('ts:auth'))
```

**✅ VERIFIQUE:**
- `state.user.language` deve ser `"es"`
- `state.user.timezone` deve ser `"America/Los_Angeles"`

### 8️⃣ Fechar Dialog
```
Clique em "Cancelar" ou clique fora
```

### 9️⃣ Reabrir Preferências (2ª VEZ)
```
1. Avatar → Preferências
2. Aba "Regionalização"
```

**🚨 MOMENTO CRÍTICO - Observe os logs:**
```
🔄 useEffect: Dialog abriu ou user mudou
📊 useEffect: open = true
👤 useEffect: user = {id: '...', language: '???', ...}
🌍 useEffect: user.language = ???
⏰ useEffect: user.timezone = ???
```

**🎯 PERGUNTAS CHAVE:**
1. O `user.language` está `'es'` ou `'pt-br'`?
2. O `user.timezone` está `'America/Los_Angeles'` ou `'America/Sao_Paulo'`?
3. O select mostra "Español" ou volta para "Português (Brasil)"?

### 🔟 Verificar Network Tab
```
1. DevTools → Aba Network
2. Procure: PATCH users/me/
3. Clique nela
4. Veja: Request Payload e Response
```

**✅ ANOTE:**
- Status: 200 OK?
- Request Payload tem `language: 'es'`?
- Response tem `user.language: 'es'`?

---

## 🧩 TESTE RÁPIDO NO CONSOLE

Cole tudo de uma vez:

```javascript
console.log('=== 🔍 DIAGNÓSTICO COMPLETO ===\n');

// 1. localStorage
console.log('1️⃣ localStorage:');
const auth = JSON.parse(localStorage.getItem('ts:auth'));
console.log('   User completo:', auth?.state?.user);
console.log('   Language:', auth?.state?.user?.language);
console.log('   Timezone:', auth?.state?.user?.timezone);

// 2. Backend
console.log('\n2️⃣ Backend (aguarde...):');
const token = localStorage.getItem('access_token');
fetch('http://localhost:8000/api/users/me/', {
  headers: { 'Authorization': `Bearer ${token}` }
})
  .then(r => r.json())
  .then(data => {
    console.log('   Backend user completo:', data);
    console.log('   Backend language:', data.language);
    console.log('   Backend timezone:', data.timezone);
    
    // 3. Comparação
    console.log('\n3️⃣ Comparação:');
    if (auth?.state?.user?.language === data.language) {
      console.log('   ✅ localStorage e backend estão SINCRONIZADOS');
    } else {
      console.log('   ❌ DESSINCRONIZADO!');
      console.log('      localStorage:', auth?.state?.user?.language);
      console.log('      Backend:', data.language);
    }
  })
  .catch(err => console.error('   ❌ Erro:', err));
```

---

## 🐛 CENÁRIOS POSSÍVEIS

### Cenário A: Logs Param em "📤 Store: Enviando"
**Significa:** Request nem chegou a ser feita  
**Causa:** Erro no authService ou interceptor Axios  
**Solução:** Verificar auth.service.ts e api.ts

### Cenário B: Logs Param em "✅ Store: Usuário atualizado"
**Significa:** Backend retornou erro ou formato inesperado  
**Causa:** Backend não salvou ou erro 400/500  
**Solução:** Verificar aba Network e backend logs

### Cenário C: Logs Mostram "👤 localStorage user.language = es" MAS ao Reabrir Volta
**Significa:** localStorage salvou, mas useEffect pega valor antigo  
**Causa:** Zustand persist não está funcionando corretamente  
**Solução:** Verificar partialize em auth.ts

### Cenário D: Tudo Certo até "💾 Store: State atualizado" MAS localStorage NÃO Tem "es"
**Significa:** persist middleware não está salvando  
**Causa:** Configuração do persist está errada  
**Solução:** Verificar configuração do persist em auth.ts

---

## 📋 CHECKLIST PARA COMPARTILHAR

Por favor, me envie:

- [ ] 📸 Screenshot da aba Console mostrando TODOS os logs do save
- [ ] 📸 Screenshot da aba Console ao REABRIR o dialog (logs do useEffect)
- [ ] 📸 Screenshot da aba Network mostrando PATCH users/me/
- [ ] 📋 Resultado do "Teste Rápido no Console" copiado
- [ ] 📊 Responda: Ao reabrir, o select mostra Español ou volta para Português?
- [ ] 💾 Resultado do `JSON.parse(localStorage.getItem('ts:auth'))` APÓS salvar

---

## 🎯 OBJETIVO

Descobrir exatamente em qual ponto os dados são perdidos:

```
Salvou no backend? ✅ ou ❌
  ↓
Salvou no Zustand store? ✅ ou ❌
  ↓
Salvou no localStorage? ✅ ou ❌
  ↓
useEffect lê valor correto? ✅ ou ❌
  ↓
Select mostra valor correto? ✅ ou ❌
```

---

**Status:** 🔍 Aguardando resultados do teste!
