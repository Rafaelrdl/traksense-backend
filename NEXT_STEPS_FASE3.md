# PRÓXIMOS PASSOS — FASE 3

**Data:** 2025-10-07  
**Status Atual:** ✅ Implementação 100% | ⏸️ Validação 0% (Bloqueada)

---

## 🚨 Ação Imediata Necessária

### Problema Atual

Os arquivos de provisionamento foram criados localmente mas **não estão visíveis no container Docker** porque:

1. Container API não tem volume mapeado (código está na imagem)
2. Necessário **rebuild da imagem** para incluir novos arquivos
3. Imports Python falhando com `ModuleNotFoundError`

### Solução (Escolha uma)

#### Opção 1: Rebuild da Imagem (Recomendado)

```bash
# Parar containers
cd infra
docker compose down

# Rebuild da imagem API (sem cache)
docker compose build --no-cache api

# Subir containers
docker compose up -d

# Verificar se os imports funcionam
docker compose exec api python -c "from apps.devices.provisioning.factory import get_provisioner; print('✅ OK')"
```

**Vantagens:**
- Solução definitiva
- Imagem fica atualizada
- Funciona em qualquer ambiente

**Desvantagens:**
- Demora ~2-5 minutos

#### Opção 2: Adicionar Volume (Desenvolvimento)

```yaml
# Editar infra/docker-compose.yml
api:
  build: ../backend
  volumes:
    - ../backend:/app/backend  # ADICIONAR ESTA LINHA
  ports: ["8000:8000"]
  # ... resto da configuração
```

```bash
# Aplicar mudanças
cd infra
docker compose up -d api

# Verificar imports
docker compose exec api python -c "from apps.devices.provisioning.factory import get_provisioner; print('✅ OK')"
```

**Vantagens:**
- Mudanças instantâneas (sem rebuild)
- Ideal para desenvolvimento

**Desvantagens:**
- Não recomendado para produção
- Performance pode ser afetada no Windows

#### Opção 3: Copiar Arquivos Manualmente (Temporário)

```bash
cd infra

# Copiar diretório provisioning
docker cp ../backend/apps/devices/provisioning api:/app/backend/apps/devices/

# Copiar services.py atualizado
docker cp ../backend/apps/devices/services.py api:/app/backend/apps/devices/

# Copiar comando provision_emqx
docker cp ../backend/apps/devices/management/commands/provision_emqx.py api:/app/backend/apps/devices/management/commands/

# Reiniciar container
docker compose restart api

# Verificar imports
docker compose exec api python -c "from apps.devices.provisioning.factory import get_provisioner; print('✅ OK')"
```

**Vantagens:**
- Rápido (sem rebuild)

**Desvantagens:**
- Não persiste (se container for recriado, perde arquivos)
- Não é idempotente

---

## ✅ Após Resolver Imports

### 1. Validar Implementação (5 minutos)

```bash
cd infra

# Passo 1: Verificar arquivos criados
docker compose exec api ls -la /app/backend/apps/devices/provisioning/

# Passo 2: Testar Factory
docker compose exec api python << 'EOF'
import os
os.environ['EMQX_PROVISION_MODE'] = 'http'

from apps.devices.provisioning.factory import get_provisioner, reset_provisioner

prov1 = get_provisioner()
print(f"✅ Provisioner 1: {type(prov1).__name__}")

prov2 = get_provisioner()
assert prov1 is prov2, "❌ Singleton não funciona!"
print("✅ Singleton OK")

reset_provisioner()
prov3 = get_provisioner()
assert prov1 is not prov3, "❌ Reset não funciona!"
print("✅ Reset OK")

print("\n✅ Todos os testes do factory passaram!")
EOF
```

**Resultado Esperado:**
```
✅ Provisioner 1: EmqxHttpProvisioner
✅ Singleton OK
✅ Reset OK
✅ Todos os testes do factory passaram!
```

### 2. Provisionar Device (10 minutos)

```bash
# Obter ID de um device existente
DEVICE_ID=$(docker compose exec api python manage.py tenant_command shell --schema=test_alpha -c "from apps.devices.models import Device; print(Device.objects.first().id)")

echo "Device ID: $DEVICE_ID"

# Provisionar device no EMQX
docker compose exec api python manage.py tenant_command provision_emqx $DEVICE_ID factory-sp --schema=test_alpha
```

**Resultado Esperado:**
```
✅ Device provisionado com sucesso!

MQTT Connection Info:
  Host:     emqx.local
  Port:     1883
  ClientID: ts-xxxxxxxx-yyyyyyyy-zzzzzzzz
  Username: t:<tenant_uuid>:d:<device_uuid>
  Password: <20+ caracteres>  ⚠️ SALVE COM SEGURANÇA!

Topics (Publish):
  - traksense/<tenant>/<site>/<device>/state
  - traksense/<tenant>/<site>/<device>/telem
  - traksense/<tenant>/<site>/<device>/event
  - traksense/<tenant>/<site>/<device>/alarm
  - traksense/<tenant>/<site>/<device>/ack

Topics (Subscribe):
  - traksense/<tenant>/<site>/<device>/cmd

LWT (Last Will Testament):
  Topic:   traksense/<tenant>/<site>/<device>/state
  Retain:  True
  QoS:     1
  Payload: {"online": false, "ts": "<timestamp>"}
```

**⚠️ IMPORTANTE:** Salvar credenciais exibidas para os próximos testes!

```powershell
# Salvar temporariamente (PowerShell)
$env:MQTT_HOST = "localhost"
$env:MQTT_PORT = "1883"
$env:MQTT_CLIENT_ID = "ts-xxxxxxxx-yyyyyyyy-zzzzzzzz"
$env:MQTT_USERNAME = "t:<tenant_uuid>:d:<device_uuid>"
$env:MQTT_PASSWORD = "<senha_gerada>"
$env:MQTT_TOPIC_BASE = "traksense/<tenant>/<site>/<device>"
```

### 3. Validar Usuário no EMQX (5 minutos)

```bash
# Consultar usuário via API do EMQX
curl -u admin:public http://localhost:18083/api/v5/authentication/password_based:built_in_database/users/$MQTT_USERNAME

# Consultar ACLs do usuário (6 regras esperadas)
curl -u admin:public "http://localhost:18083/api/v5/authorization/sources/built_in_database/rules?username=$MQTT_USERNAME"
```

**Dashboard Web:**
1. Acessar: http://localhost:18083
2. Login: admin / public
3. Menu: **Authentication** → **Password-Based** → **Built-in Database**
4. Buscar usuário: `t:<tenant_uuid>:d:<device_uuid>`
5. Menu: **Authorization** → **Built-in Database** → **Rules**
6. Verificar **6 regras** do usuário (5 publish + 1 subscribe)

### 4. Executar Testes MQTT (30 minutos)

Seguir **VALIDATION_CHECKLIST_FASE3.md** — Passos 5 a 10:

```bash
# Instalar paho-mqtt no container
docker compose exec api pip install paho-mqtt

# Passo 5: Teste de publish autorizado
docker compose exec api python /app/backend/test_mqtt_authorized_publish.py

# Passo 6: Teste de subscribe autorizado
docker compose exec api python /app/backend/test_mqtt_authorized_subscribe.py

# Passo 7: Teste de publish NÃO autorizado (negação esperada)
docker compose exec api python /app/backend/test_mqtt_unauthorized_publish.py

# Passo 8: Teste de subscribe wildcard negado (SUBACK 0x80)
docker compose exec api python /app/backend/test_mqtt_unauthorized_subscribe.py

# Passo 9: Teste de LWT
docker compose exec api python /app/backend/test_mqtt_lwt.py

# Passo 10: Verificar logs do EMQX
docker compose logs emqx | grep -i "authorization_denied\|not_authorized"
```

**Scripts de Teste:** Todos os scripts estão documentados no `VALIDATION_CHECKLIST_FASE3.md` (Passos 5-9).

Copie cada script do checklist e salve como:
- `backend/test_mqtt_authorized_publish.py`
- `backend/test_mqtt_authorized_subscribe.py`
- `backend/test_mqtt_unauthorized_publish.py`
- `backend/test_mqtt_unauthorized_subscribe.py`
- `backend/test_mqtt_lwt.py`

### 5. Documentar Resultados

Criar arquivo `VALIDATION_REPORT_FASE3.md` com:

```markdown
# Relatório de Validação — Fase 3

**Data:** 2025-10-XX
**Executado por:** [Seu Nome]
**Ambiente:** Docker Compose (desenvolvimento)

## Resultados

| Passo | Teste | Status | Observações |
|-------|-------|--------|-------------|
| 1 | Implementação das classes | ✅ / ❌ | ... |
| 2 | Factory e Singleton | ✅ / ❌ | ... |
| 3 | Provisionar device | ✅ / ❌ | Device ID: ... |
| 4 | Validar usuário no EMQX | ✅ / ❌ | 6 regras criadas |
| 5 | Publish autorizado | ✅ / ❌ | 5 tópicos OK |
| 6 | Subscribe autorizado | ✅ / ❌ | 1 tópico OK |
| 7 | Publish não autorizado | ✅ / ❌ | Desconexão esperada |
| 8 | Subscribe wildcard negado | ✅ / ❌ | SUBACK 0x80 |
| 9 | LWT | ✅ / ❌ | Retain OK |
| 10 | Logs de auditoria | ✅ / ❌ | Tentativas negadas logadas |

## Critérios de Aceite

- [ ] Existe script/endpoint de provisionamento funcional
- [ ] Cliente MQTT publica apenas em tópicos autorizados
- [ ] Cliente MQTT assina apenas em tópicos autorizados
- [ ] Tentativas fora do prefixo são negadas
- [ ] Logs do EMQX evidenciam tentativas negadas
- [ ] ClientID único é gerado
- [ ] LWT configurado e testado

## Conclusão

[Descrever se a Fase 3 está aprovada ou se há pendências]
```

---

## 🎯 Implementações Opcionais

### Endpoint DRF (Opcional)

Criar `backend/apps/devices/views.py` (se não existir) ou adicionar ao existente:

```python
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Device
from .services import provision_emqx_for_device
from .serializers import DeviceSerializer


class IsInternalOps(IsAuthenticated):
    """Permissão: apenas internal_ops pode provisionar devices"""
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.groups.filter(name='internal_ops').exists()


class DeviceViewSet(viewsets.ModelViewSet):
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=True, methods=['post'], permission_classes=[IsInternalOps])
    def provision(self, request, pk=None):
        """
        Provisiona credenciais MQTT no EMQX para o device.
        
        POST /api/devices/{id}/provision/
        Body: {"site_slug": "factory-sp"}
        
        Returns:
            {
                "mqtt": {"host": "...", "port": 1883, ...},
                "topics": {"publish": [...], "subscribe": [...]},
                "lwt": {"topic": "...", "retain": true, ...}
            }
        """
        device = self.get_object()
        site_slug = request.data.get('site_slug')
        
        if not site_slug:
            return Response(
                {"error": "Campo 'site_slug' é obrigatório"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            mqtt_info = provision_emqx_for_device(device, site_slug)
            return Response(mqtt_info, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
```

Registrar viewset em `backend/core/urls.py`:

```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.devices.views import DeviceViewSet

router = DefaultRouter()
router.register(r'devices', DeviceViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
    # ... outras rotas
]
```

Testar:

```bash
# Obter token de autenticação (se usar JWT)
TOKEN="seu_token_aqui"

# Provisionar device via API
curl -X POST http://localhost:8000/api/devices/<device_id>/provision/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"site_slug": "factory-sp"}'
```

### Django Admin Action (Opcional)

Editar `backend/apps/devices/admin.py`:

```python
from django.contrib import admin, messages
from django.shortcuts import render
from .models import Device
from .services import provision_emqx_for_device


class ProvisionForm(forms.Form):
    """Form intermediário para pedir site_slug"""
    site_slug = forms.CharField(
        max_length=50,
        help_text="Slug do site (ex: factory-sp, sala-a)"
    )


@admin.action(description='Provisionar EMQX (gerar credenciais MQTT)')
def provision_devices_action(modeladmin, request, queryset):
    """
    Admin action para provisionar devices selecionados no EMQX.
    
    Uso:
        1. Selecionar devices no Django Admin
        2. Ações → "Provisionar EMQX"
        3. Preencher site_slug
        4. Confirmar
    """
    # Se form não foi submetido, mostrar form intermediário
    if 'apply' not in request.POST:
        return render(
            request,
            'admin/provision_confirmation.html',
            {
                'devices': queryset,
                'form': ProvisionForm(),
                'title': 'Provisionar Devices no EMQX',
            }
        )
    
    # Form submetido: provisionar devices
    form = ProvisionForm(request.POST)
    if not form.is_valid():
        modeladmin.message_user(request, "Site slug inválido", level=messages.ERROR)
        return
    
    site_slug = form.cleaned_data['site_slug']
    success_count = 0
    error_count = 0
    
    for device in queryset:
        try:
            mqtt_info = provision_emqx_for_device(device, site_slug)
            success_count += 1
            
            # Logar senha (⚠️ apenas em dev!)
            password = mqtt_info['mqtt']['password']
            modeladmin.message_user(
                request,
                f"✅ Device {device.id} provisionado! Password: {password}",
                level=messages.SUCCESS
            )
        except Exception as e:
            error_count += 1
            modeladmin.message_user(
                request,
                f"❌ Falha ao provisionar Device {device.id}: {e}",
                level=messages.ERROR
            )
    
    modeladmin.message_user(
        request,
        f"Provisionamento concluído: {success_count} sucessos, {error_count} falhas",
        level=messages.INFO
    )


class DeviceAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'template', 'credentials_id', 'topic_base']
    actions = [provision_devices_action]
    
    readonly_fields = ['credentials_id', 'topic_base']  # Não editar manualmente


admin.site.register(Device, DeviceAdmin)
```

Criar template `backend/templates/admin/provision_confirmation.html`:

```html
{% extends "admin/base_site.html" %}

{% block content %}
<h1>{{ title }}</h1>

<p>Você está prestes a provisionar <strong>{{ devices|length }}</strong> device(s) no EMQX:</p>

<ul>
    {% for device in devices %}
    <li>{{ device.name }} (ID: {{ device.id }})</li>
    {% endfor %}
</ul>

<form method="post">
    {% csrf_token %}
    {{ form.as_p }}
    
    <input type="hidden" name="action" value="provision_devices_action">
    <input type="hidden" name="_selected_action" value="{{ devices|join:',' }}">
    
    <button type="submit" name="apply" class="default">Provisionar</button>
    <a href="{% url 'admin:devices_device_changelist' %}" class="button">Cancelar</a>
</form>

<p><strong>⚠️ ATENÇÃO:</strong> As senhas geradas serão exibidas apenas 1x. Salve com segurança!</p>
{% endblock %}
```

---

## 🐛 Troubleshooting

### Problema: "curl não funciona no Windows"

**Solução:** Usar PowerShell com `Invoke-WebRequest`:

```powershell
$headers = @{ Authorization = "Basic " + [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("admin:public")) }

Invoke-WebRequest -Uri "http://localhost:18083/api/v5/status" -Headers $headers
```

### Problema: "paho-mqtt não instalado"

```bash
docker compose exec api pip install paho-mqtt

# Ou adicionar ao requirements.txt:
echo "paho-mqtt>=2.0.0" >> backend/requirements.txt
docker compose build --no-cache api
```

### Problema: "EMQX retorna 401 Unauthorized"

Verificar credenciais:

```bash
docker compose exec api python -c "import os; print('User:', os.getenv('EMQX_ADMIN_USER')); print('Pass:', os.getenv('EMQX_ADMIN_PASS'))"
```

Resetar senha do admin no EMQX:

```bash
docker compose exec emqx emqx_ctl admins passwd admin new_password
```

Atualizar `.env.api`:

```bash
EMQX_ADMIN_PASS=new_password
```

---

## 📚 Documentação de Referência

- [SUMMARY_FASE3.md](./SUMMARY_FASE3.md) — Sumário da implementação
- [VALIDATION_CHECKLIST_FASE3.md](./VALIDATION_CHECKLIST_FASE3.md) — Checklist detalhado (10 passos)
- [README_FASE3.md](./README_FASE3.md) — Documentação completa
- [ADR-003](./docs/adr/ADR-003-emqx-authz.md) — Decisão arquitetural

---

## ✅ Checklist de Continuidade

- [ ] **Resolver imports** (rebuild da imagem ou adicionar volume)
- [ ] **Executar validações** (Passos 1-10 do checklist)
- [ ] **Documentar resultados** (criar VALIDATION_REPORT_FASE3.md)
- [ ] **Implementar opcionais** (endpoint DRF, admin action)
- [ ] **Converter testes para pytest** (automatizar validações)
- [ ] **Avançar para Fase 4** (ingest assíncrono, adapters, TimescaleDB)

---

**Última Atualização:** 2025-10-07 21:05 BRT  
**Próxima Ação:** Rebuild da imagem API para carregar arquivos de provisionamento
