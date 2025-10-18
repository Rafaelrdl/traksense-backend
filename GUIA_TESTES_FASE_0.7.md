# Guia de Teste - Fase 0.7 (Dashboard e Exports)

**Data**: 18 de outubro de 2025  
**Status**: ✅ Pronto para Testes

---

## 📋 Pré-requisitos

### 1. Serviços Docker Rodando
```powershell
cd "c:\Users\Rafael Ribeiro\TrakSense\traksense-backend\docker"
docker-compose ps
```

**Esperado:**
- ✅ `traksense-postgres` - Healthy
- ✅ `traksense-redis` - Healthy  
- ✅ `traksense-minio` - Healthy
- ✅ `traksense-mailpit` - Healthy
- ✅ `traksense-api` - Running
- ✅ `traksense-worker` - Running

### 2. Migrations Aplicadas
```powershell
docker-compose run --rm api python manage.py migrate ops
```

**Esperado:**
- `[standard:public] Applying ops.0001_initial... OK`
- `[1/1 standard:uberlandia_medical_center] Applying ops.0001_initial... OK`

---

## 🧪 Teste 1: Dashboard com Gráficos

### Passo 1: Acessar o Dashboard
1. Abra o navegador
2. Acesse: `http://localhost:8000/admin/`
3. Login com credenciais de staff
4. Clique no botão **"🎛️ Control Center"** na barra lateral
5. Clique no botão **"Dashboard"** no topo da página

**URL Direta**: `http://localhost:8000/ops/dashboard/`

### Passo 2: Selecionar Tenant e Sensores
1. No dropdown **"Tenant *"**, selecione: `Uberlândia Medical Center (uberlandia-medical-center)`
2. Aguarde a página recarregar
3. Você verá checkboxes com sensores disponíveis (ex: temp_01, temp_02, temp_03, etc.)
4. Marque **2 ou 3 sensores** (ex: temp_01, temp_02)

### Passo 3: Configurar e Visualizar Gráfico
1. No dropdown **"Agregação"**, selecione: `5 minutos`
2. (Opcional) Preencha campos **"De"** e **"Até"** para limitar período
3. Clique no botão **"Atualizar Gráfico"**
4. Aguarde alguns segundos

**Resultados Esperados:**
- ✅ Badge "Carregando..." aparece e desaparece
- ✅ Gráfico de linhas é renderizado
- ✅ Múltiplas linhas com cores distintas (uma por sensor)
- ✅ Eixo X mostra tempo (formato HH:mm ou dd/MM HH:mm)
- ✅ Eixo Y mostra valores
- ✅ Badge mostra: "X pontos de dados"
- ✅ Título do gráfico: "Uberlândia Medical Center - Agregação: 5m"

### Passo 4: Testar Interatividade
1. Passe o mouse sobre os pontos do gráfico
2. Verifique o **tooltip** mostrando:
   - Nome do sensor
   - Valor exato
   - Min e Máx (se disponível)
3. Teste marcar mais sensores e clicar "Atualizar Gráfico"
4. Teste limite: tente marcar **11 sensores** (deve alertar: "Máximo de 10 sensores permitidos")

---

## 📥 Teste 2: Export Assíncrono

### Passo 1: Acessar Página de Exports
1. No Control Center, clique no botão **"Exports"** no topo
2. Você verá formulário de criação + tabela de histórico

**URL Direta**: `http://localhost:8000/ops/exports/`

### Passo 2: Criar Novo Export
1. No formulário:
   - **Tenant ***: `Uberlândia Medical Center (uberlandia-medical-center)`
   - **Sensor ID**: deixe vazio (para exportar todos) ou preencha `temp_01`
   - **De**: (opcional) deixe vazio
   - **Até**: (opcional) deixe vazio
2. Clique no botão **"Criar"** (ícone +)

**Resultados Esperados:**
- ✅ Mensagem verde: "Export #X criado! Você receberá um email quando estiver pronto."
- ✅ Nova linha aparece na tabela com status **"⏳ Pendente"**
- ✅ Página auto-refresh a cada 10s

### Passo 3: Acompanhar Processamento
1. Aguarde 10-20 segundos (página recarrega automaticamente)
2. Observe mudança de status:
   - `⏳ Pendente` → `⚙️ Processando` → `✅ Concluído`

**Se demorar muito** (> 30s), verifique logs do worker:
```powershell
docker-compose logs --tail=50 -f worker
```

### Passo 4: Download do CSV
1. Quando status = **"✅ Concluído"**:
   - Coluna **"Registros"** mostra quantidade (ex: 6,489)
   - Coluna **"Tamanho"** mostra MB (ex: 0.52 MB)
   - Coluna **"Ações"** mostra botão **"Download"**
2. Clique em **"Download"**
3. Arquivo CSV deve baixar automaticamente

**Validar CSV:**
- Abra o CSV no Excel ou editor de texto
- Deve ter colunas: `timestamp`, `sensor_id`, `value`, `unit`
- Dados devem estar corretos

### Passo 5: Testar Cancelamento
1. Crie outro export (mesmo processo do Passo 2)
2. **Rapidamente**, clique no botão **"Cancelar"** enquanto status = "⏳ Pendente"
3. Confirme na mensagem de alerta
4. Status deve mudar para **"❌ Falhou"**
5. Botão **"Ver Erro"** aparece
6. Clique em "Ver Erro" → Modal mostra: "Cancelado pelo usuário"

---

## 📧 Teste 3: Notificação por Email

### Passo 1: Acessar Mailpit
1. Abra: `http://localhost:8025/`
2. Você verá interface do Mailpit (simulador de email)

### Passo 2: Criar Export e Aguardar Conclusão
1. Crie novo export (Teste 2, Passo 2)
2. Aguarde status **"✅ Concluído"**
3. Acesse Mailpit: `http://localhost:8025/`

**Resultados Esperados:**
- ✅ Novo email na caixa de entrada
- ✅ Assunto: `[TrakSense] Export Concluído - Uberlândia Medical Center`
- ✅ Remetente: `traksense@localhost`
- ✅ Corpo do email em **português** com:
  - Detalhes do export (Tenant, Sensor, Período)
  - Quantidade de registros
  - Tamanho do arquivo
  - Link para download (válido por 24h)
  - Data de expiração

### Passo 3: Testar Email de Falha
1. Force uma falha (ex: export de tenant inexistente via API)
2. Verifique email com assunto: `[TrakSense] Export Falhou - ...`

---

## 🔍 Teste 4: Validação de UI em Português

### Checklist - Dashboard
- [ ] Breadcrumb: "Início" > "Dashboard"
- [ ] Título: "Dashboard de Telemetria"
- [ ] Alert: "Gráficos Interativos: Visualize tendências temporais..."
- [ ] Labels: "Tenant *", "Agregação", "Selecione Sensores (máx 10)"
- [ ] Dropdown agregação: "1 minuto", "5 minutos", "1 hora"
- [ ] Date pickers: "De (opcional)", "Até (opcional)"
- [ ] Botão: "Atualizar Gráfico"
- [ ] Chart título: "{Tenant} - Agregação: {bucket}"
- [ ] Eixos: "Tempo" (X), "Valor" (Y)
- [ ] Tooltip: "mín: X, máx: Y"
- [ ] Contador: "X pontos de dados"
- [ ] Alert erro: "Por favor, selecione um tenant primeiro"

### Checklist - Exports
- [ ] Breadcrumb: "Início" > "Exports"
- [ ] Título: "Exports Assíncronos"
- [ ] Alert: "Export em Background: Solicite exports grandes..."
- [ ] Labels: "Tenant *", "Sensor ID (opcional)", "De (opcional)", "Até (opcional)"
- [ ] Botão: "Criar" (com ícone +)
- [ ] Tabela headers: "ID", "Status", "Tenant", "Sensor", "Período", "Registros", "Tamanho", "Criado em", "Ações"
- [ ] Status badges: "⏳ Pendente", "⚙️ Processando", "✅ Concluído", "❌ Falhou"
- [ ] Botões ações: "Download", "Cancelar", "Ver Erro"
- [ ] Mensagem sucesso: "Export #X criado! Você receberá um email quando estiver pronto."
- [ ] Modal erro: Mostra mensagem de erro completa

---

## 🐛 Troubleshooting

### Problema: "connection is bad: Unknown host"
**Solução**: Certifique-se de que os containers estão rodando:
```powershell
cd "c:\Users\Rafael Ribeiro\TrakSense\traksense-backend\docker"
docker-compose ps
docker-compose up -d postgres redis minio mailpit api worker
```

### Problema: Dashboard não mostra sensores
**Solução**: Verifique se há dados de telemetria no tenant:
```powershell
docker-compose exec api python manage.py shell
```
```python
from django_tenants.utils import schema_context, get_tenant_model
from apps.ingest.models import TelemetryReading

tenant = get_tenant_model().objects.get(slug='uberlandia-medical-center')
with schema_context(tenant.slug):
    print(f"Total readings: {TelemetryReading.objects.count()}")
    sensors = TelemetryReading.objects.values_list('sensor_id', flat=True).distinct()
    print(f"Sensors: {list(sensors)}")
```

### Problema: Export fica em "Pendente" indefinidamente
**Solução**: Verificar logs do Celery Worker:
```powershell
docker-compose logs --tail=100 -f worker
```

Se worker não está rodando:
```powershell
docker-compose up -d worker
```

### Problema: Gráfico não renderiza
**Solução**:
1. Abra DevTools do navegador (F12)
2. Vá para aba **Console**
3. Procure por erros de JavaScript
4. Verifique se Chart.js foi carregado (aba Network)
5. Teste URL da API manualmente:
   ```
   http://localhost:8000/ops/api/chart-data/?tenant_slug=uberlandia-medical-center&sensor_ids=temp_01&bucket=5m
   ```

### Problema: CSV não tem dados
**Solução**: Verifique se há dados no tenant selecionado (ver script acima)

---

## ✅ Critérios de Sucesso

### Dashboard (Fase 0.7.1)
- [ ] Página carrega sem erros
- [ ] Tenant dropdown populado
- [ ] Sensores são listados após selecionar tenant
- [ ] Gráfico renderiza com múltiplos sensores
- [ ] Cores distintas para cada sensor
- [ ] Tooltip funciona corretamente
- [ ] Limite de 10 sensores é respeitado
- [ ] Agregação temporal funciona (1m, 5m, 1h)
- [ ] Date range filters funcionam
- [ ] Toda UI está em português
- [ ] Responsivo (funciona em mobile)

### Export Assíncrono (Fase 0.7.2)
- [ ] Página de exports carrega sem erros
- [ ] Formulário de criação funciona
- [ ] Export é enfileirado (status Pendente)
- [ ] Celery processa o export (status Processando → Concluído)
- [ ] CSV é gerado corretamente
- [ ] Download funciona
- [ ] Email de sucesso é enviado
- [ ] Email está em português
- [ ] Cancelamento funciona
- [ ] Modal de erro exibe mensagens
- [ ] Auto-refresh funciona
- [ ] Tabela mostra histórico
- [ ] Filtro por usuário funciona
- [ ] Toda UI está em português

---

## 📊 Relatório de Testes

### Template para Preencher:

**Data do Teste**: ___________  
**Testado por**: ___________

#### Dashboard:
- [ ] ✅ Todas as funcionalidades OK
- [ ] ⚠️ Problemas encontrados: ___________

#### Exports:
- [ ] ✅ Todas as funcionalidades OK
- [ ] ⚠️ Problemas encontrados: ___________

#### Email:
- [ ] ✅ Emails recebidos corretamente
- [ ] ⚠️ Problemas encontrados: ___________

#### Performance:
- Tempo médio para carregar dashboard: _____ segundos
- Tempo médio para processar export (10k registros): _____ segundos
- Tamanho típico de CSV: _____ MB

**Observações**:
- ___________
- ___________

**Status Final**: ✅ Aprovado | ⚠️ Com Ressalvas | ❌ Reprovado

---

**Criado por**: GitHub Copilot  
**Data**: 2025-10-18T18:35:00-03:00  
**Versão**: Fase 0.7 - Guia de Testes Completo
