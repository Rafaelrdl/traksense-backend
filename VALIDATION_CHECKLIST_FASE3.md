# VALIDATION_CHECKLIST_FASE3.md

# ✅ Checklist de Validação — Fase 3: EMQX AuthN/ACL & Provisioning

**Status:** 🟡 EM ANDAMENTO  
**Data de Criação:** 2025-10-07  
**Responsável:** Time TrakSense  
**Objetivo:** Validar provisionamento de devices IoT no EMQX com autenticação e autorização mínima

---

## 📋 Visão Geral

A Fase 3 implementa o provisionamento de credenciais MQTT no broker EMQX para dispositivos IoT, garantindo:

- **Autenticação (AuthN):** Cada device tem username/password únicos
- **Autorização (AuthZ):** ACL mínima — device só acessa seus próprios tópicos
- **Segurança:** Sem wildcards perigosos (#, +) fora do prefixo do device
- **Isolamento multi-tenant:** Devices de um tenant não acessam tópicos de outros

### Critérios de Aceite (Refinados do Prompt)

1. ✅ Existe script/endpoint de provisionamento que cria usuário no EMQX e configura ACL mínima
2. ⬜ Cliente MQTT publica apenas em: `traksense/{tenant}/{site}/{device}/(state|telem|event|alarm|ack)`
3. ⬜ Cliente MQTT assina apenas em: `traksense/{tenant}/{site}/{device}/cmd`
4. ⬜ Tentativa fora do prefixo resulta em negação (SUBACK 0x80 ou desconexão)
5. ⬜ Logs no EMQX evidenciam tentativas negadas
6. ⬜ ClientID único por device é gerado e documentado
7. ⬜ LWT configurado no device (documentação + teste de verificação via retain em state)

---

## 🛠️ Pré-requisitos

### 1. Ambiente

- Docker Compose com 4 containers UP: `emqx`, `db`, `redis`, `api`
- EMQX acessível em: http://localhost:18083 (dashboard) e tcp://localhost:1883 (MQTT)
- Backend Django rodando com variáveis de ambiente configuradas

### 2. Variáveis de Ambiente (`.env.api`)

```bash
# Verificar se estão definidas:
EMQX_MGMT_URL=http://emqx:18083
EMQX_ADMIN_USER=admin
EMQX_ADMIN_PASS=public
EMQX_REALM=traksense
EMQX_PROVISION_MODE=http
```

**Validação:**

```bash
docker compose exec api sh -c 'echo $EMQX_MGMT_URL'
# Esperado: http://emqx:18083
```

### 3. Tenant e Device de Teste

```bash
# Conectar no Django shell (tenant test_alpha):
docker compose exec api python manage.py tenant_command shell --schema=test_alpha

# Buscar device existente (criado na Fase 2):
from apps.devices.models import Device
device = Device.objects.first()
print(f"Device ID: {device.id}")
print(f"Device Name: {device.name}")
print(f"Template: {device.template.code}")
# Guardar device_id para os testes
```

### 4. Dependências Python

Adicionar ao `backend/requirements.txt`:

```
requests>=2.31.0
urllib3>=2.0.0
paho-mqtt>=2.0.0  # Para testes de integração
```

Instalar:

```bash
docker compose exec api pip install paho-mqtt
```

---

## 📝 Passos de Validação

### Passo 1: Validar Implementação das Classes

**Objetivo:** Verificar que todas as classes e funções foram implementadas corretamente.

**Checklist:**

- [ ] 1.1. Arquivo `backend/apps/devices/provisioning/__init__.py` existe com `EmqxProvisioner` e `EmqxCredentials`
- [ ] 1.2. Arquivo `backend/apps/devices/provisioning/emqx.py` existe (re-exports)
- [ ] 1.3. Arquivo `backend/apps/devices/provisioning/emqx_http.py` existe com `EmqxHttpProvisioner`
- [ ] 1.4. Arquivo `backend/apps/devices/provisioning/emqx_sql.py` existe (skeleton com NotImplementedError)
- [ ] 1.5. Arquivo `backend/apps/devices/provisioning/factory.py` existe com `get_provisioner()`
- [ ] 1.6. Arquivo `backend/apps/devices/services.py` contém `generate_client_id()` e `provision_emqx_for_device()`
- [ ] 1.7. Arquivo `backend/apps/devices/management/commands/provision_emqx.py` existe

**Comandos:**

```bash
# Verificar arquivos:
docker compose exec api ls -la /app/backend/apps/devices/provisioning/
docker compose exec api ls -la /app/backend/apps/devices/management/commands/provision_emqx.py

# Testar imports:
docker compose exec api python -c "from apps.devices.provisioning.factory import get_provisioner; print('✅ Import OK')"
docker compose exec api python -c "from apps.devices.services import provision_emqx_for_device; print('✅ Import OK')"
```

**Resultado Esperado:**

```
✅ Todos os imports bem-sucedidos, sem erros de sintaxe ou import
```

---

### Passo 2: Validar Factory e Singleton

**Objetivo:** Verificar que o Factory retorna a implementação correta e usa singleton.

**Checklist:**

- [ ] 2.1. `get_provisioner()` retorna `EmqxHttpProvisioner` quando `EMQX_PROVISION_MODE=http`
- [ ] 2.2. `get_provisioner()` levanta `ValueError` quando `EMQX_PROVISION_MODE=sql` (não implementado)
- [ ] 2.3. Singleton funciona (mesma instância reutilizada)
- [ ] 2.4. `reset_provisioner()` força recriação

**Comandos:**

```bash
# Testar factory via Python:
docker compose exec api python << 'EOF'
import os
os.environ['EMQX_PROVISION_MODE'] = 'http'

from apps.devices.provisioning.factory import get_provisioner, reset_provisioner

# Teste 1: Obter provisioner
prov1 = get_provisioner()
print(f"✅ Provisioner 1: {type(prov1).__name__}")

# Teste 2: Singleton (mesma instância)
prov2 = get_provisioner()
assert prov1 is prov2, "❌ Singleton não funciona!"
print("✅ Singleton OK (mesma instância)")

# Teste 3: Reset
reset_provisioner()
prov3 = get_provisioner()
assert prov1 is not prov3, "❌ Reset não funciona!"
print("✅ Reset OK (nova instância)")

print("\n✅ Todos os testes do factory passaram!")
EOF
```

**Resultado Esperado:**

```
✅ Provisioner 1: EmqxHttpProvisioner
✅ Singleton OK (mesma instância)
✅ Reset OK (nova instância)
✅ Todos os testes do factory passaram!
```

---

### Passo 3: Provisionar Device via Management Command

**Objetivo:** Executar provisionamento completo de um device e obter credenciais MQTT.

**Checklist:**

- [ ] 3.1. Comando `provision_emqx` executa sem erros
- [ ] 3.2. Credenciais MQTT são geradas (username, password, client_id)
- [ ] 3.3. Device.credentials_id é atualizado no banco
- [ ] 3.4. Device.topic_base é atualizado no banco
- [ ] 3.5. Username segue formato: `t:<tenant_uuid>:d:<device_uuid>`
- [ ] 3.6. ClientID segue formato: `ts-<tenant_short>-<device_short>-<random>`
- [ ] 3.7. Password tem mínimo 20 caracteres

**Comandos:**

```bash
# Obter device_id do tenant test_alpha:
DEVICE_ID=$(docker compose exec api python manage.py tenant_command shell --schema=test_alpha -c "from apps.devices.models import Device; print(Device.objects.first().id)")

echo "Device ID: $DEVICE_ID"

# Provisionar device:
docker compose exec api python manage.py tenant_command provision_emqx $DEVICE_ID factory-sp --schema=test_alpha

# Verificar campos atualizados no banco:
docker compose exec api python manage.py tenant_command shell --schema=test_alpha << EOF
from apps.devices.models import Device
device = Device.objects.get(id='$DEVICE_ID')
print(f"credentials_id: {device.credentials_id}")
print(f"topic_base: {device.topic_base}")
EOF
```

**Resultado Esperado:**

```
✅ Device provisionado com sucesso!

MQTT Connection Info:
  Host: emqx.local
  Port: 1883
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
```

**⚠️ IMPORTANTE:** Salvar credenciais exibidas para os próximos testes!

```bash
# Exemplo de salvamento temporário (para testes):
export MQTT_HOST="localhost"
export MQTT_PORT="1883"
export MQTT_CLIENT_ID="ts-xxxxxxxx-yyyyyyyy-zzzzzzzz"
export MQTT_USERNAME="t:<tenant_uuid>:d:<device_uuid>"
export MQTT_PASSWORD="<senha_gerada>"
export MQTT_TOPIC_BASE="traksense/<tenant>/<site>/<device>"
```

---

### Passo 4: Validar Criação de Usuário no EMQX

**Objetivo:** Verificar que o usuário foi criado no EMQX via Management API.

**Checklist:**

- [ ] 4.1. Usuário aparece no dashboard do EMQX
- [ ] 4.2. Usuário pode ser consultado via API HTTP
- [ ] 4.3. ACLs foram criadas (6 regras: 5 publish + 1 subscribe)

**Comandos:**

```bash
# Consultar usuário via API do EMQX:
curl -u admin:public http://localhost:18083/api/v5/authentication/password_based:built_in_database/users/$MQTT_USERNAME

# Consultar ACLs do usuário:
curl -u admin:public "http://localhost:18083/api/v5/authorization/sources/built_in_database/rules?username=$MQTT_USERNAME"
```

**Resultado Esperado:**

```json
// Usuário:
{
  "user_id": "t:<tenant_uuid>:d:<device_uuid>",
  "is_superuser": false
}

// ACLs (6 regras):
{
  "data": [
    {"username": "...", "permission": "allow", "action": "publish", "topic": "traksense/.../state"},
    {"username": "...", "permission": "allow", "action": "publish", "topic": "traksense/.../telem"},
    {"username": "...", "permission": "allow", "action": "publish", "topic": "traksense/.../event"},
    {"username": "...", "permission": "allow", "action": "publish", "topic": "traksense/.../alarm"},
    {"username": "...", "permission": "allow", "action": "publish", "topic": "traksense/.../ack"},
    {"username": "...", "permission": "allow", "action": "subscribe", "topic": "traksense/.../cmd"}
  ],
  "meta": {"count": 6}
}
```

**Dashboard Web:**

1. Acessar: http://localhost:18083
2. Login: admin / public
3. Menu: **Authentication** → **Password-Based** → **Built-in Database**
4. Buscar usuário: `t:<tenant_uuid>:d:<device_uuid>`
5. Menu: **Authorization** → **Built-in Database** → **Rules**
6. Verificar 6 regras do usuário

---

### Passo 5: Teste de Conexão MQTT Autorizada (Publish)

**Objetivo:** Verificar que o device consegue publicar nos tópicos permitidos.

**Checklist:**

- [ ] 5.1. Device conecta com credenciais corretas
- [ ] 5.2. Device publica em `.../state` → sucesso (sem desconectar)
- [ ] 5.3. Device publica em `.../telem` → sucesso
- [ ] 5.4. Device publica em `.../event` → sucesso
- [ ] 5.5. Device publica em `.../alarm` → sucesso
- [ ] 5.6. Device publica em `.../ack` → sucesso
- [ ] 5.7. Mensagens aparecem nos logs do EMQX

**Script de Teste (Python com paho-mqtt):**

```python
# Salvar como: backend/test_mqtt_authorized_publish.py
import paho.mqtt.client as mqtt
import time
import os

# Credenciais do device provisionado (ajustar conforme Passo 3)
MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_CLIENT_ID = os.getenv("MQTT_CLIENT_ID")
MQTT_USERNAME = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")
MQTT_TOPIC_BASE = os.getenv("MQTT_TOPIC_BASE")

print(f"🔌 Conectando no EMQX: {MQTT_HOST}:{MQTT_PORT}")
print(f"   ClientID: {MQTT_CLIENT_ID}")
print(f"   Username: {MQTT_USERNAME}")
print(f"   Topic Base: {MQTT_TOPIC_BASE}")

# Callback de conexão
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Conectado com sucesso!")
    else:
        print(f"❌ Falha na conexão: rc={rc}")

# Callback de publicação
def on_publish(client, userdata, mid):
    print(f"✅ Mensagem publicada: mid={mid}")

# Criar cliente
client = mqtt.Client(client_id=MQTT_CLIENT_ID, protocol=mqtt.MQTTv311)
client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
client.on_connect = on_connect
client.on_publish = on_publish

# Conectar
client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
client.loop_start()

time.sleep(2)  # Aguardar conexão

# Testar publicação nos tópicos permitidos
topics_to_test = [
    f"{MQTT_TOPIC_BASE}/state",
    f"{MQTT_TOPIC_BASE}/telem",
    f"{MQTT_TOPIC_BASE}/event",
    f"{MQTT_TOPIC_BASE}/alarm",
    f"{MQTT_TOPIC_BASE}/ack",
]

for topic in topics_to_test:
    payload = f'{{"test": "authorized", "topic": "{topic}"}}'
    result = client.publish(topic, payload, qos=1)
    print(f"📤 Publicando em: {topic}")
    time.sleep(0.5)

time.sleep(2)
client.loop_stop()
client.disconnect()

print("\n✅ Teste de publicação autorizada concluído!")
```

**Executar:**

```bash
# Definir variáveis (ajustar com credenciais do Passo 3):
export MQTT_HOST="localhost"
export MQTT_PORT="1883"
export MQTT_CLIENT_ID="ts-xxxxxxxx-yyyyyyyy-zzzzzzzz"
export MQTT_USERNAME="t:<tenant_uuid>:d:<device_uuid>"
export MQTT_PASSWORD="<senha_gerada>"
export MQTT_TOPIC_BASE="traksense/<tenant>/<site>/<device>"

# Executar teste:
docker compose exec api python /app/backend/test_mqtt_authorized_publish.py
```

**Resultado Esperado:**

```
🔌 Conectando no EMQX: localhost:1883
   ClientID: ts-xxxxxxxx-yyyyyyyy-zzzzzzzz
   Username: t:<tenant_uuid>:d:<device_uuid>
   Topic Base: traksense/<tenant>/<site>/<device>
✅ Conectado com sucesso!
📤 Publicando em: traksense/<tenant>/<site>/<device>/state
✅ Mensagem publicada: mid=1
📤 Publicando em: traksense/<tenant>/<site>/<device>/telem
✅ Mensagem publicada: mid=2
📤 Publicando em: traksense/<tenant>/<site>/<device>/event
✅ Mensagem publicada: mid=3
📤 Publicando em: traksense/<tenant>/<site>/<device>/alarm
✅ Mensagem publicada: mid=4
📤 Publicando em: traksense/<tenant>/<site>/<device>/ack
✅ Mensagem publicada: mid=5

✅ Teste de publicação autorizada concluído!
```

---

### Passo 6: Teste de Conexão MQTT Autorizada (Subscribe)

**Objetivo:** Verificar que o device consegue assinar o tópico de comandos.

**Checklist:**

- [ ] 6.1. Device assina `.../cmd` → SUBACK com QoS válido (0, 1 ou 2)
- [ ] 6.2. Device recebe mensagens publicadas em `.../cmd`

**Script de Teste:**

```python
# Salvar como: backend/test_mqtt_authorized_subscribe.py
import paho.mqtt.client as mqtt
import time
import os

MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_CLIENT_ID = os.getenv("MQTT_CLIENT_ID")
MQTT_USERNAME = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")
MQTT_TOPIC_BASE = os.getenv("MQTT_TOPIC_BASE")

cmd_topic = f"{MQTT_TOPIC_BASE}/cmd"
received_messages = []

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Conectado com sucesso!")
        # Assinar tópico de comandos
        result, mid = client.subscribe(cmd_topic, qos=1)
        print(f"📥 Assinando tópico: {cmd_topic}")
    else:
        print(f"❌ Falha na conexão: rc={rc}")

def on_subscribe(client, userdata, mid, granted_qos):
    if granted_qos[0] != 0x80:  # 0x80 = falha
        print(f"✅ Assinatura confirmada: mid={mid}, qos={granted_qos[0]}")
    else:
        print(f"❌ Assinatura negada: mid={mid}, qos=0x80")

def on_message(client, userdata, msg):
    print(f"✅ Mensagem recebida: topic={msg.topic}, payload={msg.payload.decode()}")
    received_messages.append(msg.payload.decode())

client = mqtt.Client(client_id=MQTT_CLIENT_ID, protocol=mqtt.MQTTv311)
client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
client.on_connect = on_connect
client.on_subscribe = on_subscribe
client.on_message = on_message

client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
client.loop_start()

time.sleep(2)

# Publicar comando de teste (simular backend enviando comando)
test_payload = '{"cmd": "reset_fault", "pulse_ms": 500}'
print(f"📤 Publicando comando de teste: {test_payload}")
client.publish(cmd_topic, test_payload, qos=1)

time.sleep(3)

client.loop_stop()
client.disconnect()

if received_messages:
    print(f"\n✅ Teste de assinatura autorizada concluído! Mensagens recebidas: {len(received_messages)}")
else:
    print(f"\n⚠️ Nenhuma mensagem recebida (pode ser OK se não houver publisher)")
```

**Executar:**

```bash
docker compose exec api python /app/backend/test_mqtt_authorized_subscribe.py
```

**Resultado Esperado:**

```
✅ Conectado com sucesso!
📥 Assinando tópico: traksense/<tenant>/<site>/<device>/cmd
✅ Assinatura confirmada: mid=1, qos=1
📤 Publicando comando de teste: {"cmd": "reset_fault", "pulse_ms": 500}
✅ Mensagem recebida: topic=traksense/<tenant>/<site>/<device>/cmd, payload={"cmd": "reset_fault", "pulse_ms": 500}

✅ Teste de assinatura autorizada concluído! Mensagens recebidas: 1
```

---

### Passo 7: Teste de Negação — Publish Não Autorizado 🚨

**Objetivo:** Verificar que o device **NÃO consegue** publicar fora do seu prefixo.

**Checklist:**

- [ ] 7.1. Device tenta publicar em `traksense/other-tenant/site/dev/telem` → negação
- [ ] 7.2. Device desconecta OU recebe erro de publicação
- [ ] 7.3. Logs do EMQX registram tentativa negada

**Script de Teste:**

```python
# Salvar como: backend/test_mqtt_unauthorized_publish.py
import paho.mqtt.client as mqtt
import time
import os

MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_CLIENT_ID = os.getenv("MQTT_CLIENT_ID")
MQTT_USERNAME = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")

# Tópico de OUTRO device (não autorizado)
unauthorized_topic = "traksense/other-tenant/other-site/other-device/telem"

disconnected = False

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Conectado com sucesso!")
    else:
        print(f"❌ Falha na conexão: rc={rc}")

def on_disconnect(client, userdata, rc):
    global disconnected
    disconnected = True
    if rc != 0:
        print(f"⚠️ Desconectado pelo broker: rc={rc} (esperado se ACL negar)")
    else:
        print(f"✅ Desconectado normalmente")

def on_publish(client, userdata, mid):
    print(f"✅ Mensagem publicada: mid={mid} (inesperado se ACL funcionar!)")

client = mqtt.Client(client_id=MQTT_CLIENT_ID, protocol=mqtt.MQTTv311)
client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_publish = on_publish

client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
client.loop_start()

time.sleep(2)

# Tentar publicar em tópico NÃO autorizado
print(f"📤 Tentando publicar em tópico NÃO autorizado: {unauthorized_topic}")
payload = '{"test": "unauthorized", "expected": "deny"}'
result = client.publish(unauthorized_topic, payload, qos=1)

time.sleep(3)

client.loop_stop()
client.disconnect()

if disconnected:
    print("\n✅ ACL funcionou! Device foi desconectado ao tentar publicar fora do prefixo.")
else:
    print("\n❌ ACL NÃO funcionou! Device não foi desconectado (verificar configuração do EMQX).")
```

**Executar:**

```bash
docker compose exec api python /app/backend/test_mqtt_unauthorized_publish.py
```

**Resultado Esperado:**

```
✅ Conectado com sucesso!
📤 Tentando publicar em tópico NÃO autorizado: traksense/other-tenant/other-site/other-device/telem
⚠️ Desconectado pelo broker: rc=5 (esperado se ACL negar)

✅ ACL funcionou! Device foi desconectado ao tentar publicar fora do prefixo.
```

**Verificar logs do EMQX:**

```bash
docker compose logs emqx | grep -i "not_authorized\|publish_not_allowed\|authorization_denied"
```

**Logs Esperados:**

```
[warning] Authorization denied: username=t:<tenant>:d:<device>, topic=traksense/other-tenant/..., action=publish
[info] Client disconnected: client_id=ts-..., reason=not_authorized
```

---

### Passo 8: Teste de Negação — Subscribe com Wildcard 🚨

**Objetivo:** Verificar que o device **NÃO consegue** assinar wildcards fora do seu prefixo.

**Checklist:**

- [ ] 8.1. Device tenta assinar `traksense/#` → SUBACK 0x80 (negação)
- [ ] 8.2. Device tenta assinar `traksense/+/+/+/telem` → SUBACK 0x80
- [ ] 8.3. Logs do EMQX registram tentativas negadas

**Script de Teste:**

```python
# Salvar como: backend/test_mqtt_unauthorized_subscribe.py
import paho.mqtt.client as mqtt
import time
import os

MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_CLIENT_ID = os.getenv("MQTT_CLIENT_ID")
MQTT_USERNAME = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")

# Tópicos com wildcards (não autorizados)
unauthorized_topics = [
    "traksense/#",  # Wildcard multi-level
    "traksense/+/+/+/telem",  # Wildcard single-level
    "traksense/other-tenant/other-site/other-device/cmd",  # Tópico de outro device
]

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Conectado com sucesso!")
    else:
        print(f"❌ Falha na conexão: rc={rc}")

def on_subscribe(client, userdata, mid, granted_qos):
    topic = unauthorized_topics[mid - 1]
    if granted_qos[0] == 0x80:  # 0x80 = falha
        print(f"✅ ACL funcionou! Assinatura negada: topic={topic}, qos=0x80")
    else:
        print(f"❌ ACL NÃO funcionou! Assinatura permitida: topic={topic}, qos={granted_qos[0]}")

client = mqtt.Client(client_id=MQTT_CLIENT_ID, protocol=mqtt.MQTTv311)
client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
client.on_connect = on_connect
client.on_subscribe = on_subscribe

client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
client.loop_start()

time.sleep(2)

# Tentar assinar tópicos NÃO autorizados
for topic in unauthorized_topics:
    print(f"📥 Tentando assinar tópico NÃO autorizado: {topic}")
    client.subscribe(topic, qos=1)
    time.sleep(1)

time.sleep(2)

client.loop_stop()
client.disconnect()

print("\n✅ Teste de assinatura não autorizada concluído!")
```

**Executar:**

```bash
docker compose exec api python /app/backend/test_mqtt_unauthorized_subscribe.py
```

**Resultado Esperado:**

```
✅ Conectado com sucesso!
📥 Tentando assinar tópico NÃO autorizado: traksense/#
✅ ACL funcionou! Assinatura negada: topic=traksense/#, qos=0x80
📥 Tentando assinar tópico NÃO autorizado: traksense/+/+/+/telem
✅ ACL funcionou! Assinatura negada: topic=traksense/+/+/+/telem, qos=0x80
📥 Tentando assinar tópico NÃO autorizado: traksense/other-tenant/other-site/other-device/cmd
✅ ACL funcionou! Assinatura negada: topic=traksense/other-tenant/other-site/other-device/cmd, qos=0x80

✅ Teste de assinatura não autorizada concluído!
```

---

### Passo 9: Validar Last Will Testament (LWT)

**Objetivo:** Verificar que o device pode configurar LWT e que ele aparece como retain em `state`.

**Checklist:**

- [ ] 9.1. Device configura LWT no tópico `.../state`
- [ ] 9.2. Device desconecta abruptamente (simular falha)
- [ ] 9.3. Mensagem LWT é publicada automaticamente pelo EMQX
- [ ] 9.4. Mensagem LWT tem retain=true (persiste no broker)

**Script de Teste:**

```python
# Salvar como: backend/test_mqtt_lwt.py
import paho.mqtt.client as mqtt
import time
import os
import signal
import sys

MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_CLIENT_ID = os.getenv("MQTT_CLIENT_ID")
MQTT_USERNAME = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")
MQTT_TOPIC_BASE = os.getenv("MQTT_TOPIC_BASE")

state_topic = f"{MQTT_TOPIC_BASE}/state"
lwt_payload = '{"online": false, "reason": "lwt_triggered"}'

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Conectado com sucesso!")
        print(f"   LWT configurado: topic={state_topic}, retain=true, qos=1")
    else:
        print(f"❌ Falha na conexão: rc={rc}")

# Configurar cliente com LWT
client = mqtt.Client(client_id=MQTT_CLIENT_ID, protocol=mqtt.MQTTv311)
client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
client.on_connect = on_connect

# IMPORTANTE: Configurar LWT ANTES de conectar!
client.will_set(state_topic, lwt_payload, qos=1, retain=True)

client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
client.loop_start()

print("⏳ Aguardando 5 segundos antes de desconectar abruptamente...")
time.sleep(5)

# Simular desconexão abrupta (sem DISCONNECT packet)
print("💀 Matando processo para disparar LWT...")
client.loop_stop()
# Não chamar client.disconnect() para simular falha!
# Apenas finalizar o processo:
sys.exit(0)
```

**Executar em um terminal:**

```bash
# Terminal 1: Subscriber no state (para ver LWT chegar)
docker compose exec emqx mosquitto_sub -h localhost -p 1883 \\
    -u "$MQTT_USERNAME" -P "$MQTT_PASSWORD" \\
    -t "$MQTT_TOPIC_BASE/state" -v

# Terminal 2: Executar teste LWT
docker compose exec api python /app/backend/test_mqtt_lwt.py
```

**Resultado Esperado (Terminal 1):**

```
traksense/<tenant>/<site>/<device>/state {"online": false, "reason": "lwt_triggered"}
```

**Validar retain:**

```bash
# Consultar mensagem retained:
docker compose exec emqx mosquitto_sub -h localhost -p 1883 \\
    -u "$MQTT_USERNAME" -P "$MQTT_PASSWORD" \\
    -t "$MQTT_TOPIC_BASE/state" -v -C 1

# Deve exibir a mensagem LWT imediatamente (mesmo sem publisher ativo)
```

---

### Passo 10: Validar Logs e Auditoria

**Objetivo:** Verificar que todas as operações estão sendo logadas corretamente.

**Checklist:**

- [ ] 10.1. Provisionamento de device é logado
- [ ] 10.2. Tentativas de acesso negadas são logadas no EMQX
- [ ] 10.3. Logs contêm informações úteis (username, topic, action, resultado)

**Comandos:**

```bash
# Logs do Django API (provisionamento):
docker compose logs api | grep -i "emqx\|provision"

# Logs do EMQX (autenticação/autorização):
docker compose logs emqx | tail -n 50

# Buscar negações de ACL:
docker compose logs emqx | grep -i "authorization_denied\|not_authorized\|publish_not_allowed"
```

**Logs Esperados (API):**

```
[INFO] EmqxHttpProvisioner inicializado: base_url=http://emqx:18083, admin_user=admin, realm=traksense
[INFO] Iniciando provisionamento EMQX para Device <uuid> (tenant=<tenant>, site=factory-sp)
[INFO] ✅ Usuário EMQX criado: t:<tenant>:d:<device>
[INFO] ✅ ACL configurada para Device <uuid> (6 regras: 5 publish + 1 subscribe)
[INFO] ✅ Device <uuid> atualizado com credentials_id e topic_base
[INFO] ✅ Provisionamento EMQX concluído com sucesso
```

**Logs Esperados (EMQX):**

```
[info] Client connected: client_id=ts-..., username=t:<tenant>:d:<device>, protocol=MQTT/3.1.1
[info] Session created for client: ts-...
[warning] Authorization denied: username=t:<tenant>:d:<device>, topic=traksense/other-tenant/..., action=publish
[info] Client disconnected: client_id=ts-..., reason=not_authorized
```

---

## 📊 Métricas de Validação

| Métrica | Esperado | Status |
|---------|----------|--------|
| Arquivos criados | 7 arquivos (provisioning/*,services.py,command) | ⬜ |
| Imports OK | 100% sem erros | ⬜ |
| Factory funciona | Singleton OK | ⬜ |
| Device provisionado | credentials_id + topic_base salvos | ⬜ |
| Usuário no EMQX | Criado via API | ⬜ |
| ACLs criadas | 6 regras (5 pub + 1 sub) | ⬜ |
| Publish autorizado | 5 tópicos OK | ⬜ |
| Subscribe autorizado | 1 tópico OK | ⬜ |
| Publish não autorizado | Desconexão/erro | ⬜ |
| Subscribe wildcard negado | SUBACK 0x80 | ⬜ |
| LWT funciona | Mensagem retained em state | ⬜ |
| Logs de auditoria | Todas operações logadas | ⬜ |

---

## ✅ Critérios de Aceite Final

**A Fase 3 está concluída quando:**

1. ✅ Existe script/endpoint de provisionamento funcional
2. ✅ Cliente MQTT publica apenas em tópicos autorizados
3. ✅ Cliente MQTT assina apenas em tópicos autorizados
4. ✅ Tentativas fora do prefixo são negadas (SUBACK 0x80 ou desconexão)
5. ✅ Logs do EMQX evidenciam tentativas negadas
6. ✅ ClientID único é gerado e documentado
7. ✅ LWT configurado e testado (retain em state)

**Assinatura de Aprovação:**

- [ ] Desenvolvedor Backend: _______________
- [ ] QA/Tester: _______________
- [ ] Tech Lead: _______________

---

## 🐛 Troubleshooting

### Problema: "EmqxConnectionError: Falha ao conectar no EMQX"

**Causa:** EMQX não está rodando ou variáveis de ambiente incorretas.

**Solução:**

```bash
# Verificar se EMQX está UP:
docker compose ps emqx

# Verificar variáveis:
docker compose exec api env | grep EMQX

# Testar conexão manual:
curl -u admin:public http://localhost:18083/api/v5/status
```

---

### Problema: "SUBACK não retorna 0x80, mas tópico não deveria ser permitido"

**Causa:** EMQX pode estar usando política de autorização padrão (allow all).

**Solução:**

1. Acessar dashboard: http://localhost:18083
2. Menu: **Authorization** → **Settings**
3. Configurar `no_match = deny` (negar tudo por padrão)
4. Salvar e reiniciar: `docker compose restart emqx`

---

### Problema: "LWT não dispara ao desconectar"

**Causa:** LWT não foi configurado antes de conectar, ou keepalive muito longo.

**Solução:**

- Configurar `client.will_set()` **ANTES** de `client.connect()`
- Reduzir keepalive: `client.connect(..., keepalive=10)`
- Simular desconexão abrupta (não chamar `disconnect()`)

---

## 📚 Referências

- [ADR-003: EMQX Authentication & Authorization Strategy](../docs/adr/ADR-003-emqx-authz.md)
- [EMQX v5 HTTP API Documentation](https://docs.emqx.com/en/emqx/v5.0/admin/api.html)
- [EMQX Authorization (ACL)](https://docs.emqx.com/en/emqx/v5.0/access-control/authz/authz.html)
- [Paho MQTT Python Client](https://www.eclipse.org/paho/index.php?page=clients/python/docs/index.php)
- [MQTT v3.1.1 Specification](http://docs.oasis-open.org/mqtt/mqtt/v3.1.1/os/mqtt-v3.1.1-os.html)

---

**Última Atualização:** 2025-10-07  
**Versão do Documento:** 1.0  
**Próxima Revisão:** Após execução completa das validações
