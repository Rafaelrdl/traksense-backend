# README — Fase 3: EMQX AuthN/ACL & Provisioning

**Status:** ✅ Implementação Concluída | 🟡 Validação em Andamento  
**Data:** 2025-10-07  
**Responsável:** Time TrakSense Backend

---

## 📌 Objetivo da Fase 3

Implementar provisionamento seguro de dispositivos IoT no broker EMQX com:

- **Autenticação (AuthN):** Username/password únicos por device
- **Autorização (AuthZ):** ACL mínima — device só acessa seus próprios tópicos
- **Princípio do mínimo privilégio:** Sem wildcards perigosos (#, +) fora do prefixo
- **Isolamento multi-tenant:** Devices de um tenant não acessam tópicos de outros

---

## 🏗️ Arquitetura

### Componentes Implementados

```
┌─────────────────────────────────────────────────────────────────┐
│                         Backend Django                          │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  apps/devices/provisioning/                              │  │
│  │                                                          │  │
│  │  ┌─────────────┐      ┌──────────────────────────────┐ │  │
│  │  │   emqx.py   │──────│ EmqxProvisioner (Interface)  │ │  │
│  │  │ (Interface) │      │ EmqxCredentials (DataClass)  │ │  │
│  │  └─────────────┘      └──────────────────────────────┘ │  │
│  │                                                          │  │
│  │  ┌─────────────────┐     ┌──────────────────────────┐  │  │
│  │  │  emqx_http.py   │─────│ EmqxHttpProvisioner      │  │  │
│  │  │  (Opção A)      │     │ - create_user()          │  │  │
│  │  │                 │     │ - set_acl()              │  │  │
│  │  │                 │     │ - delete_user()          │  │  │
│  │  │                 │     │ - Retry/Backoff (3x)     │  │  │
│  │  └─────────────────┘     └──────────────────────────┘  │  │
│  │                                                          │  │
│  │  ┌─────────────────┐     ┌──────────────────────────┐  │  │
│  │  │  emqx_sql.py    │─────│ EmqxSqlProvisioner       │  │  │
│  │  │  (Opção B)      │     │ (Skeleton não impl.)     │  │  │
│  │  └─────────────────┘     └──────────────────────────┘  │  │
│  │                                                          │  │
│  │  ┌─────────────────┐     ┌──────────────────────────┐  │  │
│  │  │   factory.py    │─────│ get_provisioner()        │  │  │
│  │  │  (Strategy)     │     │ - Singleton pattern      │  │  │
│  │  │                 │     │ - EMQX_PROVISION_MODE    │  │  │
│  │  └─────────────────┘     └──────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  apps/devices/services.py                               │  │
│  │                                                          │  │
│  │  - generate_client_id()                                 │  │
│  │  - provision_emqx_for_device()                          │  │
│  │  - deprovision_emqx_for_device()                        │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  management/commands/provision_emqx.py                  │  │
│  │  $ python manage.py tenant_command provision_emqx       │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                │ HTTP Management API
                                ▼
                    ┌──────────────────────────┐
                    │     EMQX Broker v5       │
                    │                          │
                    │  - Authentication DB     │
                    │  - Authorization Rules   │
                    │  - MQTT Clients          │
                    └──────────────────────────┘
```

### Strategy Pattern

O provisionador usa Strategy Pattern para alternar entre implementações:

- **Opção A (http):** EmqxHttpProvisioner — HTTP Management API (padrão dev/staging)
- **Opção B (sql):** EmqxSqlProvisioner — Postgres AuthN/AuthZ (produção, não implementado)

Trocar entre estratégias: mudar `EMQX_PROVISION_MODE=http` para `sql` no `.env.api`.

---

## 🔐 Modelo de Segurança

### Credenciais por Device

Cada device recebe credenciais únicas ao ser provisionado:

```yaml
Username: t:<tenant_uuid>:d:<device_uuid>
Password: <20+ caracteres aleatórios, gerados com secrets.token_urlsafe()>
ClientID: ts-<tenant_short>-<device_short>-<random>
```

**Exemplo:**

```
Username: t:1a2b3c4d-5e6f-7g8h-9i0j-k1l2m3n4o5p6:d:9f8e7d6c-5b4a-3210-fedc-ba0987654321
Password: Xy9Kp2Lm4Nq6Rs8Tv0UwZa1Bc
ClientID: ts-1a2b3c4d-9f8e7d6c-a1b2c3d4
```

### ACL Mínima (6 Regras)

Cada device possui exatamente 6 regras de ACL:

| Ação | Permissão | Tópico | Descrição |
|------|-----------|--------|-----------|
| publish | allow | `traksense/{tenant}/{site}/{device}/state` | Status online/offline (com LWT) |
| publish | allow | `traksense/{tenant}/{site}/{device}/telem` | Telemetria (temperatura, pressão, etc.) |
| publish | allow | `traksense/{tenant}/{site}/{device}/event` | Eventos (mudança de estado) |
| publish | allow | `traksense/{tenant}/{site}/{device}/alarm` | Alarmes (falhas, limiares excedidos) |
| publish | allow | `traksense/{tenant}/{site}/{device}/ack` | Confirmações de comandos |
| subscribe | allow | `traksense/{tenant}/{site}/{device}/cmd` | Comandos do backend |

**Importante:**
- ❌ Sem wildcards (#, +) fora do prefixo do device
- ❌ Device não acessa tópicos de outros devices
- ❌ Device não acessa tópicos de outros tenants

---

## 🚀 Como Usar

### 1. Provisionar Device via CLI

```bash
# Sintaxe:
docker compose exec api python manage.py tenant_command provision_emqx \\
    <device_id> <site_slug> --schema=<tenant_schema>

# Exemplo:
docker compose exec api python manage.py tenant_command provision_emqx \\
    8b848ad7-7f07-4479-9ecd-32f0f68ffca5 \\
    factory-sp \\
    --schema=test_alpha

# Saída:
✅ Device provisionado com sucesso!

MQTT Connection Info:
  Host:     emqx.local
  Port:     1883
  ClientID: ts-1a2b3c4d-9f8e7d6c-a1b2c3d4
  Username: t:1a2b3c4d-5e6f-7g8h-9i0j-k1l2m3n4o5p6:d:9f8e7d6c-5b4a-3210-fedc-ba0987654321
  Password: Xy9Kp2Lm4Nq6Rs8Tv0UwZa1Bc  ⚠️ SALVE COM SEGURANÇA!

Topics (Publish):
  - traksense/1a2b.../factory-sp/9f8e.../state
  - traksense/1a2b.../factory-sp/9f8e.../telem
  - traksense/1a2b.../factory-sp/9f8e.../event
  - traksense/1a2b.../factory-sp/9f8e.../alarm
  - traksense/1a2b.../factory-sp/9f8e.../ack

Topics (Subscribe):
  - traksense/1a2b.../factory-sp/9f8e.../cmd

LWT (Last Will Testament):
  Topic:   traksense/1a2b.../factory-sp/9f8e.../state
  Retain:  True
  QoS:     1
  Payload: {"online": false, "ts": "<timestamp>"}
  
  ⚠️ O device deve configurar LWT ao conectar!
```

**⚠️ SEGURANÇA CRÍTICA:**
- Salvar senha em secrets manager (AWS Secrets, Azure KeyVault)
- OU exibir apenas 1x ao operador
- NUNCA armazenar em plain-text no banco

### 2. Provisionar via Python (Django Shell)

```python
from apps.devices.models import Device
from apps.devices.services import provision_emqx_for_device

# Buscar device
device = Device.objects.get(id='<device_uuid>')

# Provisionar
mqtt_info = provision_emqx_for_device(
    device=device,
    site_slug='factory-sp'
)

# Exibir credenciais
print(f"Username: {mqtt_info['mqtt']['username']}")
print(f"Password: {mqtt_info['mqtt']['password']}")  # ⚠️ SALVAR COM SEGURANÇA!
print(f"ClientID: {mqtt_info['mqtt']['client_id']}")
```

### 3. Configurar Device IoT (Integrador)

```python
import paho.mqtt.client as mqtt

# Credenciais recebidas do provisionamento
MQTT_HOST = "emqx.local"  # ou IP do broker
MQTT_PORT = 1883  # ou 8883 com TLS em produção
MQTT_CLIENT_ID = "ts-1a2b3c4d-9f8e7d6c-a1b2c3d4"
MQTT_USERNAME = "t:1a2b3c4d-...:d:9f8e7d6c-..."
MQTT_PASSWORD = "Xy9Kp2Lm4Nq6Rs8Tv0UwZa1Bc"
MQTT_TOPIC_BASE = "traksense/1a2b.../factory-sp/9f8e..."

# Configurar cliente com LWT (IMPORTANTE!)
client = mqtt.Client(client_id=MQTT_CLIENT_ID)
client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

# Last Will Testament (disparado se device desconectar abruptamente)
lwt_payload = '{"online": false, "ts": "2025-10-07T15:30:00Z"}'
client.will_set(
    topic=f"{MQTT_TOPIC_BASE}/state",
    payload=lwt_payload,
    qos=1,
    retain=True  # Mensagem persiste no broker
)

# Conectar
client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
client.loop_start()

# Publicar telemetria
telem_payload = '{"temp": 23.5, "pressure": 101.3}'
client.publish(f"{MQTT_TOPIC_BASE}/telem", telem_payload, qos=1)

# Assinar comandos
def on_message(client, userdata, msg):
    print(f"Comando recebido: {msg.payload.decode()}")
    # Processar comando e enviar ACK

client.subscribe(f"{MQTT_TOPIC_BASE}/cmd", qos=1)
client.on_message = on_message
```

---

## 🧪 Validação

Consulte o [VALIDATION_CHECKLIST_FASE3.md](./VALIDATION_CHECKLIST_FASE3.md) para:

- Checklist completo de validação
- Scripts de teste paho-mqtt
- Testes de autorização (publish/subscribe autorizado)
- Testes de negação (ACL funcionando)
- Validação de LWT
- Análise de logs

**Resumo dos Testes:**

```bash
# Passo 1: Validar implementação
docker compose exec api ls -la /app/backend/apps/devices/provisioning/

# Passo 2: Testar factory
docker compose exec api python -c "from apps.devices.provisioning.factory import get_provisioner; print('✅ OK')"

# Passo 3: Provisionar device
docker compose exec api python manage.py tenant_command provision_emqx <device_id> <site> --schema=test_alpha

# Passo 4: Validar usuário no EMQX
curl -u admin:public http://localhost:18083/api/v5/authentication/password_based:built_in_database/users/<username>

# Passo 5-8: Testes MQTT (ver VALIDATION_CHECKLIST_FASE3.md)

# Passo 9: Validar LWT

# Passo 10: Verificar logs
docker compose logs emqx | grep -i "authorization_denied\|not_authorized"
```

---

## ⚙️ Configuração

### Variáveis de Ambiente (`.env.api`)

```bash
# EMQX Management API
EMQX_MGMT_URL=http://emqx:18083
EMQX_ADMIN_USER=admin
EMQX_ADMIN_PASS=public
EMQX_REALM=traksense

# Modo de provisionamento: 'http' (padrão) ou 'sql' (não implementado)
EMQX_PROVISION_MODE=http
```

### Alternando entre HTTP e SQL

```bash
# Dev/Staging (padrão): HTTP Management API
EMQX_PROVISION_MODE=http

# Produção (quando implementar): Postgres AuthN/AuthZ
EMQX_PROVISION_MODE=sql
```

Não é necessário alterar código — apenas mudar variável de ambiente e reiniciar:

```bash
docker compose restart api
```

---

## 📁 Estrutura de Arquivos

```
backend/apps/devices/
├── provisioning/
│   ├── __init__.py           # EmqxProvisioner, EmqxCredentials
│   ├── emqx.py               # Re-exports
│   ├── emqx_http.py          # Opção A: HTTP Management API (implementado)
│   ├── emqx_sql.py           # Opção B: Postgres AuthN/ACL (skeleton)
│   └── factory.py            # Strategy Factory + Singleton
├── services.py               # provision_emqx_for_device(), generate_client_id()
└── management/
    └── commands/
        └── provision_emqx.py # Management command CLI

docs/adr/
└── ADR-003-emqx-authz.md     # Decisão arquitetural (http vs sql)

VALIDATION_CHECKLIST_FASE3.md # Checklist detalhado de validação
README_FASE3.md               # Este arquivo
```

---

## 🔍 Troubleshooting

### Erro: "EmqxConnectionError: Falha ao conectar no EMQX"

**Causa:** EMQX não está rodando ou variáveis incorretas.

**Solução:**

```bash
# Verificar containers:
docker compose ps

# Verificar variáveis:
docker compose exec api env | grep EMQX

# Testar API manualmente:
curl -u admin:public http://localhost:18083/api/v5/status
```

### Erro: "SUBACK 0x80 não retorna, ACL não funciona"

**Causa:** EMQX pode estar usando política de autorização padrão (allow all).

**Solução:**

1. Acessar dashboard: http://localhost:18083
2. Menu: **Authorization** → **Settings**
3. Configurar `no_match = deny`
4. Salvar e reiniciar: `docker compose restart emqx`

### Device desconecta imediatamente após conectar

**Causa:** Credenciais incorretas ou ClientID duplicado.

**Solução:**

```bash
# Verificar logs do EMQX:
docker compose logs emqx | tail -n 50

# Buscar erros de autenticação:
docker compose logs emqx | grep -i "auth_failed\|bad_username_or_password"

# Re-provisionar device (gera novas credenciais):
docker compose exec api python manage.py tenant_command provision_emqx <device_id> <site> --schema=<tenant>
```

---

## 📚 Referências

- [ADR-003: EMQX Authentication & Authorization Strategy](./docs/adr/ADR-003-emqx-authz.md)
- [EMQX v5 HTTP API Documentation](https://docs.emqx.com/en/emqx/v5.0/admin/api.html)
- [EMQX Authorization (ACL)](https://docs.emqx.com/en/emqx/v5.0/access-control/authz/authz.html)
- [Paho MQTT Python Client](https://www.eclipse.org/paho/index.php?page=clients/python/docs/index.php)
- [MQTT v3.1.1 Specification](http://docs.oasis-open.org/mqtt/mqtt/v3.1.1/os/mqtt-v3.1.1-os.html)

---

## 🎯 Próximos Passos (Fase 4)

- [ ] Implementar serviço Ingest assíncrono (asyncio-mqtt)
- [ ] Adapters Pydantic para normalização de payloads (parsec_v1)
- [ ] Persistência em TimescaleDB via asyncpg (batch insert)
- [ ] Validação de contratos MQTT (schemas JSON)
- [ ] Dead Letter Queue (DLQ) para payloads inválidos

---

**Última Atualização:** 2025-10-07  
**Versão:** 1.0  
**Autor:** Time TrakSense Backend
