# ADR-003: EMQX Authentication & Authorization Strategy

**Status:** Aceito  
**Data:** 2025-10-07  
**Decisores:** Time TrakSense  
**Contexto:** Fase 3 - Provisionamento de Devices e segurança MQTT

---

## Contexto e Problema

A plataforma TrakSense precisa provisionar dispositivos IoT com credenciais seguras para conexão ao broker EMQX. Cada device deve ter:

1. **Autenticação (AuthN):** Username/password único
2. **Autorização (AuthZ):** Acesso restrito apenas aos tópicos do próprio device
3. **Princípio do mínimo privilégio:** Sem wildcards perigosos (`#`, `+`) fora do escopo do device
4. **Isolamento multi-tenant:** Devices de um tenant não devem acessar tópicos de outros

### Requisitos Técnicos

- **Publish permitido:** `traksense/{tenant}/{site}/{device}/(state|telem|event|alarm|ack)`
- **Subscribe permitido:** `traksense/{tenant}/{site}/{device}/cmd`
- **Negação:** Qualquer tentativa fora do prefixo deve ser bloqueada (SUBACK 0x80 ou desconexão)
- **ClientID único:** Gerado por device para rastreabilidade
- **LWT (Last Will Testament):** Configurado pelo próprio device em `state` com retain

---

## Opções Consideradas

### Opção A: HTTP Management API (Escolhida)

**Descrição:**  
Usar a HTTP Management API do EMQX v5 para criar usuários e regras de ACL via REST.

**Vantagens:**
- ✅ **Simplicidade:** Sem necessidade de estrutura adicional no banco de dados
- ✅ **Isolamento:** Backend não precisa acessar internals do EMQX
- ✅ **Flexibilidade:** Fácil trocar de broker sem alterar schema SQL
- ✅ **Auditabilidade:** Logs centralizados no backend
- ✅ **Dev/Staging:** Ideal para ambientes onde latência HTTP é aceitável

**Desvantagens:**
- ⚠️ **Latência:** Requisições HTTP adicionam overhead (mitigado com retry/backoff)
- ⚠️ **Disponibilidade:** Dependência do endpoint EMQX (mitigado com idempotência)
- ⚠️ **Performance:** Não ideal para provisionamento massivo simultâneo

**Implementação:**
```python
# backend/apps/devices/provisioning/emqx_http.py
class EmqxHttpProvisioner(EmqxProvisioner):
    def create_user(self, creds: EmqxCredentials) -> None:
        # POST /api/v5/authentication/{realm}/users
        # Retry 3x com backoff exponencial (1s, 2s, 4s)
        ...
    
    def set_acl(self, creds, tenant, site, device) -> None:
        # POST /api/v5/authorization/sources/{realm}/rules
        # Permite apenas prefixos exatos do device
        ...
```

**Mitigações de Risco:**
1. **Latência/Timeout:** Retry com backoff exponencial (3 tentativas)
2. **Indisponibilidade:** Operação idempotente (pode re-executar sem duplicar)
3. **Auditoria:** Logs estruturados de todas as chamadas HTTP
4. **Métricas:** Contagem de sucessos/falhas para alertas

---

### Opção B: PostgreSQL Authentication & Authorization (Alternativa)

**Descrição:**  
EMQX lê credenciais e ACLs diretamente de tabelas PostgreSQL via conector nativo.

**Vantagens:**
- ✅ **Performance:** Baixa latência (acesso direto ao DB)
- ✅ **Escalabilidade:** Suporta milhões de devices
- ✅ **Transacional:** Provisionamento atômico (credencial + ACL na mesma transação)
- ✅ **Produção:** Ideal para alta carga

**Desvantagens:**
- ⚠️ **Complexidade:** Requer schema adicional e configuração do EMQX
- ⚠️ **Acoplamento:** Backend precisa conhecer estrutura interna do EMQX
- ⚠️ **Manutenção:** Alterações no schema do EMQX exigem migrations

**Implementação (Skeleton):**
```python
# backend/apps/devices/provisioning/emqx_sql.py
class EmqxSqlProvisioner(EmqxProvisioner):
    def create_user(self, creds: EmqxCredentials) -> None:
        # INSERT INTO emqx_authn (username, password_hash, salt)
        ...
    
    def set_acl(self, creds, tenant, site, device) -> None:
        # INSERT INTO emqx_acl (username, action, topic, permission)
        ...
```

**Schema SQL (Exemplo - EMQX v5):**
```sql
CREATE TABLE emqx_authn (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    salt VARCHAR(64),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE emqx_acl (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    permission VARCHAR(10) CHECK (permission IN ('allow', 'deny')),
    action VARCHAR(10) CHECK (action IN ('publish', 'subscribe', 'all')),
    topic VARCHAR(512) NOT NULL,
    UNIQUE(username, action, topic)
);

CREATE INDEX idx_emqx_authn_username ON emqx_authn(username);
CREATE INDEX idx_emqx_acl_username ON emqx_acl(username);
```

---

## Decisão

**Escolhida:** Opção A (HTTP Management API)

**Justificativa:**
1. **Fase atual (dev/staging):** Simplicidade é mais importante que performance máxima
2. **Volume inicial:** Não teremos provisionamento massivo simultâneo na Fase 3
3. **Isolamento:** Menor acoplamento com internals do EMQX facilita testes e manutenção
4. **Reversibilidade:** Strategy Pattern permite trocar para Opção B sem breaking changes

**Quando migrar para Opção B:**
- Provisionamento de >1000 devices/hora
- Latência HTTP causando timeouts frequentes
- EMQX Management API se tornando gargalo (evidenciado por métricas)

---

## Implementação

### 1. Variáveis de Ambiente

```bash
# infra/.env.api
EMQX_MGMT_URL=http://emqx:18083
EMQX_ADMIN_USER=admin
EMQX_ADMIN_PASS=public
EMQX_REALM=traksense
EMQX_PROVISION_MODE=http  # ou 'sql' para Opção B
```

### 2. Strategy Pattern

```python
# backend/apps/devices/provisioning/factory.py
def get_provisioner() -> EmqxProvisioner:
    mode = os.getenv("EMQX_PROVISION_MODE", "http")
    if mode == "http":
        return EmqxHttpProvisioner()
    elif mode == "sql":
        return EmqxSqlProvisioner()
    raise ValueError(f"Unsupported mode: {mode}")
```

**Benefício:** Trocar entre A/B é apenas mudar `EMQX_PROVISION_MODE` — sem alterar services.py ou views.py.

### 3. ACL Mínima (Exemplo)

Para device `device-123` do tenant `tenant-abc` no site `site-xyz`:

```json
{
  "rules": [
    {
      "action": "publish",
      "permission": "allow",
      "topic": "traksense/tenant-abc/site-xyz/device-123/state"
    },
    {
      "action": "publish",
      "permission": "allow",
      "topic": "traksense/tenant-abc/site-xyz/device-123/telem"
    },
    {
      "action": "publish",
      "permission": "allow",
      "topic": "traksense/tenant-abc/site-xyz/device-123/event"
    },
    {
      "action": "publish",
      "permission": "allow",
      "topic": "traksense/tenant-abc/site-xyz/device-123/alarm"
    },
    {
      "action": "publish",
      "permission": "allow",
      "topic": "traksense/tenant-abc/site-xyz/device-123/ack"
    },
    {
      "action": "subscribe",
      "permission": "allow",
      "topic": "traksense/tenant-abc/site-xyz/device-123/cmd"
    }
  ]
}
```

**Importante:** Nunca usar `#` ou `+` fora do prefixo do device.

---

## Consequências

### Positivas
- ✅ Implementação rápida (API HTTP é mais simples)
- ✅ Testes de integração facilitados (mock HTTP vs mock SQL)
- ✅ Menor risco de erros em schema SQL
- ✅ Facilita debugging (logs HTTP vs queries SQL)

### Negativas
- ⚠️ Latência adicional (aceitável em dev/staging)
- ⚠️ Necessidade de retry/backoff para resiliência
- ⚠️ Migração futura para Opção B se volume crescer

### Neutras
- 🔄 Strategy Pattern adiciona uma camada de abstração
- 🔄 Documentação de LWT deve ser clara para integradores

---

## Validação

### Critérios de Aceite

1. ✅ Device provisionado consegue publicar em `.../state|telem|event|alarm|ack`
2. ✅ Device provisionado consegue assinar `.../cmd`
3. ✅ Device provisionado **não consegue** publicar em `traksense/other/.../telem` (SUBACK 0x80 ou disconnect)
4. ✅ Device provisionado **não consegue** assinar `traksense/#` (negação)
5. ✅ Logs de auditoria registram todos os provisionamentos
6. ✅ Métricas básicas (sucessos/falhas) disponíveis

### Testes de Integração

```python
# tests/test_emqx_provisioning.py
def test_authorized_publish(mqtt_client, provisioned_creds):
    # Device publica em seu próprio tópico → sucesso
    client.publish(f"{topic_base}/telem", payload)
    assert not client.was_disconnected()

def test_unauthorized_publish(mqtt_client, provisioned_creds):
    # Device tenta publicar em tópico de outro device → negação
    client.publish("traksense/other-tenant/site/dev/telem", payload)
    assert client.was_disconnected() or client.got_puback_error()

def test_unauthorized_subscribe_wildcard(mqtt_client, provisioned_creds):
    # Device tenta assinar wildcard → SUBACK 0x80
    rc, mid = client.subscribe("traksense/#")
    assert granted_qos == 0x80  # Subscription denied
```

---

## Referências

- [EMQX v5 HTTP API](https://docs.emqx.com/en/emqx/v5.0/admin/api.html)
- [EMQX PostgreSQL AuthN/AuthZ](https://docs.emqx.com/en/emqx/v5.0/access-control/authn/postgresql.html)
- [ADR-000: Arquitetura Multi-Tenant](./ADR-000.md)
- [ADR-001: Timescale Hypertable Única](./ADR-001.md)

---

## Histórico de Revisões

| Data       | Versão | Autor        | Alteração              |
|------------|--------|--------------|------------------------|
| 2025-10-07 | 1.0    | Time Backend | Criação inicial        |
