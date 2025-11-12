# ✅ IMPLEMENTADO: Timestamp em Horário Local do Site

## 🎯 Objetivo

Armazenar timestamps no **horário local do Site** em vez de UTC, facilitando:
- Análises diretas no banco de dados sem conversões
- Debug intuitivo (timestamps correspondem ao horário real)
- Logs mais claros para operadores

## 🏗️ Arquitetura Implementada

### 1. **Cache Inteligente de Timezone**

**Arquivo:** `apps/ingest/views.py`

```python
# Cache key: site_timezone:{tenant}:{site_name}
cache_key = f"site_timezone:umc:Uberlândia Medical Center"
```

**Fluxo:**
1. Primeira mensagem: consulta `Site.timezone` no banco → cache por 24h
2. Mensagens seguintes: usa valor do cache (zero queries)
3. Atualização de Site: signal invalida cache automaticamente

**Performance:**
- ✅ **Zero overhead** em mensagens subsequentes
- ✅ **Automático** - não precisa gerenciar invalidação manual
- ✅ **Multi-tenant** - cache separado por tenant e site

### 2. **Conversão de Timestamp**

**Fluxo completo:**

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Equipamento envia SenML                                  │
│    bt = 1762913123 (Unix timestamp UTC)                     │
└──────────────────┬──────────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. API recebe via EMQX                                      │
│    - Extrai nome do Site do tópico MQTT                     │
│    - Busca timezone do Site no cache                        │
└──────────────────┬──────────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. Conversão de Timezone                                    │
│    a) bt → datetime UTC: 2025-11-12 02:05:23 UTC           │
│    b) UTC → America/Sao_Paulo: 2025-11-11 23:05:23 BRT     │
│    c) Armazena: 2025-11-11 23:05:23-03:00                  │
└──────────────────┬──────────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. Banco de Dados (PostgreSQL)                             │
│    ts = 2025-11-11 23:05:23-03:00  ← HORÁRIO LOCAL!        │
└─────────────────────────────────────────────────────────────┘
```

**Código:**
```python
# 1. Criar datetime UTC do timestamp
utc_dt = datetime.fromtimestamp(senml_bt, tz=dt_timezone.utc)

# 2. Converter para timezone local do Site
site_tz = pytz.timezone('America/Sao_Paulo')  # Do cache
local_dt = utc_dt.astimezone(site_tz)

# 3. Armazenar com timezone local
ingest_timestamp = local_dt  # 2025-11-11 23:05:23-03:00
```

### 3. **Invalidação Automática de Cache**

**Arquivo:** `apps/assets/signals.py`

```python
@receiver(post_save, sender=Site)
def invalidate_site_timezone_cache_on_save(sender, instance, **kwargs):
    cache_key = f"site_timezone:{schema_name}:{instance.name}"
    cache.delete(cache_key)
```

**Quando invalida:**
- ✅ Site é editado (ex: mudar timezone de America/Sao_Paulo para America/Fortaleza)
- ✅ Site é deletado
- ✅ Próxima mensagem MQTT busca novo timezone automaticamente

### 4. **Compatibilidade com Regras de Alerta**

**Arquivo:** `apps/alerts/tasks.py`

**Problema:** Regras comparavam timestamps em timezones diferentes
- `latest_reading.ts` → horário local (23:05)
- `timezone.now()` → UTC (02:05)
- Diferença aparente de 3 horas! ❌

**Solução:** Converter `timezone.now()` para o timezone do reading

```python
now = timezone.now()  # UTC
if latest_reading.ts.tzinfo:
    now_in_reading_tz = now.astimezone(latest_reading.ts.tzinfo)
    time_diff = now_in_reading_tz - latest_reading.ts
```

**Resultado:** Comparação correta independente do timezone!

## 🌍 Suporte Multi-Timezone

### Configuração por Site

Cada Site tem seu timezone configurado:

| Site | Timezone | UTC Offset | Exemplo |
|------|----------|------------|---------|
| UMC Uberlândia | America/Sao_Paulo | UTC-3 | 23:05 → armazena 23:05 |
| Hospital NY | America/New_York | UTC-5 | 18:05 → armazena 18:05 |
| Clínica Lisboa | Europe/Lisbon | UTC+0 | 02:05 → armazena 02:05 |

### Adicionar Novo Cliente em Timezone Diferente

**Exemplo: Cliente em Manaus (UTC-4)**

1. **Criar Site no Admin/API:**
```python
Site.objects.create(
    name='Hospital Manaus',
    timezone='America/Manaus',  # UTC-4
    ...
)
```

2. **Sistema automaticamente:**
   - ✅ Cache o timezone na primeira mensagem
   - ✅ Converte timestamps para UTC-4
   - ✅ Armazena no horário local de Manaus
   - ✅ Regras comparam corretamente

**Zero código adicional necessário!** 🎉

### Timezones Suportados

Qualquer timezone IANA válido:
- **Brasil:** America/Sao_Paulo, America/Manaus, America/Fortaleza, America/Recife
- **EUA:** America/New_York, America/Chicago, America/Los_Angeles
- **Europa:** Europe/London, Europe/Paris, Europe/Lisbon
- **Ásia:** Asia/Tokyo, Asia/Shanghai, Asia/Dubai
- [Lista completa](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)

## 📊 Análise de Dados

### Query Direta no Banco

Agora você pode fazer queries intuitivas:

```sql
-- Readings entre 22h e 23h (horário local)
SELECT * FROM reading 
WHERE ts >= '2025-11-11 22:00:00'
  AND ts < '2025-11-11 23:00:00'
ORDER BY ts DESC;

-- Resultado: timestamps em horário local!
 sensor_id    | value | ts                        
--------------+-------+---------------------------
 temp_saida   | 8.5   | 2025-11-11 22:35:23-03:00
 temp_retorno | 25.0  | 2025-11-11 22:35:23-03:00
```

### Logs Mais Claros

**Antes (UTC):**
```
INFO 2025-11-11 23:05:26 - Timestamp: 2025-11-12T02:05:23+00:00
```
❌ Confuso! Mostra dia 12 quando ainda é dia 11

**Depois (Local):**
```
⏰ TIMESTAMP - 
   Unix=1762913123s, 
   UTC=12/11/2025 02:05:23, 
   Local(America/Sao_Paulo)=11/11/2025 23:05:23, 
   ✅ Armazenando: 11/11/2025 23:05:23 BRT
```
✅ Claro! Mostra ambos os horários

## 🧪 Validação

### 1. Testar Cache de Timezone

```powershell
# Primeira mensagem - deve consultar banco
docker-compose logs -f api | Select-String "cacheado"

# Mensagens seguintes - deve usar cache
docker-compose logs -f api | Select-String "do cache"
```

**Saída esperada:**
```
📍 Timezone do Site 'Uberlândia Medical Center' cacheado: America/Sao_Paulo
✅ Timezone do Site 'Uberlândia Medical Center' do cache: America/Sao_Paulo
✅ Timezone do Site 'Uberlândia Medical Center' do cache: America/Sao_Paulo
...
```

### 2. Testar Conversão de Timestamp

```powershell
# Publicar mensagem via MQTTX
# Verificar log
docker-compose logs -f api | Select-String "TIMESTAMP"
```

**Saída esperada:**
```
⏰ TIMESTAMP - 
   Unix=1762913123s, 
   UTC=12/11/2025 02:05:23, 
   Local(America/Sao_Paulo)=11/11/2025 23:05:23, 
   ✅ Armazenando: 11/11/2025 23:05:23 BRT
```

### 3. Verificar Banco de Dados

```sql
-- Conectar no PostgreSQL
docker exec -it traksense-postgres psql -U traksense -d traksense

-- Mudar para schema do tenant
SET search_path TO umc, public;

-- Ver últimas leituras
SELECT 
    sensor_id,
    value,
    ts,
    EXTRACT(TIMEZONE FROM ts) / 3600 as utc_offset_hours
FROM reading
ORDER BY ts DESC
LIMIT 5;
```

**Resultado esperado:**
```
sensor_id              | value | ts                        | utc_offset_hours
-----------------------+-------+---------------------------+-----------------
temp_saida             | 8.5   | 2025-11-11 23:05:23-03:00 | -3
temp_retorno           | 25.0  | 2025-11-11 23:05:23-03:00 | -3
```

✅ **UTC offset = -3 (America/Sao_Paulo)**

### 4. Testar Mudança de Timezone

```python
# No Django Admin ou shell
from apps.assets.models import Site

site = Site.objects.get(name='Uberlândia Medical Center')
site.timezone = 'America/Fortaleza'  # UTC-3 também
site.save()

# Verificar log
# ✅ Cache do timezone invalidado para Site 'Uberlândia Medical Center'
```

Próxima mensagem MQTT vai usar novo timezone automaticamente!

## 📝 Comparação: Antes vs Depois

### Antes (UTC)

| Aspecto | Comportamento |
|---------|---------------|
| Hora enviada | 23:05 (local) |
| Hora armazenada | 02:05 (UTC, dia seguinte!) |
| Query no banco | `WHERE ts > '2025-11-12 02:00'` ❌ confuso |
| Análise | Precisa sempre converter mentalmente -3h |
| Debug | Timestamps no "futuro" |

### Depois (Local)

| Aspecto | Comportamento |
|---------|---------------|
| Hora enviada | 23:05 (local) |
| Hora armazenada | 23:05 (local) ✅ |
| Query no banco | `WHERE ts > '2025-11-11 23:00'` ✅ intuitivo |
| Análise | Timestamps diretos, sem conversão |
| Debug | Timestamps correspondem à realidade |

## 🎯 Benefícios

1. **✅ Análise Intuitiva:** Timestamps no banco correspondem ao horário real do equipamento
2. **✅ Zero Overhead:** Cache evita queries extras (1 query na primeira mensagem, 0 depois)
3. **✅ Auto-invalidação:** Mudanças no timezone do Site refletem automaticamente
4. **✅ Multi-timezone Nativo:** Novos clientes em outros fusos funcionam sem código adicional
5. **✅ Compatível:** Regras de alerta comparam corretamente independente do timezone
6. **✅ Logs Claros:** Mostra UTC e horário local para debug

## 🔄 Manutenção

### Adicionar Novo Site em Timezone Diferente

```python
# Apenas configurar o timezone correto
Site.objects.create(
    name='Hospital Tokyo',
    timezone='Asia/Tokyo',  # UTC+9
    ...
)
```

Sistema funciona automaticamente! 🎉

### Corrigir Timezone de Site Existente

```python
site = Site.objects.get(name='...')
site.timezone = 'America/Recife'  # Novo timezone
site.save()  # Signal invalida cache automaticamente
```

Próxima mensagem já usa o timezone correto!

### Monitoring

```python
# Ver cache keys ativos
from django.core.cache import cache
cache.keys('site_timezone:*')

# Limpar cache manualmente (se necessário)
cache.delete_pattern('site_timezone:*')
```

## 📚 Referências

- **Timezones IANA:** https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
- **Python pytz:** https://pypi.org/project/pytz/
- **Django Cache:** https://docs.djangoproject.com/en/5.0/topics/cache/
- **Django Signals:** https://docs.djangoproject.com/en/5.0/topics/signals/

---

**Data de Implementação:** 11 de novembro de 2025  
**Status:** ✅ Produção  
**Performance:** Zero overhead após primeira mensagem  
**Compatibilidade:** 100% multi-timezone
