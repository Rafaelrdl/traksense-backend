# 🎯 FASE 6 - Sistema de Alertas e Regras - IMPLEMENTAÇÃO COMPLETA

**Data**: 29 de Outubro de 2025  
**Status**: ✅ **BACKEND COMPLETO E FUNCIONAL**

---

## 📋 Resumo Executivo

Implementação completa do sistema de alertas e regras para monitoramento de equipamentos HVAC, incluindo:

- ✅ **3 Modelos Django** (Rule, Alert, NotificationPreference)
- ✅ **6 Serializers** com validação completa
- ✅ **3 ViewSets** com 10+ actions customizadas
- ✅ **Serviço de Notificações** multi-canal
- ✅ **Sistema de Monitoramento** via Celery
- ✅ **Templates de Email** responsivos
- ✅ **Migrations** aplicadas com sucesso
- ✅ **URLs** configuradas e integradas
- ✅ **Tasks Periódicas** agendadas

---

## 🏗️ Arquitetura Implementada

### 1. Modelos de Dados

#### **Rule** (Regras de Monitoramento)
```python
- equipment: FK para Asset
- parameter_key: Campo da telemetria a monitorar
- operator: >, <, >=, <=, ==, !=
- threshold: Valor limite
- severity: CRITICAL, HIGH, MEDIUM, LOW
- actions: Lista de ações (EMAIL, IN_APP, SMS, WHATSAPP)
- enabled: Ativa/desativa regra
- cooldown_minutes: Tempo mínimo entre alertas
```

#### **Alert** (Alertas Disparados)
```python
- rule: FK para Rule
- asset_tag: Identificador do equipamento
- severity: Herdado da regra
- acknowledged: Bool + timestamp + user
- resolved: Bool + timestamp + user
- is_active: Property (not acknowledged AND not resolved)
```

#### **NotificationPreference** (Preferências do Usuário)
```python
- user: OneToOne com User
- email_enabled, push_enabled, sound_enabled, sms_enabled, whatsapp_enabled
- critical_alerts, high_alerts, medium_alerts, low_alerts
- phone_number, whatsapp_number
- Métodos: should_notify_severity(), get_enabled_channels()
```

### 2. API Endpoints

#### **Rules API** (`/api/alerts/rules/`)
```
GET     /                      - Lista regras
POST    /                      - Cria regra
GET     /{id}/                 - Detalhe da regra
PUT     /{id}/                 - Atualiza regra
DELETE  /{id}/                 - Deleta regra
POST    /{id}/toggle_status/   - Ativa/desativa
GET     /statistics/           - Estatísticas por severidade
```

**Filtros**: `enabled`, `severity`, `equipment_id`

#### **Alerts API** (`/api/alerts/alerts/`)
```
GET     /                      - Lista alertas
POST    /                      - Cria alerta (admin)
GET     /{id}/                 - Detalhe do alerta
PUT     /{id}/                 - Atualiza alerta
DELETE  /{id}/                 - Deleta alerta
POST    /{id}/acknowledge/     - Reconhece alerta
POST    /{id}/resolve/         - Resolve alerta
GET     /statistics/           - Estatísticas (active, acknowledged, resolved)
```

**Filtros**: `status` (active/acknowledged/resolved), `severity`, `rule_id`, `asset_tag`

#### **Preferences API** (`/api/alerts/notification-preferences/`)
```
GET     /                      - Lista preferências (admin)
POST    /                      - Cria preferências (admin)
GET     /{id}/                 - Detalhe
PUT     /{id}/                 - Atualiza
GET     /me/                   - Minhas preferências
PUT     /me/                   - Atualiza minhas preferências
PATCH   /me/                   - Atualiza parcialmente
```

Auto-cria preferências padrão no primeiro acesso.

### 3. Serviço de Notificações

**Arquivo**: `apps/alerts/services/notification_service.py`

#### Lógica Hierárquica
```
Notificação Enviada = (action in rule.actions) AND (channel in user.preferences) AND (severity in user.preferences)
```

#### Canais Implementados
- ✅ **Email**: Django email backend + Mailpit (dev)
- ✅ **In-App**: Placeholder (pronto para FCM/APNs)
- ✅ **SMS**: Placeholder (pronto para Twilio/AWS SNS)
- ✅ **WhatsApp**: Placeholder (pronto para Twilio/Meta)

#### Método Principal
```python
service = NotificationService()
results = service.send_alert_notifications(alert, users=None)
# Returns: {'sent': [...], 'failed': [...], 'skipped': [...]}
```

### 4. Sistema de Monitoramento

**Arquivo**: `apps/alerts/tasks.py`

#### Task 1: `evaluate_rules_task()`
- **Frequência**: A cada 5 minutos (300s)
- **Função**: Avalia todas as regras ativas contra telemetria
- **Processo**:
  1. Busca telemetria recente (< 15 min)
  2. Compara com threshold
  3. Verifica cooldown
  4. Cria alerta se condição atendida
  5. Envia notificações

#### Task 2: `cleanup_old_alerts_task()`
- **Frequência**: Uma vez por dia (86400s)
- **Função**: Remove alertas resolvidos antigos (> 90 dias)

#### Configuração Celery Beat
```python
CELERY_BEAT_SCHEDULE = {
    'evaluate-alert-rules': {
        'task': 'alerts.evaluate_rules',
        'schedule': 300.0,  # 5 minutos
    },
    'cleanup-old-alerts': {
        'task': 'alerts.cleanup_old_alerts',
        'schedule': 86400.0,  # 24 horas
    },
}
```

---

## 📁 Estrutura de Arquivos

```
apps/alerts/
├── __init__.py
├── apps.py                  ✅ Configuração do app
├── models.py                ✅ Rule, Alert, NotificationPreference
├── serializers.py           ✅ 6 serializers com validação
├── views.py                 ✅ 3 ViewSets com actions
├── urls.py                  ✅ Router configurado
├── admin.py                 ✅ Django admin
├── tasks.py                 ✅ Celery tasks
├── migrations/
│   └── 0001_initial.py      ✅ Aplicada com sucesso
├── services/
│   ├── __init__.py
│   └── notification_service.py  ✅ Multi-channel notifications
└── templates/
    └── alerts/
        └── email/
            └── alert_notification.html  ✅ Template responsivo
```

---

## 🔧 Configurações Atualizadas

### `config/settings/base.py`

#### TENANT_APPS
```python
TENANT_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.admin',
    'django.contrib.sessions',
    'django.contrib.auth',
    'apps.accounts',
    'apps.ingest',
    'apps.assets',
    'apps.alerts',  # ✅ ADICIONADO
]
```

#### CELERY_BEAT_SCHEDULE
```python
CELERY_BEAT_SCHEDULE = {
    # ... existing tasks ...
    'evaluate-alert-rules': {
        'task': 'alerts.evaluate_rules',
        'schedule': 300.0,
    },
    'cleanup-old-alerts': {
        'task': 'alerts.cleanup_old_alerts',
        'schedule': 86400.0,
    },
}
```

### `config/urls.py`
```python
urlpatterns = [
    # ... existing paths ...
    path('api/alerts/', include('apps.alerts.urls')),  # ✅ ADICIONADO
]
```

---

## 🗄️ Database Schema

### Tabelas Criadas

#### `alerts_rule`
```sql
- id (PK)
- equipment_id (FK → assets_asset)
- name, description
- parameter_key, variable_key
- operator, threshold
- severity (CRITICAL, HIGH, MEDIUM, LOW)
- actions (JSON array)
- enabled (bool)
- cooldown_minutes (int)
- created_by_id (FK → accounts_user)
- created_at, updated_at
```

**Índices**:
- `(equipment, enabled)` - Performance para busca de regras ativas
- `(severity, enabled)` - Estatísticas por severidade

#### `alerts_alert`
```sql
- id (PK)
- rule_id (FK → alerts_rule)
- asset_tag, equipment_name
- severity
- message, raw_data (JSON)
- triggered_at
- acknowledged (bool)
- acknowledged_at, acknowledged_by_id (FK)
- acknowledged_notes
- resolved (bool)
- resolved_at, resolved_by_id (FK)
- resolved_notes
```

**Índices**:
- `(rule, triggered_at)` - Busca de alertas por regra
- `(acknowledged, resolved)` - Filtro de status (active/acknowledged/resolved)
- `(severity, triggered_at)` - Ordenação por severidade
- `(asset_tag)` - Busca por equipamento

#### `alerts_notificationpreference`
```sql
- id (PK)
- user_id (OneToOne → accounts_user)
- email_enabled, push_enabled, sound_enabled
- sms_enabled, whatsapp_enabled
- critical_alerts, high_alerts, medium_alerts, low_alerts
- phone_number, whatsapp_number
- created_at, updated_at
```

---

## 🎨 Templates de Email

### `alert_notification.html`

**Features**:
- Design responsivo
- Badge de severidade colorido (CRITICAL=red, HIGH=orange, MEDIUM=yellow, LOW=blue)
- Informações do alerta formatadas
- Botão CTA para visualizar detalhes
- Footer com instruções e link para preferências
- Styled com CSS inline (compatível com email clients)

**Contexto**:
```python
{
    'alert': Alert instance,
    'rule': Rule instance,
    'user': User instance,
    'severity_label': Display name da severidade,
}
```

---

## 🧪 Scripts de Teste

### `create_sample_alerts.py`

**Funcionalidades**:
1. **Criar regras de exemplo**:
   - High Temperature (CRITICAL)
   - Low Humidity (HIGH)
   - High Power Consumption (MEDIUM)
   - Equipment Offline (LOW)

2. **Criar alertas de teste**

3. **Configurar preferências de usuários**:
   - Email, Push, Sound: Habilitados
   - SMS, WhatsApp: Desabilitados (requer telefone)
   - Critical, High, Medium: Habilitados
   - Low: Desabilitado por padrão

**Uso**:
```powershell
docker exec -it traksense-api python create_sample_alerts.py
```

---

## ✅ Validações Implementadas

### Serializers

#### RuleSerializer
- ✅ `actions` deve conter apenas: EMAIL, IN_APP, SMS, WHATSAPP
- ✅ `threshold` deve ser numérico
- ✅ `cooldown_minutes` >= 0

#### NotificationPreferenceSerializer
- ✅ `phone_number` deve começar com '+'
- ✅ `whatsapp_number` deve começar com '+'
- ✅ Se `sms_enabled=True`, `phone_number` é obrigatório
- ✅ Se `whatsapp_enabled=True`, `whatsapp_number` é obrigatório

#### AcknowledgeAlertSerializer
- ✅ `notes` pode ser opcional
- ✅ Auto-define `acknowledged_by` como usuário logado

#### ResolveAlertSerializer
- ✅ `notes` pode ser opcional
- ✅ Auto-define `resolved_by` como usuário logado
- ✅ Auto-acknowledges se não foi reconhecido antes

---

## 🔐 Permissões

### Todas as Views
- ✅ `IsAuthenticated` - Usuário deve estar autenticado
- ✅ `IsTenantMember` - Usuário deve pertencer ao tenant (multi-tenancy)

### Write Operations (POST, PUT, DELETE)
- ✅ `CanWrite` - Usuário deve ter permissão de escrita (GERENTE ou ADMIN)

### Admin-Only Operations
- ✅ Criar alertas manualmente (via API)
- ✅ Listar todas as preferências de usuários

---

## 📊 Fluxo de Dados

### Criação de Alerta (Automático)

```
1. Telemetry Reading chega
   ↓
2. Celery Task (5 min) executa evaluate_rules_task()
   ↓
3. Para cada Rule ativa:
   - Busca última telemetria
   - Compara com threshold
   - Verifica cooldown
   ↓
4. Se condição atendida:
   - Cria Alert
   - Chama NotificationService
   ↓
5. NotificationService:
   - Para cada usuário:
     - Verifica preferências de severidade
     - Verifica canais habilitados
     - Envia notificações
```

### Workflow de Alerta

```
Alert Created (is_active = True)
   ↓
[Acknowledge] → acknowledged = True (is_active = True)
   ↓
[Resolve] → resolved = True (is_active = False)
```

**Nota**: `resolve()` auto-acknowledges se não foi reconhecido.

---

## 🚀 Deployment Checklist

### Antes do Deploy

- [x] Migrations criadas
- [x] Migrations aplicadas
- [x] URLs configuradas
- [x] Celery Beat configurado
- [x] Templates de email criados
- [x] Testes manuais realizados

### Após o Deploy

- [ ] Configurar provedor de SMS (Twilio/AWS SNS)
- [ ] Configurar provedor de WhatsApp (Twilio/Meta)
- [ ] Configurar push notifications (FCM/APNs)
- [ ] Configurar email de produção (SendGrid/SES)
- [ ] Monitorar logs de Celery
- [ ] Criar dashboards de métricas
- [ ] Configurar alertas de monitoramento (meta-alertas!)

---

## 📈 Métricas e KPIs

### Performance
- Avaliação de regras: < 30s para 100 regras
- Criação de alerta: < 1s
- Envio de notificações: < 5s por usuário

### Disponibilidade
- Celery Beat uptime: > 99.9%
- API availability: > 99.9%
- Email delivery rate: > 95%

### Uso
- Total de regras ativas
- Total de alertas/dia
- Taxa de acknowledge (% de alertas reconhecidos)
- Taxa de resolve (% de alertas resolvidos)
- Notificações enviadas por canal

---

## 🐛 Known Issues & Limitations

### Limitações Atuais

1. **Push Notifications**: Placeholder - requer integração com FCM/APNs
2. **SMS/WhatsApp**: Placeholder - requer conta Twilio/AWS SNS
3. **Real-time Alerts**: Usa polling (Celery 5min) - considerar WebSockets
4. **Batch Notifications**: Envia individual - otimizar para múltiplos destinatários
5. **Alert Deduplication**: Usa cooldown - considerar algoritmo mais sofisticado

### Melhorias Futuras

- [ ] WebSocket para alertas em tempo real
- [ ] Aggregation de alertas similares
- [ ] Machine learning para threshold adaptativo
- [ ] Escalation automática (se não reconhecido em X tempo)
- [ ] Integração com sistemas externos (Slack, PagerDuty, etc.)
- [ ] Relatórios e analytics de alertas
- [ ] Mobile app com push real

---

## 🔗 Integrações

### Existentes
- ✅ **Django Multi-Tenant**: Isolamento de dados por tenant
- ✅ **Celery + Redis**: Tasks assíncronas e agendadas
- ✅ **PostgreSQL**: Armazenamento de regras, alertas, preferências
- ✅ **Mailpit**: Email de desenvolvimento
- ✅ **TelemetryReading**: Fonte de dados para avaliação

### Planejadas
- 🔜 **Twilio**: SMS e WhatsApp
- 🔜 **Firebase**: Push notifications
- 🔜 **SendGrid/SES**: Email de produção
- 🔜 **Websockets**: Real-time alerts no frontend

---

## 📚 Documentação Adicional

- **GUIA_TESTE_ALERTAS.md** - Guia completo de testes
- **API Documentation** - http://localhost:8000/api/docs/ (Swagger)
- **Django Admin** - http://localhost:8000/admin/

---

## 👥 Contatos e Suporte

**Desenvolvedor**: GitHub Copilot  
**Data de Implementação**: 29 de Outubro de 2025  
**Versão**: 1.0.0

---

## ✨ Conclusão

O sistema de alertas e regras está **100% funcional** no backend, pronto para:
1. ✅ Integração com frontend React
2. ✅ Testes end-to-end
3. ✅ Deploy em produção (após configurar providers externos)

**Próximo passo recomendado**: Integrar com frontend para completar o ciclo completo de alertas.

---

**Status Final**: 🎉 **BACKEND FASE 6 COMPLETO E OPERACIONAL** 🎉
