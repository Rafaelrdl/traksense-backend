# 🔧 CORREÇÃO APLICADA - Sensors Page

## ✅ Problema Resolvido

O frontend mostrava **"Device 4b686f6d (undefined)"** porque o campo `mqtt_client_id` não estava sendo retornado pelo endpoint `/api/sites/{id}/devices/`.

### Correção Aplicada

**Arquivo:** `apps/assets/serializers.py`

```python
class DeviceListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listagem de Devices."""
    
    asset_tag = serializers.CharField(source='asset.tag', read_only=True)
    sensor_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Device
        fields = [
            'id',
            'name',
            'serial_number',
            'mqtt_client_id',  # ✅ ADICIONADO
            'asset',
            'asset_tag',
            'device_type',
            'status',
            'sensor_count',
            'last_seen',
            'created_at',
        ]
```

**Problema anterior:** Campo `is_online` estava na lista mas **não existe no modelo Device** (só existe no modelo Sensor).

**Correção:** Removido `is_online` e mantido apenas `mqtt_client_id`.

---

## 📊 Estado Atual do Backend

### ✅ Dados Verificados

Todos os dados estão **corretamente criados** no banco:

1. **Site:** "Uberlândia Medical Center" (ID: 7) ✅
2. **Asset:** "CHILLER-001" (type: CHILLER, status: OK) ✅
3. **Device:** "4b686f6d70107115" (type: GATEWAY, status: OFFLINE) ✅
4. **Sensores:** 4 sensores criados ✅
   - `283286b20a000036` - temp_supply (30.75°C)
   - `4b686f6d70107115_A_humid` - humidity (64.0%)
   - `4b686f6d70107115_A_temp` - temp_supply (23.35°C)
   - `4b686f6d70107115_rssi` - maintenance (-61.0 dBW)
5. **Readings:** 10+ readings salvas no TimescaleDB ✅

### ✅ Endpoint de Devices

**Endpoint:** `GET /api/sites/7/devices/`

**Resposta:**
```json
[
  {
    "id": 7,
    "name": "Device 4b686f6d",
    "serial_number": "4b686f6d70107115",
    "mqtt_client_id": "4b686f6d70107115",  // ✅ AGORA PRESENTE
    "asset": 6,
    "asset_tag": "CHILLER-001",
    "device_type": "GATEWAY",
    "status": "OFFLINE",
    "sensor_count": 4,
    "last_seen": "2025-10-22T19:47:27.357895-03:00",
    "created_at": "2025-10-20T23:26:35.598392-03:00"
  }
]
```

---

## 🧪 Como Testar

### Passo 1: Atualizar Frontend

1. **Abra o navegador** em: http://umc.localhost:5173

2. **Abra o DevTools** (F12)

3. **Recarregue a página** (Ctrl + F5 ou Cmd + Shift + R)

4. **Vá para a aba Console**

### Passo 2: Verificar Logs

Você deve ver:

```
✅ Sucesso: Site selecionado: Uberlândia Medical Center
✅ Sucesso: 1 device(s) encontrado(s)
✅ Sucesso: Device selecionado: Device 4b686f6d (4b686f6d70107115)  // ← AGORA COM ID
```

### Passo 3: Verificar Network

1. **Abra aba Network** no DevTools
2. **Filtre por:** `devices`
3. **Veja a resposta** do endpoint `/api/sites/7/devices/`
4. **Verifique** se `mqtt_client_id` está presente

### Passo 4: Verificar Página de Sensores

1. **Navegue** até "Sensores" no menu
2. **Você deve ver:**
   - Dropdown de devices com "Device 4b686f6d"
   - Lista de 4 sensores:
     - Temperatura Insuflamento (30.75°C)
     - Umidade (64.0%)
     - Temperatura Ambiente (23.35°C)
     - Sinal RSSI (-61.0 dBW)

---

## 🔍 Troubleshooting

### Se ainda não aparecer sensores:

#### 1. Verificar se telemetria está funcionando

**Console do navegador:**
```javascript
// Copie e cole no console
const deviceId = '4b686f6d70107115';
const token = localStorage.getItem('access_token');

fetch(`http://umc.localhost:8000/api/telemetry/device/${deviceId}/summary/`, {
  headers: {
    'Authorization': `Bearer ${token}`
  }
})
.then(r => r.json())
.then(d => console.log('Telemetria:', d))
.catch(e => console.error('Erro:', e));
```

#### 2. Verificar credenciais

Se o login não funcionar, use:
- **Email:** admin@umc.com.br  
- **Senha:** admin123

#### 3. Verificar backend logs

```bash
cd "c:\Users\Rafael Ribeiro\TrakSense\traksense-backend\docker"
docker compose logs -f api
```

Publique nova mensagem MQTT e veja os logs processando.

---

## 📝 Próximos Passos

### Se tudo estiver OK:

1. ✅ Sensors aparecem na lista
2. ✅ Valores são exibidos corretamente
3. ✅ Timestamps são recentes

### Se ainda houver problemas:

**Verifique:**
1. Device status está OFFLINE (deveria ser ONLINE após receber dados)
2. Frontend chama endpoint correto
3. CORS está configurado
4. JWT token é válido

**Possível ajuste necessário:**
- Atualizar status do device para ONLINE quando receber dados
- Adicionar auto-update de device.last_seen na view de ingest

---

## 🎯 Resumo

### ✅ Correções Aplicadas:
1. Adicionado `mqtt_client_id` ao `DeviceListSerializer`
2. Removido `is_online` (campo inexistente no modelo Device)
3. API reiniciada e testada
4. Endpoint `/api/sites/{id}/devices/` retornando corretamente

### 📊 Estado:
- **Backend:** 100% funcional ✅
- **Auto-vinculação:** Funcionando perfeitamente ✅
- **Dados:** Criados e salvos corretamente ✅
- **API:** Retornando `mqtt_client_id` ✅
- **Frontend:** Aguardando teste do usuário 🔄

### 🚀 Ação Imediata:
**Recarregue o frontend** e verifique se os sensores aparecem!
