# ✅ Checklist de Validação - Fase 2

## 📋 Critérios de Aceitação

### 1. Modelos de Domínio

#### DeviceTemplate
- [ ] Modelo criado com campos: `code`, `name`, `version`, `superseded_by`, `description`
- [ ] Constraint `unique_device_template_code_version` aplicado
- [ ] Property `is_deprecated` funciona corretamente
- [ ] `__str__` mostra status [DEPRECIADO] quando aplicável

#### PointTemplate
- [ ] Modelo criado com FK para `DeviceTemplate`
- [ ] Tipos suportados: NUMERIC, BOOL, ENUM, TEXT
- [ ] Validação: `unit` só para NUMERIC
- [ ] Validação: `enum_values` obrigatório para ENUM
- [ ] Validação: `hysteresis` ≥ 0
- [ ] Constraint `unique_point_template_per_device` aplicado

#### Device
- [ ] Modelo criado com FK para `DeviceTemplate`
- [ ] Campos: `name`, `site_id`, `topic_base`, `credentials_id`, `status`
- [ ] Status: PENDING, ACTIVE, DECOMMISSIONED

#### Point
- [ ] Modelo criado com FK para `Device` e `PointTemplate`
- [ ] Campo `is_contracted` (boolean)
- [ ] Constraint `unique_point_per_device` aplicado

#### DashboardTemplate
- [ ] Modelo criado com FK para `DeviceTemplate`
- [ ] Campo `json` (JSONField)
- [ ] Validação JSON contra schema `dashboard_template_v1.json`
- [ ] Versionamento com `superseded_by`

#### DashboardConfig
- [ ] Modelo criado com OneToOne para `Device`
- [ ] Campo `json` (JSONField)
- [ ] Campo `template_version` (rastreabilidade)

---

### 2. Validações

- [ ] PointTemplate: `unit` rejeitado para não-NUMERIC
- [ ] PointTemplate: `enum_values` obrigatório para ENUM
- [ ] PointTemplate: `hysteresis` negativo rejeitado
- [ ] DashboardTemplate: JSON inválido rejeitado (schema validation)

---

### 3. Serviços

#### `provision_device_from_template(device, contracted_points=None)`
- [ ] Cria Points a partir de PointTemplates
- [ ] Aplica `is_contracted` corretamente
- [ ] Filtra por `contracted_points` quando fornecido
- [ ] Chama `instantiate_dashboard_config()`
- [ ] É idempotente (não duplica ao rodar 2x)

#### `instantiate_dashboard_config(device)`
- [ ] Busca DashboardTemplate mais recente
- [ ] Filtra painéis por pontos contratados
- [ ] Cria config vazio mas válido se sem template
- [ ] Usa `update_or_create` (idempotente)

---

### 4. Django Admin

#### DeviceTemplateAdmin
- [ ] Registrado no admin
- [ ] Inline de PointTemplate funciona
- [ ] Badge de status (ATIVO/DEPRECIADO) exibido
- [ ] Campos read-only quando depreciado
- [ ] Apenas `internal_ops` pode add/change/delete

#### PointTemplateAdmin
- [ ] Registrado no admin
- [ ] Apenas `internal_ops` pode add/change/delete

#### DeviceAdmin
- [ ] Registrado no admin
- [ ] Inline de Point (read-only) funciona
- [ ] `save_model()` chama `provision_device_from_template()`
- [ ] Mensagem de sucesso customizada exibida
- [ ] Apenas `internal_ops` pode add/delete

#### PointAdmin
- [ ] Registrado no admin
- [ ] Campos críticos read-only
- [ ] `has_add_permission()` retorna False

#### DashboardTemplateAdmin
- [ ] Registrado no admin
- [ ] Preview JSON formatado exibido
- [ ] Validação automática no save
- [ ] Apenas `internal_ops` pode add/change/delete

#### DashboardConfigAdmin
- [ ] Registrado no admin
- [ ] Preview JSON formatado exibido
- [ ] Read-only (gerado automaticamente)
- [ ] `has_add_permission()` retorna False

---

### 5. RBAC (Controle de Acesso)

#### Data Migration
- [ ] Migration `0002_rbac_groups.py` criada
- [ ] Grupos criados: `internal_ops`, `customer_admin`, `viewer`

#### Permissões
- [ ] `internal_ops`: CRUD completo em todos os modelos
- [ ] `customer_admin`: view apenas
- [ ] `viewer`: view apenas

#### Aplicação no Admin
- [ ] `internal_ops` vê botões de add/change/delete
- [ ] `customer_admin` e `viewer` não veem botões (403 ou hidden)

---

### 6. Seeds

#### `seed_device_templates`
- [ ] Command criado em `devices/management/commands/`
- [ ] Cria `inverter_v1_parsec` (v1) com 3 pontos
- [ ] Cria `chiller_v1` (v1) com 3 pontos
- [ ] É idempotente (não duplica ao rodar 2x)

#### `seed_dashboard_templates`
- [ ] Command criado em `dashboards/management/commands/`
- [ ] Cria dashboard para `inverter_v1_parsec` (4 painéis)
- [ ] Cria dashboard para `chiller_v1` (4 painéis)
- [ ] É idempotente

---

### 7. Testes

#### `test_templates_immutability.py`
- [ ] `test_create_device_template_v1` passa
- [ ] `test_create_new_version_and_deprecate_old` passa
- [ ] `test_unique_constraint_code_version` passa
- [ ] `test_point_template_validation_unit_only_numeric` passa
- [ ] `test_point_template_validation_enum_requires_values` passa
- [ ] `test_point_template_validation_hysteresis_non_negative` passa

#### `test_device_provisioning.py`
- [ ] `test_provision_device_creates_points` passa
- [ ] `test_provision_device_with_contracted_points` passa
- [ ] `test_provision_device_creates_dashboard_config` passa
- [ ] `test_dashboard_config_filters_by_contracted_points` passa
- [ ] `test_provision_idempotent` passa
- [ ] `test_dashboard_config_without_template` passa

---

### 8. Documentação

- [ ] README_FASE2.md criado e completo
- [ ] Instruções de uso claras
- [ ] Exemplos de código incluídos
- [ ] Troubleshooting documentado

---

## 🧪 Passos de Validação

### 1. Setup Inicial

```bash
# Instalar dependência
pip install jsonschema>=4.22

# Criar migrations
python manage.py makemigrations devices
python manage.py makemigrations dashboards

# Aplicar migrations
python manage.py migrate_schemas --shared
python manage.py migrate_schemas

# Criar seeds
python manage.py seed_device_templates
python manage.py seed_dashboard_templates
```

### 2. Verificar Modelos

```bash
python manage.py shell
```

```python
from apps.devices.models import DeviceTemplate, PointTemplate
from apps.dashboards.models import DashboardTemplate

# Verificar templates criados
DeviceTemplate.objects.all()
# <QuerySet [<DeviceTemplate: Inversor Parsec v1 (v1)>, <DeviceTemplate: Chiller v1 (v1)>]>

# Verificar pontos
template = DeviceTemplate.objects.get(code='inverter_v1_parsec')
template.point_templates.all()
# <QuerySet [<PointTemplate: inverter_v1_parsec.status (ENUM)>, ...]>

# Verificar dashboard
DashboardTemplate.objects.all()
# <QuerySet [<DashboardTemplate: Dashboard inverter_v1_parsec (v1)>, ...]>
```

### 3. Testar Provisionamento

```bash
python manage.py shell
```

```python
from apps.devices.models import Device, DeviceTemplate, Point
from apps.devices.services import provision_device_from_template
from apps.dashboards.models import DashboardConfig

# Criar device
template = DeviceTemplate.objects.get(code='inverter_v1_parsec', version=1)
device = Device.objects.create(
    template=template,
    name='Inversor 01 - Teste'
)

# Provisionar
provision_device_from_template(device)

# Verificar Points
Point.objects.filter(device=device).count()
# 3

# Verificar DashboardConfig
config = DashboardConfig.objects.get(device=device)
print(config.json)
# {'schema': 'v1', 'layout': 'cards-2col', 'panels': [...]}
```

### 4. Testar Validações

```python
from apps.devices.models import PointTemplate, PointType
from django.core.exceptions import ValidationError

# Tentar criar PointTemplate BOOL com unit (deve falhar)
pt = PointTemplate(
    device_template=template,
    name='test',
    label='Test',
    ptype=PointType.BOOL,
    unit='°C'  # INVÁLIDO
)

try:
    pt.full_clean()
except ValidationError as e:
    print("✅ Validação funcionou:", e)
```

### 5. Testar Admin

1. Criar superusuário:
   ```bash
   python manage.py createsuperuser
   ```

2. Adicionar ao grupo internal_ops:
   ```python
   from django.contrib.auth.models import User, Group
   user = User.objects.get(username='admin')
   group = Group.objects.get(name='internal_ops')
   user.groups.add(group)
   ```

3. Acessar admin:
   - Rodar: `python manage.py runserver`
   - Abrir: http://localhost:8000/admin/
   - Navegar para Devices → Device
   - Criar novo Device
   - Salvar e verificar mensagem de sucesso
   - Verificar que Points aparecem no inline

### 6. Executar Testes

```bash
# Todos os testes
pytest backend/tests/test_templates_immutability.py -v
pytest backend/tests/test_device_provisioning.py -v

# Teste específico
pytest backend/tests/test_device_provisioning.py::TestDeviceProvisioning::test_provision_device_creates_points -v
```

---

## ✅ Critério de Aceite Final

**A Fase 2 está completa quando:**

1. ✅ Todos os modelos criados e migrations aplicadas
2. ✅ Validações funcionam corretamente
3. ✅ Provisionamento automático funciona (Points + DashboardConfig)
4. ✅ RBAC aplicado no admin
5. ✅ Seeds executam sem erro
6. ✅ Todos os testes passam
7. ✅ Admin permite criar Device e ver provisionamento automático
8. ✅ Documentação completa

---

## 🐛 Problemas Comuns

### "No module named 'jsonschema'"
**Solução:** `pip install jsonschema>=4.22`

### "No such table: devices_devicetemplate"
**Solução:** `python manage.py migrate_schemas`

### "Group 'internal_ops' does not exist"
**Solução:** Executar migration RBAC ou criar manualmente

### Points não criados após salvar Device no admin
**Solução:** Verificar se `save_model()` no DeviceAdmin chama `provision_device_from_template()`

---

**Data de Validação:** _____________

**Validado por:** _____________

**Status:** [ ] Aprovado  [ ] Pendente  [ ] Reprovado

**Observações:**
