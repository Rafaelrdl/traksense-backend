# ✅ CHECKLIST DE VALIDAÇÃO - SISTEMA DE ALERTAS

**Data**: 29 de Outubro de 2025  
**Versão**: 1.0  
**Tempo estimado**: 10-15 minutos

---

## 🎯 Objetivo

Validar que o sistema de alertas está 100% funcional, desde o backend até o frontend, incluindo a nova integração do badge no menu.

---

## ⚡ Pré-requisitos

Antes de começar, certifique-se de que:

- [ ] Backend está rodando (Docker containers ativos)
- [ ] Frontend está rodando (`npm run dev`)
- [ ] Você está logado no sistema
- [ ] Existe pelo menos 1 alerta no banco de dados

---

## 📋 Checklist de Validação

### 1. BACKEND ✅

#### Containers Docker
```powershell
cd "c:\Users\Rafael Ribeiro\TrakSense\traksense-backend"
docker ps
```

- [ ] `traksense-api` - Status: Up
- [ ] `traksense-postgres` - Status: Up
- [ ] `traksense-redis` - Status: Up
- [ ] `traksense-mailpit` - Status: Up (porta 8025)
- [ ] `traksense-emqx` - Status: Up

#### API Endpoints (Teste Manual via Browser/Postman)
```
GET http://localhost:8000/api/alerts/alerts/
GET http://localhost:8000/api/alerts/alerts/statistics/
GET http://localhost:8000/api/alerts/rules/
```

- [ ] Endpoints retornam JSON válido
- [ ] Status 200 OK
- [ ] Dados de alertas presentes

#### Criar Dados de Teste (Se necessário)
```powershell
docker exec -it traksense-api python create_sample_alerts.py
```

- [ ] Script executou sem erros
- [ ] Alertas criados no banco

---

### 2. FRONTEND - NAVEGAÇÃO ✅

#### Badge no Menu

**Desktop:**
- [ ] Abra `http://localhost:5173`
- [ ] Faça login
- [ ] Observe o menu horizontal no topo
- [ ] Item **"Alertas"** está presente
- [ ] Se houver alertas ativos, **badge vermelho** aparece com número
- [ ] Badge mostra número correto (ex: `[3]` se 3 alertas ativos)
- [ ] Badge NÃO aparece se não há alertas ativos

**Mobile/Tablet (< 768px):**
- [ ] Redimensione navegador para mobile
- [ ] Abra menu hambúrguer (☰)
- [ ] Item **"Alertas"** está na lista
- [ ] Badge aparece à direita do item (se houver alertas ativos)
- [ ] Badge mostra número correto

#### Navegação
- [ ] Clique em **"Alertas"** no menu
- [ ] Página **AlertsPage** carrega
- [ ] URL não muda (sistema usa state, não routing)
- [ ] Menu marca "Alertas" como ativo (background branco)

---

### 3. PÁGINA DE ALERTAS ✅

#### Cards de Estatísticas
- [ ] **Card "Total"**: Mostra número total de alertas
- [ ] **Card "Ativos"**: Mostra alertas não reconhecidos/resolvidos
- [ ] **Card "Reconhecidos"**: Mostra alertas reconhecidos mas não resolvidos
- [ ] **Card "Resolvidos"**: Mostra alertas finalizados
- [ ] Números batem com filtros aplicados

#### Filtros
- [ ] **Dropdown "Status"**: Todos, Ativos, Reconhecidos, Resolvidos
- [ ] Altere para "Ativos" → Lista filtra corretamente
- [ ] Altere para "Reconhecidos" → Lista filtra corretamente
- [ ] Altere para "Resolvidos" → Lista filtra corretamente
- [ ] **Dropdown "Severidade"**: Todas, Crítico, Alto, Médio, Baixo
- [ ] Filtre por "Crítico" → Lista mostra apenas alertas críticos

#### Lista de Alertas
- [ ] Alertas aparecem em ordem cronológica (mais recentes primeiro)
- [ ] Cada alerta mostra:
  - Nome da regra
  - Mensagem
  - Badge de severidade colorido (vermelho, laranja, amarelo, azul)
  - Status (Ativo, Reconhecido, Resolvido)
  - Timestamp
- [ ] Cores de severidade corretas:
  - **Crítico**: Vermelho
  - **Alto**: Laranja
  - **Médio**: Amarelo
  - **Baixo**: Azul

#### Auto-Refresh
- [ ] Aguarde 30 segundos na página
- [ ] **Spinner** aparece brevemente
- [ ] Dados são atualizados automaticamente
- [ ] Badge no menu também atualiza

#### Refresh Manual
- [ ] Clique no botão **"Atualizar"** (ícone de refresh)
- [ ] Spinner aparece
- [ ] Dados recarregam

---

### 4. DIALOG DE DETALHES DO ALERTA ✅

#### Abrir Dialog
- [ ] Clique em qualquer alerta da lista
- [ ] Dialog abre com overlay escuro
- [ ] Dialog centralizado na tela

#### Conteúdo do Dialog
- [ ] **Nome da Regra**: Aparece no topo
- [ ] **Mensagem**: Texto do alerta
- [ ] **Equipamento**: Nome do equipamento/asset
- [ ] **Severidade**: Badge colorido
- [ ] **Status**: Badge de status (Ativo, Reconhecido, Resolvido)
- [ ] **Criado em**: Timestamp formatado
- [ ] **Seção de Reconhecimento**: Aparece se reconhecido
  - Reconhecido por (email)
  - Reconhecido em (timestamp)
  - Notas de reconhecimento
- [ ] **Seção de Resolução**: Aparece se resolvido
  - Resolvido por (email)
  - Resolvido em (timestamp)
  - Notas de resolução

#### Ações no Dialog
- [ ] **Campo de Notas**: Input de texto funciona
- [ ] **Botão "Reconhecer Alerta"**: Visível se não reconhecido
- [ ] **Botão "Resolver Alerta"**: Visível se não resolvido
- [ ] **Botão "Fechar"**: Fecha o dialog

---

### 5. AÇÕES DE ALERTA ✅

#### Reconhecer Alerta
1. Abra um alerta **não reconhecido**
2. Digite notas (ex: "Investigando o problema")
3. Clique em **"Reconhecer Alerta"**

**Validações:**
- [ ] Toast de sucesso aparece ("Alerta reconhecido com sucesso")
- [ ] Dialog fecha automaticamente
- [ ] **Badge no menu diminui** (se era o único ativo)
- [ ] Card "Reconhecidos" incrementa (+1)
- [ ] Card "Ativos" decrementa (-1)
- [ ] Lista atualiza (alerta não aparece mais em "Ativos")

#### Resolver Alerta
1. Abra um alerta **reconhecido** (ou não reconhecido)
2. Digite notas de resolução (ex: "Problema corrigido")
3. Clique em **"Resolver Alerta"**

**Validações:**
- [ ] Toast de sucesso aparece ("Alerta resolvido com sucesso")
- [ ] Dialog fecha automaticamente
- [ ] **Badge no menu atualiza** (decrementa se estava ativo)
- [ ] Card "Resolvidos" incrementa (+1)
- [ ] Card "Reconhecidos" ou "Ativos" decrementa (-1)
- [ ] Alerta não aparece mais em filtros "Ativos" ou "Reconhecidos"
- [ ] Se era o último alerta ativo, badge desaparece do menu

---

### 6. PREFERÊNCIAS DE NOTIFICAÇÃO ✅

#### Abrir Dialog
1. Clique no **avatar** (canto superior direito)
2. Selecione **"Preferências"**
3. Dialog abre

**Validações:**
- [ ] Dialog tem 2 abas: "Notificações" e "Fusos Horários"
- [ ] Aba "Notificações" está ativa

#### Configurar Notificações
1. Na aba **"Notificações"**:

**Validações:**
- [ ] **Email**: Checkbox marcado (sempre habilitado)
- [ ] **Notificações In-App**: Checkbox funciona
- [ ] **SMS**: 
  - Checkbox funciona
  - Se marcado, campo de **"Número de Telefone"** aparece
  - Campo aceita entrada (+55 11 99999-9999)
- [ ] **WhatsApp**: 
  - Checkbox funciona
  - Se marcado, campo de **"Número do WhatsApp"** aparece
  - Campo aceita entrada
- [ ] **Push Notifications**: Checkbox funciona

#### Filtros de Severidade
- [ ] **Crítico**: Checkbox funciona (sempre marcado por padrão)
- [ ] **Alto**: Checkbox funciona
- [ ] **Médio**: Checkbox funciona
- [ ] **Baixo**: Checkbox funciona
- [ ] Pelo menos 1 severidade deve estar marcada

#### Salvar Preferências
1. Faça alterações (marque/desmarque checkboxes)
2. Digite números de telefone (se SMS/WhatsApp marcados)
3. Clique em **"Salvar Alterações"**

**Validações:**
- [ ] Spinner aparece no botão ("Salvando...")
- [ ] Toast de sucesso aparece ("Preferências salvas com sucesso")
- [ ] Dialog fecha automaticamente
- [ ] **Reabra o dialog**: Preferências salvas estão carregadas corretamente

---

### 7. MULTI-TENANCY ✅

**Se você tiver múltiplos sites/tenants:**

1. Use o **seletor de sites** no header (ao lado do logo)
2. Selecione outro site
3. Observe a página de alertas

**Validações:**
- [ ] Página recarrega
- [ ] Alertas mostrados são **apenas do site selecionado**
- [ ] Badge no menu reflete alertas do site atual
- [ ] Estatísticas são recalculadas para o site atual
- [ ] Não há alertas "vazando" entre sites

---

### 8. PERFORMANCE E UX ✅

#### Tempos de Carregamento
- [ ] Página inicial carrega em **< 3 segundos**
- [ ] Troca de página (navegação) é **instantânea** (< 500ms)
- [ ] Dialog abre **suavemente** (< 300ms)
- [ ] Filtros respondem **instantaneamente** (< 100ms)
- [ ] Auto-refresh não causa **lag** ou **freeze**

#### Loading States
- [ ] Spinner aparece durante carregamento inicial
- [ ] Skeleton screens (se implementados)
- [ ] Botões mostram "Carregando..." quando em ação
- [ ] Não há "flash" de conteúdo vazio

#### Error Handling
1. **Simule erro de rede**: Desligue backend
2. Tente atualizar alertas

**Validações:**
- [ ] Toast de erro aparece
- [ ] Mensagem clara ("Erro ao carregar alertas")
- [ ] Página não quebra (graceful degradation)
- [ ] Dados anteriores permanecem visíveis

---

### 9. CONSOLE DO NAVEGADOR ✅

Abra o **DevTools** (F12) → **Console**

**Validações:**
- [ ] **Nenhum erro** em vermelho
- [ ] **Nenhum warning** crítico
- [ ] Logs informativos OK (se houver)

Aba **Network**:
- [ ] Requests para `/api/alerts/alerts/` → Status **200**
- [ ] Requests para `/api/alerts/alerts/statistics/` → Status **200**
- [ ] Headers incluem `Authorization: Bearer <token>`
- [ ] Se multi-tenant, header `X-Tenant-Domain` presente

---

## 🎯 Critérios de Sucesso

Para considerar o sistema **100% validado**, todas as checkboxes acima devem estar marcadas ✅.

### Prioridades

**CRÍTICO (deve funcionar):**
- Backend rodando
- Endpoints retornando dados
- Badge aparecendo no menu com número correto
- AlertsPage carregando
- Reconhecer/Resolver alertas funcionando
- Preferências salvando

**IMPORTANTE (deve funcionar bem):**
- Auto-refresh funcionando
- Filtros funcionando
- Dialog de detalhes completo
- Multi-tenancy isolando dados

**DESEJÁVEL (pode ter bugs menores):**
- Performance otimizada
- Loading states suaves
- Error handling elegante

---

## 🐛 Encontrou um Bug?

Se alguma checkbox não pôde ser marcada:

1. **Anote o problema**:
   - O que você tentou fazer?
   - O que esperava acontecer?
   - O que realmente aconteceu?

2. **Verifique os logs**:
   ```powershell
   # Backend
   docker logs traksense-api --tail 50
   
   # Console do navegador (F12)
   ```

3. **Verifique a documentação**:
   - `INTEGRACAO_COMPLETA_ALERTAS.md` → Troubleshooting
   - `GUIA_TESTE_FRONTEND_ALERTAS.md`

4. **Reporte o bug** com:
   - Descrição do problema
   - Logs relevantes
   - Screenshots (se aplicável)

---

## ✅ Resultado Final

Após completar este checklist:

- [ ] **Todos os itens críticos** estão ✅
- [ ] **Pelo menos 90% dos itens importantes** estão ✅
- [ ] **Bugs encontrados foram documentados**
- [ ] **Sistema está pronto para uso**

---

## 🎉 Parabéns!

Se você chegou até aqui e marcou tudo ✅, o sistema de alertas está **100% funcional e validado**.

**Próximos passos:**
1. Use o sistema em produção
2. Monitore logs e performance
3. Colete feedback dos usuários
4. Itere e melhore conforme necessário

---

**Data de Validação**: _____/_____/_____  
**Validado por**: _____________________  
**Status**: 🎯 **APROVADO** / ⚠️ **COM RESSALVAS** / ❌ **REPROVADO**

**Observações**:
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________
