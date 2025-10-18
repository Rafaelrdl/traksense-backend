# Fase 0.7 - Melhorias do Control Center

**Data de Início**: 18 de outubro de 2025  
**Status**: 🚧 **EM PROGRESSO**

---

## 🎯 Objetivos da Fase 0.7

Implementar 4 melhorias críticas no Control Center para aumentar valor operacional, performance e segurança.

---

## 📋 Features Planejadas

### 1️⃣ Dashboard com Gráficos (Chart.js)
**Prioridade**: 🔴 **ALTA** - Maior valor imediato  
**Estimativa**: 2-3 horas  
**Status**: 🚧 Em progresso

#### Objetivos
- Visualização temporal de métricas em gráficos de linha
- Comparação de múltiplos sensores no mesmo gráfico
- Detecção visual de anomalias e tendências
- Interface interativa com zoom e tooltip

#### Componentes a Implementar
1. **Nova view**: `telemetry_dashboard()`
2. **Template**: `dashboard.html` com Chart.js
3. **API endpoint**: `/ops/api/chart-data/` (JSON para gráficos)
4. **Filtros**: Tenant, sensores múltiplos, range temporal
5. **Tipos de gráfico**: Linha (temporal), barra (comparação)

#### Stack Técnico
- **Frontend**: Chart.js 4.x (via CDN)
- **Backend**: Django view retornando JSON
- **Agregação**: time_bucket() para performance
- **Cores**: Palette distinta por sensor

---

### 2️⃣ Export Assíncrono (Celery)
**Prioridade**: 🟠 **MÉDIA-ALTA** - Resolve timeouts  
**Estimativa**: 3-4 horas  
**Status**: ⏳ Aguardando

#### Objetivos
- Suportar exports de milhões de registros sem timeout
- Notificação por email quando CSV estiver pronto
- Fila de jobs com status (pending, processing, completed, failed)
- Download via link temporário (S3/MinIO)

#### Componentes a Implementar
1. **Celery task**: `export_telemetry_async.delay()`
2. **Model**: `ExportJob` (tenant, status, file_url, created_at)
3. **View**: `request_export()` (cria job), `download_export()` (serve arquivo)
4. **Template**: Lista de exports com status
5. **Email**: Notificação com link de download

#### Stack Técnico
- **Task Queue**: Celery + Redis
- **Storage**: MinIO (S3-compatible)
- **Notificação**: Django Email (Mailpit em dev)
- **Progress**: Task state tracking

---

### 3️⃣ Audit Log de Queries
**Prioridade**: 🟡 **MÉDIA** - Compliance e segurança  
**Estimativa**: 2 horas  
**Status**: ⏳ Aguardando

#### Objetivos
- Rastrear todas as queries executadas no Control Center
- Registrar: usuário, tenant consultado, filtros, timestamp
- Interface para revisar histórico de acessos
- Export de audit logs para compliance

#### Componentes a Implementar
1. **Model**: `AuditLog` (user, tenant, action, filters, ip, timestamp)
2. **Middleware/Decorator**: Auto-logging em views
3. **View**: `audit_log_list()` (visualização para staff)
4. **Template**: Tabela paginada de logs
5. **Filtros**: Por usuário, tenant, data

#### Stack Técnico
- **Storage**: PostgreSQL (schema public)
- **Indexação**: timestamp, user_id, tenant_id
- **Retenção**: 90 dias (configurável)

---

### 4️⃣ Cache Redis para Lista de Tenants
**Prioridade**: 🟢 **BAIXA** - Otimização futura  
**Estimativa**: 1 hora  
**Status**: ⏳ Aguardando

#### Objetivos
- Reduzir queries ao banco na página inicial
- Invalidação automática quando tenant é modificado
- TTL configurável (default: 5 minutos)

#### Componentes a Implementar
1. **Cache wrapper**: `get_cached_tenants()`
2. **Signal**: Invalidar cache em Tenant.save()
3. **View update**: Usar cache em `index()`
4. **Admin action**: "Clear tenants cache"

#### Stack Técnico
- **Cache**: Redis (já configurado)
- **Django Cache**: `@cache_page` ou manual
- **Invalidação**: Django signals

---

## 📊 Cronograma Estimado

| Feature | Estimativa | Dependências |
|---------|-----------|--------------|
| Dashboard com Gráficos | 2-3h | Nenhuma |
| Export Assíncrono | 3-4h | Celery já configurado |
| Audit Log | 2h | Nenhuma |
| Cache Redis | 1h | Nenhuma |
| **Total** | **8-10h** | - |

---

## 🔄 Ordem de Implementação

1. ✅ **Dashboard com Gráficos** (em progresso)
   - Maior valor imediato
   - Não tem dependências
   - Facilita detecção de problemas

2. ⏳ **Export Assíncrono**
   - Resolve problema real (timeouts)
   - Celery já está configurado
   - Melhora UX significativamente

3. ⏳ **Audit Log**
   - Importante para compliance
   - Simples de implementar
   - Sem dependências externas

4. ⏳ **Cache Redis**
   - Otimização incremental
   - Mais relevante quando houver muitos tenants
   - Rápido de implementar

---

## 🧪 Critérios de Aceitação

### Dashboard com Gráficos
- [ ] Página `/ops/dashboard/` acessível
- [ ] Seleção de tenant obrigatória
- [ ] Seleção de múltiplos sensores (checkbox)
- [ ] Gráfico de linha temporal renderizado
- [ ] Tooltip mostrando valores exatos
- [ ] Zoom funcional
- [ ] Responsivo (mobile-friendly)
- [ ] Exportar gráfico como PNG

### Export Assíncrono
- [ ] Botão "Request Export" cria job
- [ ] Job processado em background
- [ ] Email enviado com link de download
- [ ] Download funcional por 24h
- [ ] Lista de exports mostra status
- [ ] Cancelamento de job pendente
- [ ] Limpeza automática de arquivos antigos

### Audit Log
- [ ] Todas as queries registradas automaticamente
- [ ] Página `/ops/audit/` lista logs
- [ ] Filtros funcionais (usuário, tenant, data)
- [ ] Export de logs em CSV
- [ ] Dados sensíveis não logados (valores)
- [ ] Retenção de 90 dias configurada

### Cache Redis
- [ ] Lista de tenants cacheada
- [ ] Cache invalidado ao salvar tenant
- [ ] TTL de 5 minutos
- [ ] Admin action "Clear cache" funcional
- [ ] Performance melhorada (< 50ms vs ~200ms)

---

## 📈 Métricas de Sucesso

### Dashboard
- **Adoção**: 80%+ dos staff users acessam dashboard
- **Valor**: Detectar 3+ anomalias antes de virar incidente
- **Performance**: Carregamento < 2s com 1000 pontos

### Export Assíncrono
- **Capacidade**: Suportar exports de 1M+ registros
- **Timeout**: 0 timeouts reportados
- **UX**: 95%+ satisfação (não bloqueia interface)

### Audit Log
- **Compliance**: 100% das queries logadas
- **Retenção**: Logs disponíveis por 90 dias
- **Investigação**: Tempo médio < 5min para rastrear acesso

### Cache Redis
- **Performance**: 75%+ redução no tempo de carregamento
- **Hit Rate**: 90%+ cache hits
- **Invalidação**: 0 cache stale reportados

---

## 🔧 Configurações Necessárias

### Chart.js (CDN)
```html
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.js"></script>
```

### Celery (já configurado)
```python
# settings/base.py
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
```

### MinIO (já configurado)
```python
MINIO_ENDPOINT = 'minio:9000'
MINIO_ACCESS_KEY = 'minioadmin'
```

### Redis Cache (adicionar)
```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': REDIS_URL,
    }
}
```

---

## 📝 Notas de Implementação

### Dashboard
- Usar Chart.js em vez de Plotly (mais leve)
- Limitar a 10 sensores por gráfico (performance)
- Agregação automática para > 1000 pontos

### Export Assíncrono
- MaxRetry=3 para falhas transientes
- Soft timeout=300s, hard timeout=600s
- Compressão GZIP para arquivos grandes

### Audit Log
- **NÃO** logar valores de telemetria (LGPD/GDPR)
- Logar apenas metadados (filtros, counts)
- Índice composto em (tenant_id, timestamp)

### Cache
- Cache key: `tenants:list:v1`
- Invalidação via signal `post_save` e `post_delete`
- Fallback se Redis não disponível

---

## 🚀 Próximos Passos

1. **Implementar Dashboard** (agora)
2. **Testar Dashboard** com dados reais
3. **Implementar Export Assíncrono**
4. **Implementar Audit Log**
5. **Implementar Cache Redis**
6. **Testes de integração**
7. **Documentação completa**
8. **Deploy em staging**

---

**Iniciado por**: GitHub Copilot  
**Data**: 2025-10-18T16:45:00-03:00  
**Versão**: Fase 0.7
