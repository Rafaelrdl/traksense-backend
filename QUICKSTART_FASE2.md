# 🚀 Guia Rápido - Fase 2

## Setup Completo (Uma Linha)

### Windows (PowerShell)
```powershell
.\setup_fase2.ps1
```

### Linux/Mac
```bash
python setup_fase2.py
```

---

## Comandos Individuais

### 1. Instalar Dependências
```bash
pip install jsonschema>=4.22
```

### 2. Criar Migrations
```bash
python manage.py makemigrations devices
python manage.py makemigrations dashboards
```

### 3. Aplicar Migrations
```bash
# Shared apps (public schema)
python manage.py migrate_schemas --shared

# Tenant apps (todos os schemas)
python manage.py migrate_schemas
```

### 4. Criar Templates Iniciais
```bash
# Device templates
python manage.py seed_device_templates

# Dashboard templates
python manage.py seed_dashboard_templates
```

### 5. Criar Superusuário
```bash
python manage.py createsuperuser
```

### 6. Adicionar Usuário a Grupo
```bash
python manage.py shell
```
```python
from django.contrib.auth.models import User, Group

user = User.objects.get(username='admin')
group = Group.objects.get(name='internal_ops')
user.groups.add(group)
```

### 7. Rodar Servidor
```bash
python manage.py runserver
```
Acessar: http://localhost:8000/admin/

---

## Testes

### Executar Todos os Testes
```bash
pytest backend/tests/test_templates_immutability.py -v
pytest backend/tests/test_device_provisioning.py -v
```

### Teste Específico
```bash
pytest backend/tests/test_device_provisioning.py::TestDeviceProvisioning::test_provision_device_creates_points -v
```

---

## Exemplos de Uso (Shell)

### Criar Device e Provisionar
```python
from apps.devices.models import Device, DeviceTemplate
from apps.devices.services import provision_device_from_template

# Buscar template
template = DeviceTemplate.objects.get(code='inverter_v1_parsec', version=1)

# Criar device
device = Device.objects.create(
    template=template,
    name='Inversor 01 - Sala A'
)

# Provisionar (criar Points e DashboardConfig)
provision_device_from_template(device)

# Verificar Points
print(device.points.all())

# Verificar DashboardConfig
print(device.dashboard_config.json)
```

### Provisionar Apenas Alguns Pontos
```python
# Provisionar apenas 'status' e 'fault'
provision_device_from_template(device, contracted_points=['status', 'fault'])
```

### Criar Nova Versão de Template
```python
from apps.devices.models import DeviceTemplate

# Buscar v1
v1 = DeviceTemplate.objects.get(code='inverter_v1_parsec', version=1)

# Criar v2
v2 = DeviceTemplate.objects.create(
    code='inverter_v1_parsec',
    name='Inversor Parsec v2',
    version=2,
    description='Nova versão com melhorias'
)

# Depreciar v1
v1.superseded_by = v2
v1.save()
```

---

## Troubleshooting Rápido

### Erro: "No such table"
```bash
python manage.py migrate_schemas
```

### Erro: "Group 'internal_ops' does not exist"
```bash
# Reexecutar migration RBAC
python manage.py migrate_schemas
```

### Points não criados
```python
# Provisionar manualmente
from apps.devices.services import provision_device_from_template
provision_device_from_template(device)
```

---

## Links Úteis

- 📖 **Documentação completa**: `backend/apps/README_FASE2.md`
- ✅ **Checklist de validação**: `VALIDATION_CHECKLIST_FASE2.md`
- 📊 **Sumário da implementação**: `SUMMARY_FASE2.md`

---

## Fluxo de Trabalho Típico

1. **Setup inicial** (uma vez)
   ```bash
   .\setup_fase2.ps1
   python manage.py createsuperuser
   ```

2. **Criar usuário interno** (shell)
   ```python
   from django.contrib.auth.models import User, Group
   user = User.objects.get(username='admin')
   user.groups.add(Group.objects.get(name='internal_ops'))
   ```

3. **Acessar admin**
   ```bash
   python manage.py runserver
   # Abrir: http://localhost:8000/admin/
   ```

4. **Criar Device no admin**
   - Navegar para: Devices → Device → Add
   - Selecionar template: `inverter_v1_parsec`
   - Nome: "Inversor 01"
   - Salvar
   - ✅ Points e DashboardConfig criados automaticamente!

5. **Verificar provisionamento** (shell)
   ```python
   from apps.devices.models import Device
   device = Device.objects.get(name='Inversor 01')
   print(device.points.count())  # 3
   print(device.dashboard_config.json)  # {...}
   ```

---

**Pronto para produção!** 🎉
