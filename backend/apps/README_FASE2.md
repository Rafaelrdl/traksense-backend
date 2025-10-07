# Fase 2 - Modelos de Domínio & Admin Interno

## 📋 Visão Geral

A Fase 2 implementa os modelos de domínio completos para dispositivos IoT e dashboards, com:

- **Templates imutáveis** (versionamento)
- **Provisionamento automático** de Points e DashboardConfig
- **RBAC** (controle de acesso por grupos)
- **Validações** de negócio
- **Django Admin** customizado para operações internas

## 🏗️ Arquitetura

```
DeviceTemplate (v1, v2, ...) → Device (instância)
    ↓ 1:N                         ↓ 1:N
PointTemplate                   Point (contratado/não contratado)

DashboardTemplate (v1, v2, ...) → DashboardConfig (JSON filtrado)
    ↓ vinculado a DeviceTemplate     ↓ vinculado a Device
```

## 📦 Modelos Implementados

### Devices App (`apps.devices`)

#### DeviceTemplate
- **Propósito**: Define um tipo/família de equipamento (ex: `inverter_v1_parsec`)
- **Campos principais**:
  - `code`: slug único (ex: `inverter_v1_parsec`)
  - `version`: número de versão (incrementa a cada mudança)
  - `superseded_by`: FK para versão mais nova (se depreciada)
- **Imutabilidade**: Nunca alterar templates publicados; criar nova versão

#### PointTemplate
- **Propósito**: Define um ponto de telemetria padrão (ex: `temp_agua`)
- **Tipos suportados**: NUMERIC, BOOL, ENUM, TEXT
- **Validações**:
  - `unit` só para NUMERIC
  - `enum_values` obrigatório para ENUM
  - `hysteresis` ≥ 0

#### Device
- **Propósito**: Instância física de equipamento
- **Provisionamento**: Ao criar, chama `provision_device_from_template()` para gerar Points e DashboardConfig
- **Status**: PENDING → ACTIVE → DECOMMISSIONED

#### Point
- **Propósito**: Ponto de telemetria específico de um Device
- **is_contracted**: Define se o ponto está ativo (aparece em dashboards)

### Dashboards App (`apps.dashboards`)

#### DashboardTemplate
- **Propósito**: Define estrutura de painéis para um DeviceTemplate
- **Validação**: JSON validado contra `dashboard_template_v1.json` schema
- **Painéis suportados**: timeseries, status, timeline, kpi, button

#### DashboardConfig
- **Propósito**: Config instanciada para um Device específico
- **Filtragem**: Apenas pontos contratados aparecem nos painéis
- **Geração**: Automática via `instantiate_dashboard_config()`

## 🔧 Serviços

### `devices.services.provision_device_from_template(device, contracted_points=None)`

Provisiona um Device criando:
1. **Points** a partir dos PointTemplates
2. **DashboardConfig** filtrado por pontos contratados

**Exemplo:**
```python
from devices.models import Device, DeviceTemplate
from devices.services import provision_device_from_template

template = DeviceTemplate.objects.get(code='inverter_v1_parsec', version=1)
device = Device.objects.create(template=template, name='Inversor 01')

# Provisionar todos os pontos
provision_device_from_template(device)

# Ou apenas alguns pontos
provision_device_from_template(device, contracted_points=['status', 'fault'])
```

### `dashboards.services.instantiate_dashboard_config(device)`

Cria DashboardConfig filtrando painéis por pontos contratados.

Chamado automaticamente por `provision_device_from_template()`.

## 🔐 RBAC (Controle de Acesso)

### Grupos Criados

| Grupo | Permissões | Uso |
|-------|-----------|-----|
| `internal_ops` | CRUD completo | Operações internas (criar templates, devices) |
| `customer_admin` | View apenas | Cliente admin (visualizar, futuramente editar limits) |
| `viewer` | View apenas | Cliente visualizador |

### Aplicação no Admin

- **DeviceTemplate/PointTemplate/DashboardTemplate**: Apenas `internal_ops` pode criar/editar
- **Device**: Apenas `internal_ops` pode criar
- **Point**: Criado automaticamente; `internal_ops` pode editar
- **DashboardConfig**: Read-only (gerado automaticamente)

## 🌱 Seeds (Dados Iniciais)

### 1. Seed Device Templates

```bash
python manage.py seed_device_templates
```

Cria:
- **inverter_v1_parsec**: status (ENUM), fault (BOOL), rssi (NUMERIC dBm)
- **chiller_v1**: temp_agua (NUMERIC °C), unit_state (ENUM), compressor_1_on (BOOL)

### 2. Seed Dashboard Templates

```bash
python manage.py seed_dashboard_templates
```

Cria dashboards para:
- **inverter_v1_parsec**: status, timeline, KPI falhas, RSSI
- **chiller_v1**: temperatura, status, KPI compressor, timeline

## 🧪 Testes

### Executar Testes

```bash
pytest backend/tests/test_templates_immutability.py -v
pytest backend/tests/test_device_provisioning.py -v
```

### Cenários Testados

#### `test_templates_immutability.py`
- ✅ Criar DeviceTemplate com versionamento
- ✅ Criar nova versão e depreciar antiga
- ✅ Constraint (code, version) único
- ✅ Validações de PointTemplate (unit, enum_values, hysteresis)

#### `test_device_provisioning.py`
- ✅ Provisionar Device cria Points automaticamente
- ✅ Provisionar apenas pontos contratados
- ✅ DashboardConfig gerado com JSON válido
- ✅ Painéis filtrados por pontos contratados
- ✅ Provisionamento idempotente (não duplica)

## 📋 Checklist de Entrega

- ✅ Modelos e migrações (DeviceTemplate, PointTemplate, Device, Point, DashboardTemplate, DashboardConfig)
- ✅ Regras de imutabilidade (version + superseded_by)
- ✅ Validações (unit/enum/polarity/hysteresis) e validador JSON
- ✅ Serviço `provision_device_from_template` + `instantiate_dashboard_config`
- ✅ Admin: inlines, read-only quando superseded, provisionamento automático no save_model
- ✅ Data migration para grupos/permissões (internal_ops, customer_admin, viewer)
- ✅ Seeds de templates (inverter_v1_parsec, chiller_v1)
- ✅ Testes: imutabilidade, provisionamento, RBAC
- ✅ README atualizado

## 🚀 Como Usar

### 1. Executar Migrações

```bash
# Migrar schema public (shared apps)
python manage.py migrate_schemas --shared

# Migrar todos os schemas de tenants
python manage.py migrate_schemas
```

### 2. Criar Dados Iniciais

```bash
# Criar templates de devices
python manage.py seed_device_templates

# Criar templates de dashboards
python manage.py seed_dashboard_templates
```

### 3. Criar Usuário Admin

```bash
python manage.py createsuperuser
```

### 4. Adicionar Usuário a Grupo

```python
from django.contrib.auth.models import User, Group

user = User.objects.get(username='admin')
internal_ops = Group.objects.get(name='internal_ops')
user.groups.add(internal_ops)
```

### 5. Acessar Django Admin

1. Rodar servidor: `python manage.py runserver`
2. Acessar: http://localhost:8000/admin/
3. Navegar para **Devices** → **Device**
4. Criar novo Device selecionando um template
5. Salvar → Points e DashboardConfig são gerados automaticamente!

### 6. Verificar Provisionamento

```python
from devices.models import Device, Point
from dashboards.models import DashboardConfig

device = Device.objects.get(name='Inversor 01')

# Ver Points gerados
print(device.points.all())

# Ver DashboardConfig
print(device.dashboard_config.json)
```

## 📁 Estrutura de Arquivos

```
backend/
├── apps/
│   ├── devices/
│   │   ├── models.py              # DeviceTemplate, PointTemplate, Device, Point
│   │   ├── admin.py               # Admin customizado com RBAC
│   │   ├── services.py            # provision_device_from_template()
│   │   ├── migrations/
│   │   │   ├── 0001_initial.py
│   │   │   └── 0002_rbac_groups.py  # Data migration para grupos
│   │   └── management/
│   │       └── commands/
│   │           └── seed_device_templates.py
│   └── dashboards/
│       ├── models.py              # DashboardTemplate, DashboardConfig
│       ├── admin.py               # Admin customizado
│       ├── services.py            # instantiate_dashboard_config()
│       ├── validators.py          # Validação JSON Schema
│       ├── schema/
│       │   └── dashboard_template_v1.json
│       └── management/
│           └── commands/
│               └── seed_dashboard_templates.py
└── tests/
    ├── test_templates_immutability.py
    └── test_device_provisioning.py
```

## 🔮 Próximas Fases

### Fase 3: Provisionamento EMQX
- Gerar credenciais MQTT para cada Device
- Configurar ACLs no EMQX
- Publicar LWT (Last Will and Testament)

### Fase 4: Ingest Assíncrono
- Serviço Python para consumir MQTT
- Validação de payloads (adapters por vendor)
- Persistência em TimescaleDB

### Fase 5: APIs DRF
- GET /api/devices/
- GET /api/dashboards/{device_id}
- GET /api/data/points (séries temporais)
- POST /api/cmd/{device_id} (comandos)

## 📝 Notas Importantes

### Imutabilidade de Templates

❌ **NÃO FAZER:**
```python
template = DeviceTemplate.objects.get(code='inverter_v1_parsec', version=1)
template.name = 'Novo nome'  # EVITAR se já está publicado!
template.save()
```

✅ **FAZER:**
```python
# Criar nova versão
v2 = DeviceTemplate.objects.create(
    code='inverter_v1_parsec',
    name='Inversor Parsec v2',
    version=2
)

# Depreciar v1
v1 = DeviceTemplate.objects.get(code='inverter_v1_parsec', version=1)
v1.superseded_by = v2
v1.save()
```

### Provisionamento Manual vs Automático

O provisionamento é **automático** no Django Admin (via `save_model`), mas **manual** via shell/código:

```python
# No shell, sempre chamar explicitamente:
device = Device.objects.create(...)
provision_device_from_template(device)
```

### JSON Schema Validation

DashboardTemplate valida automaticamente no `clean()`:

```python
# Válido
dashboard = DashboardTemplate(
    device_template=template,
    json={
        "schema": "v1",
        "layout": "cards-2col",
        "panels": [...]
    }
)
dashboard.full_clean()  # OK

# Inválido
dashboard = DashboardTemplate(
    device_template=template,
    json={"invalid": "structure"}
)
dashboard.full_clean()  # ValidationError!
```

## 🐛 Troubleshooting

### Erro: "No such table: devices_devicetemplate"

**Solução:** Executar migrações
```bash
python manage.py migrate_schemas
```

### Erro: "Group 'internal_ops' does not exist"

**Solução:** Executar data migration
```bash
python manage.py migrate_schemas
```

### Points não foram criados após salvar Device

**Solução:** Verificar se `provision_device_from_template()` foi chamado. No Admin é automático, mas via shell é manual.

### DashboardConfig está vazio

**Solução:** Verificar se DashboardTemplate existe para o DeviceTemplate. Se não, será criado config vazio.

---

**Desenvolvido por:** TrakSense Team  
**Data:** 2025-10-07  
**Fase:** 2/6
