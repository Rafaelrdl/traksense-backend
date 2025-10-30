# 🎯 Guia Rápido - Control Center

## Como Acessar o Control Center

### Método 1: Via Botão no Django Admin (RECOMENDADO) ⚡

1. **Acesse o Django Admin**
   ```
   http://localhost:8000/admin/
   ```

2. **Faça Login**
   - Username: `admin`
   - Password: `Admin@123456` (ou a senha que você configurou)

3. **Localize o Botão na Barra Lateral**
   
   Na barra lateral esquerda, procure pela seção:
   ```
   AUTHENTICATION AND AUTHORIZATION
   ├── 🎛️ Control Center  ← CLIQUE AQUI
   ├── Users
   └── Groups
   ```

4. **Clique em "🎛️ Control Center"**
   - Você será redirecionado para `http://localhost:8000/ops/`
   - A página do Control Center abrirá com o título "Control Center"

---

### Método 2: Via URL Direta

Você também pode acessar diretamente pela URL:
```
http://localhost:8000/ops/
```

**Nota**: Requer login com usuário staff (`is_staff=True`)

---

## Funcionalidades do Control Center

### 1. Seletor de Tenant
- Lista todos os tenants cadastrados no sistema
- Permite escolher qual organização consultar

### 2. Filtros de Telemetria
- **device_id**: Filtrar por dispositivo específico
- **sensor_id**: Filtrar por sensor específico
- **from/to**: Range de tempo (ISO-8601)
- **bucket**: Agregação (1m, 5m, 1h)
- **limit**: Quantidade de resultados

### 3. Resultados Agregados
- Visualização em tabela paginada
- Métricas: avg, min, max, last, count
- Ordenação por timestamp

### 4. Drill-down
- Inspecionar leituras brutas de sensor específico
- Estatísticas detalhadas
- Últimas N leituras

### 5. Export CSV
- Download de dados filtrados
- Formato CSV pronto para análise
- Protegido por CSRF

---

## Requisitos de Acesso

✅ **Permissões Necessárias**:
- `is_staff = True` (usuário staff)
- Acesso ao schema `public`
- Login ativo no Django Admin

❌ **Não Funciona Para**:
- Usuários não-staff (`is_staff = False`)
- Acesso via domínios de tenant (ex: `umc.localhost`)
- Requisições não autenticadas

---

## Segurança

### Isolamento de Schema
O Control Center executa **exclusivamente no schema public**, mas pode consultar dados de qualquer tenant usando `schema_context()`:

```python
with schema_context('uberlandia_medical_center'):
    readings = Reading.objects.filter(sensor_id='temp_01')
```

### Proteção CSRF
Todos os formulários incluem token CSRF:
```html
<form method="post">
    {% csrf_token %}
    <!-- campos -->
</form>
```

### Bloqueio em Tenants
O middleware `BlockTenantOpsMiddleware` garante que `/ops/` retorne 404 quando acessado via domínio de tenant.

---

## Troubleshooting

### ❓ Não vejo o botão "Control Center" no Admin

**Possíveis causas**:
1. Cache do navegador - Faça hard refresh (`Ctrl + Shift + R`)
2. API não reiniciou - Execute: `docker compose -f docker/docker-compose.yml restart api`
3. Configuração não carregou - Verifique `config/settings/base.py` → `JAZZMIN_SETTINGS`

### ❓ Erro 404 ao acessar /ops/

**Possíveis causas**:
1. Acessando via domínio de tenant (ex: `umc.localhost:8000/ops/`)
   - **Solução**: Use `localhost:8000/ops/` (schema public)
2. URL não registrada
   - **Solução**: Verifique `config/urls_public.py` → `path('ops/', ...)`

### ❓ Erro 302 (redirecionamento)

**Causa**: Você não está autenticado ou não é staff

**Solução**:
1. Acesse `http://localhost:8000/admin/`
2. Faça login com usuário staff
3. Tente novamente acessar `/ops/`

### ❓ Página carrega mas aparece "Ops Panel" em vez de "Control Center"

**Causa**: Cache do navegador ou API não reiniciou

**Solução**:
1. Limpe cache do navegador (`Ctrl + Shift + Delete`)
2. Reinicie API: `docker compose -f docker/docker-compose.yml restart api`
3. Hard refresh: `Ctrl + Shift + R`

---

## Dicas de Uso

### 💡 Atalho de Teclado

**Adicione aos Favoritos**:
1. Acesse `http://localhost:8000/ops/`
2. Pressione `Ctrl + D`
3. Salve como "Control Center"
4. Próxima vez: `Ctrl + L` → digite "control" → Enter

### 💡 Query Rápida

Para consultar rapidamente um sensor:
1. Selecione tenant
2. Digite `sensor_id` (ex: `temp_01`)
3. Deixe outros campos vazios
4. Clique "Query Telemetry"

### 💡 Export Grande

Para exports > 1000 registros:
1. Aumente `limit` para 10000 (máximo para CSV)
2. Adicione filtros para reduzir volume
3. Considere múltiplos exports com range de tempo

---

## Exemplo de Fluxo Completo

```
1. Login Admin
   └─> http://localhost:8000/admin/
   
2. Clique "🎛️ Control Center"
   └─> http://localhost:8000/ops/
   
3. Selecione Tenant
   └─> "Uberlândia Medical Center"
   
4. Configure Filtros
   ├─> sensor_id: "temp_01"
   ├─> bucket: "1m"
   └─> limit: 50
   
5. Query Telemetry
   └─> Visualize resultados agregados
   
6. Drill-down (opcional)
   └─> Clique botão "Drill-down" em linha desejada
   └─> Visualize leituras brutas + estatísticas
   
7. Export CSV (opcional)
   └─> Clique "Export CSV"
   └─> Baixe arquivo para análise
```

---

## 📊 Exemplo de Resultados

### Telemetry List (Agregado)
```
Bucket              | Device    | Sensor  | Avg   | Min   | Max   | Last  | Count
--------------------|-----------|---------|-------|-------|-------|-------|------
2025-10-18 03:26:00 | device_001| temp_01 | 20.80 | 20.67 | 20.93 | 20.93 | 2
2025-10-18 03:25:00 | device_001| temp_01 | 20.75 | 20.70 | 20.80 | 20.80 | 3
2025-10-18 03:24:00 | device_001| temp_01 | 20.85 | 20.80 | 20.90 | 20.90 | 2
```

### Drill-down (Raw Readings)
```
Timestamp                  | Device     | Sensor  | Value | Labels
---------------------------|------------|---------|-------|--------
2025-10-18 03:26:14.345343 | device_001 | temp_01 | 20.93 | {"unit":"celsius"}
2025-10-18 03:26:03.123456 | device_001 | temp_01 | 20.67 | {"unit":"celsius"}
2025-10-18 03:25:52.987654 | device_001 | temp_01 | 20.80 | {"unit":"celsius"}
```

---

## ✅ Checklist de Validação

Antes de usar em produção, valide:

- [ ] Botão aparece no Django Admin
- [ ] Botão redireciona para `/ops/`
- [ ] Página exibe "Control Center" no título
- [ ] Lista de tenants carrega corretamente
- [ ] Filtros funcionam (device_id, sensor_id, timestamps)
- [ ] Resultados agregados aparecem
- [ ] Paginação funciona (próxima/anterior)
- [ ] Drill-down exibe leituras brutas
- [ ] Export CSV gera arquivo válido
- [ ] 404 ao acessar via domínio de tenant
- [ ] Redirecionamento para login se não-staff

---

**Última atualização**: 18/10/2025  
**Versão**: Fase 0.6.1
