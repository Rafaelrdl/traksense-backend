# 📋 GUIA: Publicar Mensagens MQTT via MQTTX

## 🎯 Configuração de Conexão MQTTX

- **Host**: localhost
- **Port**: 1883
- **Protocol**: mqtt://

## 📤 Mensagens para Publicar

### Mensagem 1 - Sensor de Temperatura/Outro
- **Topic**: `traksense/umc/sensor/4b686f6d70107115/283286b20a000036`
- **Payload**: `25.5`
- **Condição**: > 10.0 ✅ **SERÁ ATENDIDA**

### Mensagem 2 - Sensor de Umidade
- **Topic**: `traksense/umc/sensor/4b686f6d70107115/4b686f6d70107115_A_humid`
- **Payload**: `80.0`
- **Condição**: > 54.0 ✅ **SERÁ ATENDIDA**

### Mensagem 3 - Sensor de Temperatura A
- **Topic**: `traksense/umc/sensor/4b686f6d70107115/4b686f6d70107115_A_temp`
- **Payload**: `32.0`
- **Condição**: > 24.0 ✅ **SERÁ ATENDIDA**

## ⏱️ Após Publicar

1. **Aguarde até 5 minutos** para o Celery avaliar automaticamente
   
2. **OU teste imediatamente**:
   ```bash
   docker exec traksense-api python test_rule_evaluation_fixed.py
   ```

3. **Monitore os logs**:
   ```bash
   # Ver logs do worker (processamento de alertas)
   docker logs -f traksense-worker
   
   # Ver logs do scheduler (agendamento)
   docker logs -f traksense-scheduler
   ```

4. **Verifique os alertas**:
   - Frontend: http://localhost/alerts
   - Backend API: http://localhost/api/alerts/
   - Admin: http://localhost/admin/alerts/alert/

## 🔍 Verificar se as Mensagens Chegaram

Execute no PowerShell:
```powershell
docker exec traksense-api python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django_tenants.utils import schema_context
from apps.ingest.models import Reading
from django.utils import timezone
from datetime import timedelta

with schema_context('umc'):
    cutoff = timezone.now() - timedelta(minutes=5)
    readings = Reading.objects.filter(
        device_id='4b686f6d70107115',
        ts__gte=cutoff
    ).order_by('-ts')[:10]
    
    print('\\n📊 Últimas 10 readings (últimos 5 min):\\n')
    for r in readings:
        print(f'{r.ts.strftime(\"%H:%M:%S\")} | {r.sensor_id:40} | {r.value}')
"
```

## ✅ Sucesso Esperado

Quando tudo funcionar, você verá nos logs do worker algo como:

```
[INFO] Alert 123 triggered for rule 10 (Alerta CHILLER-001) on equipment CHILLER-001 in tenant umc
[INFO] Notifications sent for alert 123: 1 sent, 0 failed, 0 skipped
```

E os alertas aparecerão no frontend! 🎉
