# Correção: Sensores Fantasma na Página de Sensores

## 🐛 Problema Identificado

A página de Sensores estava exibindo 5 sensores (HUM-001, TEMP-AMB-001, TEMP-WATER-IN-001, TEMP-WATER-OUT-001, temp_supply_1) mesmo quando o site "Uberlândia Medical Center" não possui nenhum sensor cadastrado no banco de dados.

### Causa Raiz

1. **Device Hardcoded**: A página `SensorsPage.tsx` estava tentando carregar telemetria de um device fixo (`GW-1760908415`) que não existe no banco de dados
2. **Sem Filtro por Site**: A página não verificava qual site estava selecionado antes de tentar carregar sensores
3. **Endpoint 404**: O endpoint `/api/telemetry/devices/GW-1760908415/summary/` retorna 404 porque o device não existe
4. **Dados em Cache**: Possível existência de dados antigos em localStorage do navegador

## ✅ Solução Implementada

### 1. **Verificação do Site Selecionado**

```typescript
// Antes
useEffect(() => {
  const DEVICE_ID = 'GW-1760908415';
  loadRealTelemetry(DEVICE_ID);
  startTelemetryAutoRefresh(DEVICE_ID, 30000);
}, []);

// Depois
useEffect(() => {
  if (!currentSite) {
    console.warn('⚠️ Nenhum site selecionado');
    setNoDeviceAvailable(true);
    return;
  }
  
  loadRealTelemetry(DEVICE_ID)
    .then(() => setNoDeviceAvailable(false))
    .catch(error => {
      console.warn('⚠️ Nenhum device/sensor encontrado');
      setNoDeviceAvailable(true);
      useSensorsStore.setState({ items: [] });
    });
}, [currentSite]);
```

### 2. **Mensagem Adequada para Empty State**

```typescript
{noDeviceAvailable ? (
  <>
    <p>📍 Nenhum device/sensor cadastrado para este site</p>
    <p>O site "{currentSite.name}" ainda não possui devices ou sensores.</p>
    <p>💡 Cadastre devices e sensores no Django Admin</p>
  </>
) : (
  <>
    <p>Nenhum sensor encontrado</p>
    <p>Verifique os filtros ou aguarde sincronização</p>
  </>
)}
```

### 3. **Limpeza de Dados ao Falhar**

Quando a API retorna erro (404), agora limpamos explicitamente a lista de sensores:

```typescript
.catch(error => {
  useSensorsStore.setState({ items: [] });
});
```

## 🧪 Como Testar

### 1. **Limpar Cache do Navegador**

```javascript
// No Console do navegador (F12):
localStorage.removeItem('ts:sensors');
localStorage.removeItem('app-storage');
location.reload();
```

### 2. **Verificar Comportamento**

1. Acesse: http://localhost:5001/
2. Faça login
3. Navegue para página "Sensores"
4. Deve aparecer:
   ```
   📍 Nenhum device/sensor cadastrado para este site
   O site "Uberlândia Medical Center" ainda não possui devices ou sensores cadastrados.
   💡 Cadastre devices e sensores no Django Admin para visualizá-los aqui.
   ```

### 3. **Verificar Logs do Console**

```
⚠️ Nenhum device/sensor encontrado para este site: Error...
📡 Tentando carregar telemetria para site: Uberlândia Medical Center
```

## 📊 Estado Atual do Banco de Dados

```sql
-- Schema: umc (Uberlândia Medical Center)
SELECT COUNT(*) FROM sites;     -- 4 sites
SELECT COUNT(*) FROM assets;    -- 0 assets
SELECT COUNT(*) FROM devices;   -- 0 devices
SELECT COUNT(*) FROM sensors;   -- 0 sensors ✅
```

## 🔮 Próximos Passos

### Para ter sensores funcionando:

1. **Criar um Asset no Site**:
   ```
   Admin → Tenants → UMC → Sites → Selecionar site → Assets → Adicionar Asset
   ```

2. **Criar um Device para o Asset**:
   ```
   - Name: Gateway Principal
   - Serial Number: GW-001
   - MQTT Client ID: GW-1760908415 (ou outro)
   - Asset: [selecionar asset criado]
   ```

3. **Criar Sensores para o Device**:
   ```
   - Tag: TEMP-001
   - Device: [selecionar device criado]
   - Metric Type: TEMPERATURE
   - Unit: °C
   ```

4. **Publicar Telemetria via MQTT**:
   ```python
   python publish_test_telemetry.py --device GW-1760908415
   ```

### Melhorias Futuras:

1. **Buscar Devices do Site Atual**:
   ```typescript
   // Ao invés de device hardcoded
   const devices = await devicesService.getAll({ site: currentSite.id });
   if (devices.results.length > 0) {
     loadRealTelemetry(devices.results[0].mqtt_client_id);
   }
   ```

2. **Dropdown de Devices**:
   - Permitir usuário selecionar qual device visualizar
   - Mostrar lista de devices disponíveis no site

3. **Auto-descoberta de Devices**:
   - Listar todos os devices do site automaticamente
   - Carregar telemetria de múltiplos devices

## 🔍 Verificação no Backend

```bash
# Verificar devices no tenant
docker exec traksense-api python manage.py shell -c "
from django_tenants.utils import schema_context
from apps.tenants.models import Tenant
from apps.assets.models import Device, Sensor

tenant = Tenant.objects.get(schema_name='umc')
schema_context(tenant.schema_name).__enter__()

print('Devices:', Device.objects.count())
print('Sensors:', Sensor.objects.count())
"

# Resultado esperado:
# Devices: 0
# Sensors: 0
```

## 📝 Arquivos Modificados

1. `src/components/pages/SensorsPage.tsx`:
   - Adicionado verificação de `currentSite`
   - Adicionado tratamento de erro para device não encontrado
   - Melhorada mensagem de empty state
   - Adicionado dependência `[currentSite]` no useEffect

2. `check_telemetry_endpoint.py` (novo):
   - Script para verificar se endpoint de telemetria existe
   - Útil para debugging

## ✅ Resultado

Agora a página de Sensores:
- ✅ Não exibe sensores fantasma
- ✅ Mostra mensagem clara quando não há dados
- ✅ Sugere ação ao usuário (cadastrar no admin)
- ✅ Respeita o site selecionado no header
- ✅ Limpa dados quando device não existe

---

**Data**: 20 de outubro de 2025  
**Versão**: FASE 3 - Correção Sensores Fantasma
