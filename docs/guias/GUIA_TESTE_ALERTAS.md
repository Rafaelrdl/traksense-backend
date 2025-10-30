# 🚨 Guia de Teste - Sistema de Alertas e Regras (FASE 6)

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Preparação do Ambiente](#preparação-do-ambiente)
3. [Testes de API](#testes-de-api)
4. [Testes de Notificações](#testes-de-notificações)
5. [Testes de Monitoramento](#testes-de-monitoramento)
6. [Testes End-to-End](#testes-end-to-end)

---

## 🎯 Visão Geral

O sistema de alertas e regras implementa:
- **Rules**: Regras de monitoramento com condições e thresholds
- **Alerts**: Alertas disparados quando regras são violadas
- **Notification Preferences**: Preferências de notificação por usuário
- **Notification Service**: Serviço de envio de notificações (Email, In-App, SMS, WhatsApp)
- **Rule Evaluation**: Tarefa Celery periódica para avaliar regras

### Arquitetura de Notificações

```
Rule.actions (O que PODE acontecer)
    ∩
User.preferences (O que o usuário QUER)
    =
Notificações Enviadas
```

---

## 🔧 Preparação do Ambiente

### 1. Verificar Containers

```powershell
docker ps
```

Deve mostrar todos os containers rodando:
- `traksense-api`
- `traksense-postgres`
- `traksense-redis`
- `traksense-mailpit`
- `traksense-emqx`

### 2. Aplicar Migrations (se não aplicou ainda)

```powershell
docker exec traksense-api python manage.py migrate
```

### 3. Criar Dados de Teste

```powershell
docker exec -it traksense-api python create_sample_alerts.py
```

Escolha a opção `4` para criar:
- Regras de exemplo
- Alertas de exemplo
- Preferências de usuário

### 4. Reiniciar API (para carregar novas tasks)

```powershell
docker restart traksense-api
```

---

## 🔌 Testes de API

### 1. Testar Endpoint de Rules

#### Listar Regras

```powershell
curl -X GET "http://umc.localhost:8000/api/alerts/rules/" `
  -H "Authorization: Bearer SEU_TOKEN" `
  -H "Content-Type: application/json"
```

#### Criar Nova Regra

```powershell
$body = @{
  name = "Temperature Too High"
  description = "Alert when temperature exceeds 28°C"
  equipment = 1  # ID do equipamento
  parameter_key = "temperature"
  variable_key = "value"
  operator = ">"
  threshold = 28.0
  severity = "HIGH"
  actions = @("EMAIL", "IN_APP")
  enabled = $true
  cooldown_minutes = 15
} | ConvertTo-Json

curl -X POST "http://umc.localhost:8000/api/alerts/rules/" `
  -H "Authorization: Bearer SEU_TOKEN" `
  -H "Content-Type: application/json" `
  -d $body
```

#### Ativar/Desativar Regra

```powershell
curl -X POST "http://umc.localhost:8000/api/alerts/rules/1/toggle_status/" `
  -H "Authorization: Bearer SEU_TOKEN" `
  -H "Content-Type: application/json"
```

#### Estatísticas de Regras

```powershell
curl -X GET "http://umc.localhost:8000/api/alerts/rules/statistics/" `
  -H "Authorization: Bearer SEU_TOKEN" `
  -H "Content-Type: application/json"
```

### 2. Testar Endpoint de Alerts

#### Listar Alertas

```powershell
curl -X GET "http://umc.localhost:8000/api/alerts/alerts/" `
  -H "Authorization: Bearer SEU_TOKEN" `
  -H "Content-Type: application/json"
```

#### Filtrar Alertas Ativos

```powershell
curl -X GET "http://umc.localhost:8000/api/alerts/alerts/?status=active" `
  -H "Authorization: Bearer SEU_TOKEN" `
  -H "Content-Type: application/json"
```

#### Reconhecer Alerta

```powershell
$body = @{
  notes = "Investigando o problema"
} | ConvertTo-Json

curl -X POST "http://umc.localhost:8000/api/alerts/alerts/1/acknowledge/" `
  -H "Authorization: Bearer SEU_TOKEN" `
  -H "Content-Type: application/json" `
  -d $body
```

#### Resolver Alerta

```powershell
$body = @{
  notes = "Problema resolvido - temperatura normalizada"
} | ConvertTo-Json

curl -X POST "http://umc.localhost:8000/api/alerts/alerts/1/resolve/" `
  -H "Authorization: Bearer SEU_TOKEN" `
  -H "Content-Type: application/json" `
  -d $body
```

#### Estatísticas de Alertas

```powershell
curl -X GET "http://umc.localhost:8000/api/alerts/alerts/statistics/" `
  -H "Authorization: Bearer SEU_TOKEN" `
  -H "Content-Type: application/json"
```

### 3. Testar Endpoint de Preferências

#### Obter Minhas Preferências

```powershell
curl -X GET "http://umc.localhost:8000/api/alerts/notification-preferences/me/" `
  -H "Authorization: Bearer SEU_TOKEN" `
  -H "Content-Type: application/json"
```

#### Atualizar Minhas Preferências

```powershell
$body = @{
  email_enabled = $true
  push_enabled = $true
  sound_enabled = $true
  sms_enabled = $false
  whatsapp_enabled = $false
  critical_alerts = $true
  high_alerts = $true
  medium_alerts = $true
  low_alerts = $false
  phone_number = "+5511999999999"
} | ConvertTo-Json

curl -X PATCH "http://umc.localhost:8000/api/alerts/notification-preferences/me/" `
  -H "Authorization: Bearer SEU_TOKEN" `
  -H "Content-Type: application/json" `
  -d $body
```

---

## 📧 Testes de Notificações

### 1. Verificar Mailpit (Email de Teste)

Abra no navegador: http://localhost:8025

Este é o Mailpit - servidor SMTP de desenvolvimento que captura todos os emails enviados.

### 2. Testar Envio de Email

Execute no Django shell:

```powershell
docker exec -it traksense-api python manage.py shell
```

```python
from apps.alerts.models import Alert
from apps.alerts.services import NotificationService

# Pegar um alerta
alert = Alert.objects.first()

# Criar serviço de notificações
service = NotificationService()

# Enviar notificações
results = service.send_alert_notifications(alert)

print("Sent:", len(results['sent']))
print("Failed:", len(results['failed']))
print("Skipped:", len(results['skipped']))
```

Depois, verifique o Mailpit (http://localhost:8025) para ver o email recebido.

### 3. Testar Lógica de Preferências

```python
from apps.accounts.models import User
from apps.alerts.models import NotificationPreference, Rule, Alert

# Criar preferências para um usuário
user = User.objects.first()
pref, created = NotificationPreference.objects.get_or_create(user=user)

# Desabilitar alertas de baixa prioridade
pref.low_alerts = False
pref.save()

# Criar regra de baixa prioridade
rule = Rule.objects.filter(severity='LOW').first()

# Criar alerta
alert = Alert.objects.create(
    rule=rule,
    asset_tag='TEST-001',
    equipment_name='Test Equipment',
    severity='LOW',
    message='Test low priority alert'
)

# Tentar enviar - deve ser pulado (skipped)
service = NotificationService()
results = service.send_alert_notifications(alert, users=[user])

print(results)  # Deve mostrar "skipped" pois usuário desabilitou alertas LOW
```

---

## 🤖 Testes de Monitoramento

### 1. Executar Avaliação Manual de Regras

```powershell
docker exec traksense-api python manage.py shell
```

```python
from apps.alerts.tasks import evaluate_rules_task

# Executar avaliação
result = evaluate_rules_task()

print(result)
# Output: {'evaluated': X, 'triggered': Y, 'errors': Z}
```

### 2. Verificar Celery Beat

```powershell
# Ver logs do Celery Beat
docker logs traksense-api | Select-String "celery"
```

Deve mostrar:
- `celery beat v5.x.x is starting.`
- Task scheduled: `alerts.evaluate_rules`
- Task scheduled: `alerts.cleanup_old_alerts`

### 3. Monitorar Execução de Tasks

```powershell
# Ver execuções recentes
docker exec traksense-api python manage.py shell
```

```python
from celery.result import AsyncResult
from config.celery import app

# Ver tasks agendadas
inspect = app.control.inspect()
scheduled = inspect.scheduled()
print("Scheduled tasks:", scheduled)

# Ver tasks ativas
active = inspect.active()
print("Active tasks:", active)
```

---

## 🔄 Testes End-to-End

### Cenário 1: Criação e Disparo de Alerta

1. **Criar uma regra**
   ```powershell
   # Via API ou Django Admin
   # http://localhost:8000/admin
   ```

2. **Simular telemetria que excede threshold**
   ```python
   from apps.ingest.models import TelemetryReading
   from apps.assets.models import Asset
   
   asset = Asset.objects.first()
   
   # Criar leitura que excede threshold
   TelemetryReading.objects.create(
       asset_tag=asset.asset_tag,
       parameter_key='temperature',
       value=35.0,  # Acima do threshold de 30°C
       data={'unit': '°C'}
   )
   ```

3. **Executar avaliação de regras**
   ```python
   from apps.alerts.tasks import evaluate_rules_task
   evaluate_rules_task()
   ```

4. **Verificar alerta criado**
   ```python
   from apps.alerts.models import Alert
   latest_alert = Alert.objects.latest('triggered_at')
   print(f"Alert: {latest_alert.message}")
   print(f"Severity: {latest_alert.severity}")
   print(f"Status: {'Active' if latest_alert.is_active else 'Inactive'}")
   ```

5. **Verificar email no Mailpit**
   - Abrir http://localhost:8025
   - Deve ter um email com o alerta

### Cenário 2: Workflow de Alerta Completo

1. **Criar alerta** (via API ou shell)

2. **Reconhecer alerta**
   ```powershell
   curl -X POST "http://umc.localhost:8000/api/alerts/alerts/1/acknowledge/" `
     -H "Authorization: Bearer TOKEN" `
     -H "Content-Type: application/json" `
     -d '{"notes":"Analisando..."}'
   ```

3. **Verificar status**
   ```python
   alert = Alert.objects.get(id=1)
   print(f"Acknowledged: {alert.acknowledged}")
   print(f"Acknowledged by: {alert.acknowledged_by.email}")
   print(f"Is active: {alert.is_active}")  # Ainda True
   ```

4. **Resolver alerta**
   ```powershell
   curl -X POST "http://umc.localhost:8000/api/alerts/alerts/1/resolve/" `
     -H "Authorization: Bearer TOKEN" `
     -H "Content-Type: application/json" `
     -d '{"notes":"Problema resolvido"}'
   ```

5. **Verificar status final**
   ```python
   alert.refresh_from_db()
   print(f"Resolved: {alert.resolved}")
   print(f"Resolved by: {alert.resolved_by.email}")
   print(f"Is active: {alert.is_active}")  # Agora False
   ```

---

## ✅ Checklist de Validação

### Backend API
- [ ] Listar regras
- [ ] Criar regra
- [ ] Editar regra
- [ ] Ativar/desativar regra
- [ ] Deletar regra
- [ ] Estatísticas de regras

### Alertas
- [ ] Listar alertas
- [ ] Filtrar alertas (active, acknowledged, resolved)
- [ ] Reconhecer alerta
- [ ] Resolver alerta
- [ ] Estatísticas de alertas

### Preferências
- [ ] Obter preferências do usuário logado
- [ ] Atualizar preferências
- [ ] Auto-criação de preferências padrão

### Notificações
- [ ] Email enviado corretamente
- [ ] Template de email renderizado
- [ ] Respeita preferências de severidade
- [ ] Respeita canais habilitados

### Monitoramento
- [ ] Task de avaliação executa sem erros
- [ ] Alertas criados quando threshold excedido
- [ ] Cooldown funciona corretamente
- [ ] Notificações enviadas após criação de alerta

### Multi-tenant
- [ ] Dados isolados por tenant
- [ ] Rules acessam apenas equipamentos do tenant
- [ ] Alerts isolados por tenant
- [ ] Preferences isoladas por tenant

---

## 🐛 Troubleshooting

### Erro: "Unknown host" ao rodar migrations

**Solução**: Rodar dentro do container:
```powershell
docker exec traksense-api python manage.py migrate
```

### Emails não estão sendo enviados

**Verificar**:
1. Mailpit está rodando: `docker ps | Select-String mailpit`
2. Settings de email no `.env`:
   ```
   MAILPIT_SMTP_HOST=mailpit
   MAILPIT_SMTP_PORT=1025
   ```
3. Logs: `docker logs traksense-api | Select-String "email"`

### Tasks Celery não estão executando

**Verificar**:
1. Redis está rodando: `docker ps | Select-String redis`
2. Celery Beat está ativo: `docker logs traksense-api | Select-String "celery beat"`
3. Tasks agendadas:
   ```python
   from config.celery import app
   inspect = app.control.inspect()
   print(inspect.scheduled())
   ```

### Regras não estão disparando alertas

**Verificar**:
1. Regra está habilitada: `rule.enabled == True`
2. Telemetria existe para o equipamento
3. Telemetria é recente (< 15 minutos)
4. Cooldown não está ativo
5. Logs da task: `docker logs traksense-api | Select-String "evaluate_rules"`

---

## 📊 Métricas de Sucesso

- ✅ Todas as APIs retornam 200/201
- ✅ Regras são criadas e listadas
- ✅ Alertas são criados quando regras são violadas
- ✅ Emails chegam no Mailpit
- ✅ Preferências são respeitadas
- ✅ Workflow de acknowledge/resolve funciona
- ✅ Tasks Celery executam sem erros
- ✅ Multi-tenancy funcionando

---

## 🎓 Próximos Passos

Após validar o backend:

1. **Integrar com Frontend**
   - Consumir APIs de rules
   - Consumir APIs de alerts
   - Atualizar preferências

2. **Implementar Providers Reais**
   - Twilio para SMS/WhatsApp
   - Firebase para Push Notifications

3. **Otimizações**
   - Cachear regras ativas
   - Batch de notificações
   - Websockets para alertas em tempo real

4. **Monitoramento**
   - Métricas de performance
   - Alertas sobre alertas (meta!)
   - Dashboard de saúde do sistema
