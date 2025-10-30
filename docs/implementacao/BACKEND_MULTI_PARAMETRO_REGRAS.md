# Backend Django - Implementação Multi-Parâmetro

## 📋 Checklist de Implementação

### Fase 1: Models e Database

- [ ] 1.1 Criar model `RuleParameter`
- [ ] 1.2 Adicionar related_name em `Rule`
- [ ] 1.3 Criar e aplicar migrations
- [ ] 1.4 Verificar banco de dados

### Fase 2: Serializers

- [ ] 2.1 Criar `RuleParameterSerializer`
- [ ] 2.2 Modificar `RuleSerializer` para nested serializer
- [ ] 2.3 Implementar `create()` com parameters
- [ ] 2.4 Implementar `update()` com parameters

### Fase 3: Celery Tasks

- [ ] 3.1 Modificar `evaluate_rules_task`
- [ ] 3.2 Criar `evaluate_rule_parameter`
- [ ] 3.3 Criar `generate_message_from_template`
- [ ] 3.4 Implementar cooldown por parâmetro

### Fase 4: Testes

- [ ] 4.1 Testar criação de regra
- [ ] 4.2 Testar edição de regra
- [ ] 4.3 Testar avaliação de regra
- [ ] 4.4 Testar geração de alertas

---

## 📁 Arquivos a Modificar

```
traksense-backend/
├── apps/
│   └── alerts/
│       ├── models.py          # ⚠️ Modificar
│       ├── serializers.py     # ⚠️ Modificar
│       ├── tasks.py           # ⚠️ Modificar
│       └── migrations/
│           └── XXXX_add_rule_parameters.py  # ✅ Criar
```

---

## 1️⃣ FASE 1: Models

### Arquivo: `apps/alerts/models.py`

**ADICIONAR ao final do arquivo:**

```python
class RuleParameter(models.Model):
    """
    Parâmetro individual de uma regra multi-parâmetro.
    
    Permite que uma Rule monitore múltiplos sensores,
    cada um com configurações independentes.
    
    Exemplo:
        Regra: "Chiller CH-01 - Monitoramento"
        - Parâmetro 1: Temperatura > 25°C (CRITICAL)
        - Parâmetro 2: Pressão > 300 PSI (HIGH)
        - Parâmetro 3: Fluxo < 50 L/min (MEDIUM)
    """
    
    rule = models.ForeignKey(
        'Rule',
        on_delete=models.CASCADE,
        related_name='parameters',
        help_text='Regra pai que contém este parâmetro'
    )
    
    parameter_key = models.CharField(
        max_length=100,
        help_text='Identificador do sensor (ex: sensor_123)'
    )
    
    variable_key = models.CharField(
        max_length=50,
        default='current',
        help_text='Variável a monitorar (ex: avg, min, max, current)'
    )
    
    operator = models.CharField(
        max_length=2,
        choices=[
            ('>', 'Maior que'),
            ('>=', 'Maior ou igual'),
            ('<', 'Menor que'),
            ('<=', 'Menor ou igual'),
            ('==', 'Igual'),
            ('!=', 'Diferente'),
        ],
        help_text='Operador de comparação'
    )
    
    threshold = models.FloatField(
        help_text='Valor limite para comparação'
    )
    
    duration = models.IntegerField(
        default=5,
        help_text='Duração do cooldown em minutos (evita spam de alertas)'
    )
    
    severity = models.CharField(
        max_length=20,
        choices=[
            ('Critical', 'Crítico'),
            ('High', 'Alto'),
            ('Medium', 'Médio'),
            ('Low', 'Baixo'),
        ],
        help_text='Severidade do alerta gerado'
    )
    
    message_template = models.TextField(
        help_text='Template da mensagem com variáveis: {sensor}, {value}, {threshold}, {operator}, {unit}'
    )
    
    unit = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text='Unidade de medida (ex: °C, PSI, L/min)'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'rule_parameters'
        ordering = ['id']
        verbose_name = 'Parâmetro de Regra'
        verbose_name_plural = 'Parâmetros de Regras'
    
    def __str__(self):
        return f"{self.rule.name} - {self.parameter_key} {self.operator} {self.threshold}"
    
    def evaluate(self, current_value: float) -> bool:
        """
        Avalia se o valor atual satisfaz a condição do parâmetro.
        
        Args:
            current_value: Valor atual do sensor
            
        Returns:
            True se a condição for atendida, False caso contrário
        """
        operators = {
            '>': lambda a, b: a > b,
            '>=': lambda a, b: a >= b,
            '<': lambda a, b: a < b,
            '<=': lambda a, b: a <= b,
            '==': lambda a, b: a == b,
            '!=': lambda a, b: a != b,
        }
        
        operator_func = operators.get(self.operator)
        if not operator_func:
            raise ValueError(f"Operador inválido: {self.operator}")
        
        return operator_func(current_value, self.threshold)
    
    def generate_message(self, sensor_tag: str, current_value: float) -> str:
        """
        Gera mensagem do alerta usando o template.
        
        Args:
            sensor_tag: Tag do sensor (ex: TEMP-001)
            current_value: Valor atual do sensor
            
        Returns:
            Mensagem formatada
        """
        return self.message_template.format(
            sensor=sensor_tag,
            value=current_value,
            threshold=self.threshold,
            operator=self.operator,
            unit=self.unit or ''
        )
```

**MODIFICAR o model `Rule`:**

Encontre a definição da classe `Rule` e adicione o comentário:

```python
class Rule(models.Model):
    """
    Regra de alertas.
    
    NOVO (v2.0): Suporta múltiplos parâmetros via related_name='parameters'
    DEPRECATED: Campos parameter_key, operator, threshold, duration, severity
                mantidos para compatibilidade com regras antigas.
    """
    
    # ... campos existentes ...
    
    # ⚠️ DEPRECATED: Usar RuleParameter.objects.filter(rule=self) ao invés
    parameter_key = models.CharField(max_length=100, blank=True, null=True)
    operator = models.CharField(max_length=2, blank=True, null=True)
    threshold = models.FloatField(blank=True, null=True)
    duration = models.IntegerField(blank=True, null=True)
    severity = models.CharField(max_length=20, blank=True, null=True)
    
    # ... resto dos campos ...
    
    def is_multi_parameter(self) -> bool:
        """Verifica se é regra multi-parâmetro (novo formato)"""
        return self.parameters.exists()
    
    def get_parameters_list(self):
        """Retorna lista de parâmetros (novo ou antigo formato)"""
        if self.is_multi_parameter():
            return self.parameters.all()
        else:
            # Regra antiga: retorna como se fosse 1 parâmetro
            return [{
                'parameter_key': self.parameter_key,
                'operator': self.operator,
                'threshold': self.threshold,
                'duration': self.duration,
                'severity': self.severity,
            }]
```

### Comandos:

```bash
# Navegar para o backend
cd traksense-backend

# Criar migration
python manage.py makemigrations alerts --name add_rule_parameters

# Aplicar migration
python manage.py migrate alerts

# Verificar tabela criada
python manage.py dbshell
\dt rule_parameters
\d rule_parameters
```

---

## 2️⃣ FASE 2: Serializers

### Arquivo: `apps/alerts/serializers.py`

**ADICIONAR ao final do arquivo:**

```python
class RuleParameterSerializer(serializers.ModelSerializer):
    """Serializer para parâmetros de regras"""
    
    class Meta:
        model = RuleParameter
        fields = [
            'id',
            'parameter_key',
            'variable_key',
            'operator',
            'threshold',
            'duration',
            'severity',
            'message_template',
            'unit',
        ]
        read_only_fields = ['id']
    
    def validate_message_template(self, value):
        """Valida que o template contém pelo menos {value}"""
        if '{value}' not in value:
            raise serializers.ValidationError(
                "Template deve conter pelo menos a variável {value}"
            )
        return value
```

**MODIFICAR o `RuleSerializer`:**

Encontre a classe `RuleSerializer` e modifique:

```python
class RuleSerializer(serializers.ModelSerializer):
    """
    Serializer para regras de alertas.
    
    Suporta dois formatos:
    1. NOVO: Array de parameters (multi-parâmetro)
    2. ANTIGO: Campos parameter_key, operator, etc. (compatibilidade)
    """
    
    # Nested serializer para parâmetros
    parameters = RuleParameterSerializer(many=True, required=False)
    
    class Meta:
        model = Rule
        fields = [
            'id',
            'name',
            'description',
            'equipment',
            'actions',
            'enabled',
            'created_at',
            'updated_at',
            'parameters',  # 🆕 NOVO
            # DEPRECATED (mantidos para leitura)
            'parameter_key',
            'variable_key',
            'operator',
            'threshold',
            'duration',
            'severity',
            'unit',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate(self, data):
        """
        Valida que a regra tem pelo menos 1 parâmetro
        (novo formato OU antigo formato)
        """
        has_new_format = 'parameters' in data and len(data['parameters']) > 0
        has_old_format = all(
            k in data for k in ['parameter_key', 'operator', 'threshold']
        )
        
        if not has_new_format and not has_old_format:
            raise serializers.ValidationError(
                "Regra deve ter pelo menos 1 parâmetro "
                "(use 'parameters' array ou campos antigos)"
            )
        
        return data
    
    def create(self, validated_data):
        """Cria regra com parâmetros aninhados"""
        parameters_data = validated_data.pop('parameters', [])
        
        # Criar regra
        rule = Rule.objects.create(**validated_data)
        
        # Criar parâmetros associados
        for param_data in parameters_data:
            RuleParameter.objects.create(rule=rule, **param_data)
        
        return rule
    
    def update(self, instance, validated_data):
        """Atualiza regra e parâmetros"""
        parameters_data = validated_data.pop('parameters', None)
        
        # Atualizar campos da regra
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Se parameters foi enviado, substituir todos
        if parameters_data is not None:
            # Deletar parâmetros antigos
            instance.parameters.all().delete()
            
            # Criar novos parâmetros
            for param_data in parameters_data:
                RuleParameter.objects.create(rule=instance, **param_data)
        
        return instance
    
    def to_representation(self, instance):
        """
        Customiza resposta para incluir parâmetros mesmo em regras antigas.
        """
        representation = super().to_representation(instance)
        
        # Se não tem parâmetros novos mas tem campos antigos, incluir como array
        if not instance.is_multi_parameter() and instance.parameter_key:
            representation['parameters'] = [{
                'parameter_key': instance.parameter_key,
                'variable_key': instance.variable_key or 'current',
                'operator': instance.operator,
                'threshold': instance.threshold,
                'duration': instance.duration or 5,
                'severity': instance.severity,
                'message_template': f"{{sensor}} está {{operator}} {{threshold}}{{unit}}",
                'unit': instance.unit,
            }]
        
        return representation
```

### Testar Serializer:

```python
# Django shell
python manage.py shell

from apps.alerts.models import Rule, RuleParameter
from apps.alerts.serializers import RuleSerializer

# Testar serialização de regra multi-parâmetro
rule = Rule.objects.first()
serializer = RuleSerializer(rule)
print(serializer.data)

# Testar criação
data = {
    'name': 'Teste Multi-Param',
    'description': 'Teste',
    'equipment': 1,
    'actions': ['EMAIL', 'IN_APP'],
    'enabled': True,
    'parameters': [
        {
            'parameter_key': 'sensor_1',
            'operator': '>',
            'threshold': 25,
            'duration': 5,
            'severity': 'Critical',
            'message_template': 'Temp: {value}°C > {threshold}°C'
        }
    ]
}

serializer = RuleSerializer(data=data)
if serializer.is_valid():
    rule = serializer.save()
    print(f"Regra criada: {rule.id}")
else:
    print(serializer.errors)
```

---

## 3️⃣ FASE 3: Celery Tasks

### Arquivo: `apps/alerts/tasks.py`

**MODIFICAR a task `evaluate_rules_task`:**

```python
from django.utils import timezone
from datetime import timedelta
from apps.alerts.models import Rule, RuleParameter, Alert
from apps.assets.models import Asset, Sensor
from apps.telemetry.models import TelemetryReading

@shared_task
def evaluate_rules_task():
    """
    Avalia todas as regras ativas.
    
    Suporta dois formatos:
    1. Regras novas (multi-parâmetro)
    2. Regras antigas (single-parâmetro)
    """
    
    rules = Rule.objects.filter(enabled=True).select_related('equipment')
    evaluated_count = 0
    alerts_created = 0
    
    for rule in rules:
        try:
            if rule.is_multi_parameter():
                # NOVO FORMATO: Avaliar cada parâmetro
                for param in rule.parameters.all():
                    alert_created = evaluate_rule_parameter(rule, param)
                    if alert_created:
                        alerts_created += 1
                    evaluated_count += 1
            else:
                # FORMATO ANTIGO: Avaliar usando campos da regra
                alert_created = evaluate_single_parameter_rule(rule)
                if alert_created:
                    alerts_created += 1
                evaluated_count += 1
                
        except Exception as e:
            logger.error(f"Erro ao avaliar regra {rule.id}: {e}")
            continue
    
    logger.info(
        f"Avaliação concluída: {evaluated_count} parâmetros avaliados, "
        f"{alerts_created} alertas criados"
    )


def evaluate_rule_parameter(rule: Rule, param: RuleParameter) -> bool:
    """
    Avalia um parâmetro específico de uma regra.
    
    Args:
        rule: Regra pai
        param: Parâmetro a avaliar
        
    Returns:
        True se alerta foi criado, False caso contrário
    """
    
    # 1. Extrair sensor_id do parameter_key (ex: sensor_123 -> 123)
    try:
        sensor_id = int(param.parameter_key.split('_')[1])
    except (IndexError, ValueError):
        logger.error(f"parameter_key inválido: {param.parameter_key}")
        return False
    
    # 2. Buscar sensor
    try:
        sensor = Sensor.objects.get(id=sensor_id)
    except Sensor.DoesNotExist:
        logger.error(f"Sensor {sensor_id} não encontrado")
        return False
    
    # 3. Buscar valor atual do sensor
    current_value = get_sensor_current_value(sensor, param.variable_key)
    if current_value is None:
        logger.warning(f"Sem leitura para sensor {sensor_id}")
        return False
    
    # 4. Avaliar condição
    condition_met = param.evaluate(current_value)
    
    if not condition_met:
        return False
    
    # 5. Verificar cooldown (evitar spam de alertas)
    cooldown_start = timezone.now() - timedelta(minutes=param.duration)
    recent_alert = Alert.objects.filter(
        rule=rule,
        parameter_key=param.parameter_key,
        created_at__gte=cooldown_start,
        status='OPEN'
    ).first()
    
    if recent_alert:
        logger.debug(
            f"Alerta em cooldown: regra={rule.id}, "
            f"param={param.parameter_key}, "
            f"cooldown={param.duration}min"
        )
        return False
    
    # 6. Gerar mensagem usando template
    message = param.generate_message(
        sensor_tag=sensor.tag,
        current_value=current_value
    )
    
    # 7. Criar alerta
    alert = Alert.objects.create(
        rule=rule,
        equipment=rule.equipment,
        parameter_key=param.parameter_key,
        severity=param.severity,
        message=message,
        value=current_value,
        threshold=param.threshold,
        status='OPEN',
    )
    
    logger.info(
        f"Alerta criado: {alert.id} | "
        f"Regra: {rule.name} | "
        f"Sensor: {sensor.tag} | "
        f"Valor: {current_value} {param.operator} {param.threshold}"
    )
    
    # 8. Disparar notificações
    trigger_notifications(alert, rule.actions)
    
    return True


def evaluate_single_parameter_rule(rule: Rule) -> bool:
    """
    Avalia regra antiga (formato single-parameter).
    Mantido para compatibilidade.
    
    Args:
        rule: Regra no formato antigo
        
    Returns:
        True se alerta foi criado, False caso contrário
    """
    
    # Lógica antiga aqui (já existente no código)
    # ...
    pass


def get_sensor_current_value(sensor: Sensor, variable_key: str = 'current') -> float | None:
    """
    Busca o valor atual de um sensor.
    
    Args:
        sensor: Instância do sensor
        variable_key: Variável a buscar (avg, min, max, current)
        
    Returns:
        Valor atual ou None se não houver leitura
    """
    
    # Buscar última leitura nos últimos 10 minutos
    time_threshold = timezone.now() - timedelta(minutes=10)
    
    reading = TelemetryReading.objects.filter(
        sensor=sensor,
        timestamp__gte=time_threshold
    ).order_by('-timestamp').first()
    
    if not reading:
        return None
    
    # Mapear variable_key para campo do modelo
    value_map = {
        'current': reading.value,
        'avg': reading.avg_value if hasattr(reading, 'avg_value') else reading.value,
        'min': reading.min_value if hasattr(reading, 'min_value') else reading.value,
        'max': reading.max_value if hasattr(reading, 'max_value') else reading.value,
    }
    
    return value_map.get(variable_key, reading.value)


def trigger_notifications(alert: Alert, actions: list):
    """
    Dispara notificações para o alerta.
    
    Args:
        alert: Alerta criado
        actions: Lista de ações (EMAIL, IN_APP, SMS, WHATSAPP)
    """
    
    # Lógica de notificações já existente
    # ...
    pass
```

### Testar Task:

```bash
# Django shell
python manage.py shell

from apps.alerts.tasks import evaluate_rules_task

# Executar task manualmente
evaluate_rules_task()

# Verificar alertas criados
from apps.alerts.models import Alert
Alert.objects.all().order_by('-created_at')[:5]
```

---

## 4️⃣ FASE 4: Testes

### Arquivo: `apps/alerts/tests/test_multi_parameter.py`

```python
from django.test import TestCase
from django.utils import timezone
from apps.alerts.models import Rule, RuleParameter, Alert
from apps.assets.models import Asset, Sensor
from apps.telemetry.models import TelemetryReading
from apps.alerts.tasks import evaluate_rules_task


class MultiParameterRuleTestCase(TestCase):
    """Testes para regras multi-parâmetro"""
    
    def setUp(self):
        """Configuração inicial dos testes"""
        
        # Criar asset
        self.asset = Asset.objects.create(
            tag='CH-01',
            name='Chiller 01',
            type='Chiller'
        )
        
        # Criar sensores
        self.sensor_temp = Sensor.objects.create(
            asset=self.asset,
            tag='TEMP-001',
            metric_type='Temperature',
            unit='°C'
        )
        
        self.sensor_pressure = Sensor.objects.create(
            asset=self.asset,
            tag='PRESS-001',
            metric_type='Pressure',
            unit='PSI'
        )
        
        # Criar regra multi-parâmetro
        self.rule = Rule.objects.create(
            name='Chiller CH-01 - Monitoramento',
            description='Temperatura e Pressão',
            equipment=self.asset,
            actions=['EMAIL', 'IN_APP'],
            enabled=True
        )
        
        # Criar parâmetros
        self.param_temp = RuleParameter.objects.create(
            rule=self.rule,
            parameter_key=f'sensor_{self.sensor_temp.id}',
            operator='>',
            threshold=25.0,
            duration=5,
            severity='Critical',
            message_template='🔥 Temperatura crítica: {value}°C (limite: {threshold}°C)',
            unit='°C'
        )
        
        self.param_pressure = RuleParameter.objects.create(
            rule=self.rule,
            parameter_key=f'sensor_{self.sensor_pressure.id}',
            operator='>',
            threshold=300.0,
            duration=10,
            severity='High',
            message_template='⚠️ Pressão elevada: {value} PSI (limite: {threshold} PSI)',
            unit='PSI'
        )
    
    def test_rule_creation(self):
        """Testa criação de regra multi-parâmetro"""
        self.assertEqual(self.rule.parameters.count(), 2)
        self.assertTrue(self.rule.is_multi_parameter())
    
    def test_parameter_evaluation_true(self):
        """Testa avaliação de parâmetro com condição verdadeira"""
        result = self.param_temp.evaluate(30.0)  # 30 > 25
        self.assertTrue(result)
    
    def test_parameter_evaluation_false(self):
        """Testa avaliação de parâmetro com condição falsa"""
        result = self.param_temp.evaluate(20.0)  # 20 > 25
        self.assertFalse(result)
    
    def test_message_generation(self):
        """Testa geração de mensagem com template"""
        message = self.param_temp.generate_message('TEMP-001', 27.5)
        self.assertIn('27.5', message)
        self.assertIn('25', message)
        self.assertIn('TEMP-001', message)
    
    def test_alert_creation_on_threshold_exceed(self):
        """Testa criação de alerta quando threshold é excedido"""
        
        # Criar leitura que excede o threshold
        TelemetryReading.objects.create(
            sensor=self.sensor_temp,
            value=30.0,  # > 25.0
            timestamp=timezone.now()
        )
        
        # Executar task
        evaluate_rules_task()
        
        # Verificar que alerta foi criado
        alerts = Alert.objects.filter(rule=self.rule, parameter_key=f'sensor_{self.sensor_temp.id}')
        self.assertEqual(alerts.count(), 1)
        
        alert = alerts.first()
        self.assertEqual(alert.severity, 'Critical')
        self.assertIn('30.0', alert.message)
    
    def test_cooldown_prevents_duplicate_alerts(self):
        """Testa que cooldown previne alertas duplicados"""
        
        # Criar leitura que excede threshold
        TelemetryReading.objects.create(
            sensor=self.sensor_temp,
            value=30.0,
            timestamp=timezone.now()
        )
        
        # Executar task primeira vez
        evaluate_rules_task()
        self.assertEqual(Alert.objects.count(), 1)
        
        # Executar task segunda vez (dentro do cooldown)
        evaluate_rules_task()
        self.assertEqual(Alert.objects.count(), 1)  # Não deve criar novo alerta
    
    def test_multiple_parameters_create_separate_alerts(self):
        """Testa que parâmetros diferentes criam alertas separados"""
        
        # Leituras que excedem ambos os thresholds
        TelemetryReading.objects.create(
            sensor=self.sensor_temp,
            value=30.0,  # > 25.0
            timestamp=timezone.now()
        )
        
        TelemetryReading.objects.create(
            sensor=self.sensor_pressure,
            value=350.0,  # > 300.0
            timestamp=timezone.now()
        )
        
        # Executar task
        evaluate_rules_task()
        
        # Verificar que 2 alertas foram criados
        alerts = Alert.objects.filter(rule=self.rule)
        self.assertEqual(alerts.count(), 2)
        
        # Verificar mensagens diferentes
        messages = [alert.message for alert in alerts]
        self.assertTrue(any('Temperatura' in msg for msg in messages))
        self.assertTrue(any('Pressão' in msg for msg in messages))
```

### Rodar Testes:

```bash
# Rodar todos os testes
python manage.py test apps.alerts.tests.test_multi_parameter

# Rodar teste específico
python manage.py test apps.alerts.tests.test_multi_parameter.MultiParameterRuleTestCase.test_alert_creation_on_threshold_exceed

# Com verbosidade
python manage.py test apps.alerts.tests.test_multi_parameter -v 2
```

---

## ✅ Validação Final

### Checklist de Validação:

```bash
# 1. Verificar models criados
python manage.py shell
>>> from apps.alerts.models import RuleParameter
>>> RuleParameter.objects.count()
0  # OK, nenhum parâmetro ainda

# 2. Verificar serializer
>>> from apps.alerts.serializers import RuleParameterSerializer
>>> RuleParameterSerializer.Meta.fields
['id', 'parameter_key', 'operator', ...]  # OK

# 3. Criar regra via API
curl -X POST http://localhost:8000/api/alerts/rules/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "Teste Multi-Param",
    "equipment": 1,
    "parameters": [
      {
        "parameter_key": "sensor_1",
        "operator": ">",
        "threshold": 25,
        "duration": 5,
        "severity": "Critical",
        "message_template": "Temp: {value}°C > {threshold}°C"
      }
    ],
    "actions": ["IN_APP"],
    "enabled": true
  }'

# 4. Listar regra
curl http://localhost:8000/api/alerts/rules/1/ \
  -H "Authorization: Bearer $TOKEN"

# 5. Executar task manualmente
python manage.py shell
>>> from apps.alerts.tasks import evaluate_rules_task
>>> evaluate_rules_task()

# 6. Verificar alertas criados
>>> from apps.alerts.models import Alert
>>> Alert.objects.all()
```

---

## 📝 Notas Importantes

### 1. Retrocompatibilidade

✅ **Garantida**: Regras antigas continuam funcionando
- Campos `parameter_key`, `operator`, etc. mantidos no model `Rule`
- Task Celery verifica `rule.is_multi_parameter()` antes de avaliar
- Serializer converte regras antigas para array ao retornar

### 2. Performance

⚠️ **Atenção**: Cada parâmetro dispara query separada
- Otimizar com `select_related('sensor')` no Celery task
- Considerar cache para leituras recentes
- Limitar número de parâmetros por regra (sugestão: max 10)

### 3. Migrations

⚠️ **Rollback**: Se precisar reverter:
```bash
# Listar migrations
python manage.py showmigrations alerts

# Reverter para migration anterior
python manage.py migrate alerts XXXX_previous_migration
```

### 4. Logging

✅ **Recomendado**: Adicionar logs em todas as operações
```python
import logging
logger = logging.getLogger(__name__)

logger.info(f"Avaliando parâmetro {param.id} da regra {rule.id}")
logger.warning(f"Sensor {sensor_id} sem leituras recentes")
logger.error(f"Erro ao avaliar regra {rule.id}: {e}")
```

---

## 🚀 Próximos Passos Após Backend

1. **Testes E2E Frontend + Backend**
   - Criar regra no frontend
   - Verificar no banco de dados
   - Disparar alertas
   - Verificar notificações

2. **Documentação da API**
   - Atualizar Swagger/OpenAPI
   - Adicionar exemplos de payloads
   - Documentar novos campos

3. **Otimizações**
   - Cache de sensores
   - Batch evaluation (avaliar múltiplas regras de uma vez)
   - Índices no banco de dados

4. **Monitoramento**
   - Métricas de performance da task
   - Alertas de falhas na avaliação
   - Dashboard de regras ativas

---

**Autor**: GitHub Copilot  
**Data**: ${new Date().toISOString().split('T')[0]}  
**Versão**: 1.0
