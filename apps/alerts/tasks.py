"""
Celery tasks for Alerts & Rules system.

This module contains periodic tasks that:
1. Evaluate rules against telemetry data
2. Create alerts when thresholds are exceeded
3. Send notifications to users
"""

import logging
from datetime import timedelta
from django.utils import timezone
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name='alerts.evaluate_rules')
def evaluate_rules_task():
    """
    Periodic task that evaluates all enabled rules against current telemetry data.
    
    This task should be scheduled to run at regular intervals (e.g., every 1-5 minutes).
    
    For each rule:
    1. Get the latest telemetry data for the equipment
    2. Check if the condition is met (threshold exceeded)
    3. Check if enough time has passed since last alert (cooldown)
    4. Create alert if condition is met
    5. Send notifications to users
    """
    from apps.alerts.models import Rule
    from apps.alerts.services import NotificationService
    
    logger.info("Starting rule evaluation task...")
    
    # Get all enabled rules
    rules = Rule.objects.filter(enabled=True).select_related('equipment')
    
    if not rules.exists():
        logger.info("No enabled rules found")
        return {
            'evaluated': 0,
            'triggered': 0,
            'errors': 0
        }
    
    evaluated_count = 0
    triggered_count = 0
    error_count = 0
    
    notification_service = NotificationService()
    
    for rule in rules:
        try:
            evaluated_count += 1
            
            # Evaluate the rule
            alert = evaluate_single_rule(rule)
            
            if alert:
                triggered_count += 1
                logger.info(
                    f"Alert {alert.id} triggered for rule {rule.id} "
                    f"({rule.name}) on equipment {rule.equipment.asset_tag}"
                )
                
                # Send notifications
                try:
                    results = notification_service.send_alert_notifications(alert)
                    logger.info(
                        f"Notifications sent for alert {alert.id}: "
                        f"{len(results['sent'])} sent, "
                        f"{len(results['failed'])} failed, "
                        f"{len(results['skipped'])} skipped"
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to send notifications for alert {alert.id}: {str(e)}"
                    )
                    error_count += 1
                    
        except Exception as e:
            logger.error(f"Error evaluating rule {rule.id}: {str(e)}")
            error_count += 1
    
    logger.info(
        f"Rule evaluation completed: "
        f"{evaluated_count} evaluated, "
        f"{triggered_count} triggered, "
        f"{error_count} errors"
    )
    
    return {
        'evaluated': evaluated_count,
        'triggered': triggered_count,
        'errors': error_count
    }


def evaluate_single_rule(rule):
    """
    Evaluate a single rule against current telemetry data.
    Suporta tanto regras com múltiplos parâmetros quanto regras antigas (formato único).
    
    Args:
        rule: Rule model instance
    
    Returns:
        Alert instance if condition is met and alert was created, None otherwise
    """
    from apps.alerts.models import Alert
    from apps.ingest.models import Reading
    
    # Verificar se a regra tem parâmetros novos (múltiplos) ou usa formato antigo
    parameters = rule.parameters.all()
    
    # Se não tem parâmetros novos mas tem campos antigos, avaliar no formato antigo
    if not parameters.exists() and rule.parameter_key:
        return evaluate_single_rule_legacy(rule)
    
    # Avaliar cada parâmetro da regra
    alerts_created = []
    
    for param in parameters:
        # Check cooldown por parâmetro
        cooldown_period = timedelta(minutes=param.duration)
        last_alert = Alert.objects.filter(
            rule=rule,
            parameter_key=param.parameter_key,
            triggered_at__gte=timezone.now() - cooldown_period
        ).first()
        
        if last_alert:
            logger.debug(
                f"Rule {rule.id} parameter {param.parameter_key} is in cooldown period "
                f"(last alert at {last_alert.triggered_at})"
            )
            continue
    
        # Buscar reading pelo sensor_id (parameter_key do parâmetro)
        try:
            latest_reading = Reading.objects.filter(
                device_id=rule.equipment.asset_tag,
                sensor_id=param.parameter_key
            ).order_by('-ts').first()
            
            if not latest_reading:
                logger.debug(
                    f"No telemetry data found for equipment {rule.equipment.asset_tag} "
                    f"parameter {param.parameter_key}"
                )
                continue
            
            # Check if reading is recent enough (within last 15 minutes)
            if latest_reading.ts < timezone.now() - timedelta(minutes=15):
                logger.debug(
                    f"Latest telemetry reading is too old "
                    f"({latest_reading.ts}) for rule {rule.id} param {param.parameter_key}"
                )
                continue
            
            # Get the value to compare
            value = latest_reading.value
            
            # Evaluate the condition
            condition_met = evaluate_condition(
                value,
                param.operator,
                param.threshold
            )
            
            if not condition_met:
                logger.debug(
                    f"Rule {rule.id} parameter {param.parameter_key} condition not met: "
                    f"{value} {param.operator} {param.threshold} = False"
                )
                continue
            
            # Condition is met - create alert
            # Gerar mensagem a partir do template
            message = generate_alert_message_from_template(
                param.message_template,
                param,
                latest_reading,
                value
            )
            
            alert = Alert.objects.create(
                rule=rule,
                asset_tag=rule.equipment.asset_tag,
                equipment_name=rule.equipment.name,
                severity=param.severity,
                parameter_key=param.parameter_key,
                parameter_value=value,
                threshold=param.threshold,
                message=message,
                triggered_at=timezone.now(),
                raw_data={
                    'parameter_key': param.parameter_key,
                    'variable_key': param.variable_key,
                    'value': value,
                    'threshold': param.threshold,
                    'operator': param.operator,
                    'unit': param.unit,
                    'timestamp': latest_reading.ts.isoformat(),
                }
            )
            
            logger.info(
                f"Alert {alert.id} created for rule {rule.id} parameter {param.parameter_key}: "
                f"{value} {param.operator} {param.threshold}"
            )
            
            alerts_created.append(alert)
            
        except Exception as e:
            logger.error(
                f"Error evaluating rule {rule.id} parameter {param.parameter_key}: {str(e)}"
            )
            continue
    
    # Retornar o primeiro alerta criado (ou None se nenhum foi criado)
    return alerts_created[0] if alerts_created else None


def evaluate_single_rule_legacy(rule):
    """
    Evaluate a single rule in the old format (single parameter).
    Mantido para compatibilidade com regras antigas.
    """
    from apps.alerts.models import Alert
    from apps.ingest.models import Reading
    
    # Check cooldown
    cooldown_period = timedelta(minutes=rule.duration)
    last_alert = Alert.objects.filter(
        rule=rule,
        triggered_at__gte=timezone.now() - cooldown_period
    ).first()
    
    if last_alert:
        logger.debug(
            f"Rule {rule.id} is in cooldown period (last alert at {last_alert.triggered_at})"
        )
        return None
    
    try:
        latest_reading = Reading.objects.filter(
            device_id=rule.equipment.asset_tag,
            sensor_id=rule.parameter_key
        ).order_by('-ts').first()
        
        if not latest_reading:
            logger.debug(
                f"No telemetry data found for equipment {rule.equipment.asset_tag} "
                f"parameter {rule.parameter_key}"
            )
            return None
        
        if latest_reading.ts < timezone.now() - timedelta(minutes=15):
            logger.debug(
                f"Latest telemetry reading is too old ({latest_reading.ts}) for rule {rule.id}"
            )
            return None
        
        value = latest_reading.value
        
        condition_met = evaluate_condition(value, rule.operator, rule.threshold)
        
        if not condition_met:
            logger.debug(
                f"Rule {rule.id} condition not met: {value} {rule.operator} {rule.threshold} = False"
            )
            return None
        
        alert = Alert.objects.create(
            rule=rule,
            asset_tag=rule.equipment.asset_tag,
            equipment_name=rule.equipment.name,
            severity=rule.severity,
            parameter_key=rule.parameter_key,
            parameter_value=value,
            threshold=rule.threshold,
            message=generate_alert_message(rule, latest_reading, value),
            triggered_at=timezone.now(),
            raw_data={
                'parameter_key': rule.parameter_key,
                'variable_key': rule.variable_key,
                'value': value,
                'threshold': rule.threshold,
                'operator': rule.operator,
                'timestamp': latest_reading.ts.isoformat(),
            }
        )
        
        logger.info(
            f"Alert {alert.id} created for rule {rule.id}: {value} {rule.operator} {rule.threshold}"
        )
        
        return alert
        
    except Exception as e:
        logger.error(
            f"Error evaluating rule {rule.id} for equipment {rule.equipment.asset_tag}: {str(e)}"
        )
        return None


def evaluate_condition(value, operator, threshold):
    """
    Evaluate a condition against a threshold.
    
    Args:
        value: Current value from telemetry
        operator: Comparison operator (>, <, >=, <=, ==, !=)
        threshold: Threshold value to compare against
    
    Returns:
        True if condition is met, False otherwise
    """
    try:
        # Convert to float for numeric comparison
        value_float = float(value)
        threshold_float = float(threshold)
        
        if operator == '>':
            return value_float > threshold_float
        elif operator == '<':
            return value_float < threshold_float
        elif operator == '>=':
            return value_float >= threshold_float
        elif operator == '<=':
            return value_float <= threshold_float
        elif operator == '==':
            return value_float == threshold_float
        elif operator == '!=':
            return value_float != threshold_float
        else:
            logger.error(f"Unknown operator: {operator}")
            return False
            
    except (ValueError, TypeError) as e:
        logger.error(f"Error comparing values: {value} {operator} {threshold} - {str(e)}")
        return False


def generate_alert_message_from_template(template, param, reading, value):
    """
    Generate alert message from template with variable substitution.
    
    Args:
        template: Message template string with {variables}
        param: RuleParameter instance
        reading: Reading instance
        value: Current value that triggered the alert
    
    Returns:
        Alert message string with variables replaced
    """
    try:
        # Mapeamento de operadores para texto
        operator_map = {
            '>': 'maior que',
            '>=': 'maior ou igual a',
            '<': 'menor que',
            '<=': 'menor ou igual a',
            '==': 'igual a',
            '!=': 'diferente de',
        }
        
        # Substituir variáveis no template
        message = template
        message = message.replace('{sensor}', param.parameter_key)
        message = message.replace('{value}', str(value))
        message = message.replace('{threshold}', str(param.threshold))
        message = message.replace('{operator}', operator_map.get(param.operator, param.operator))
        message = message.replace('{unit}', param.unit or '')
        
        return message
        
    except Exception as e:
        logger.error(f"Error generating alert message from template: {str(e)}")
        return f"Alerta disparado para parâmetro {param.parameter_key}"


def generate_alert_message(rule, reading, value):
    """
    Generate a human-readable alert message (legacy format).
    
    Args:
        rule: Rule model instance
        reading: TelemetryReading instance
        value: Current value that triggered the alert
    
    Returns:
        Alert message string
    """
    try:
        # Get unit from reading data if available
        unit = reading.data.get('unit', '') if hasattr(reading, 'data') else ''
        
        message = (
            f"{rule.parameter_key} value of {value}{unit} "
            f"is {rule.operator} threshold of {rule.threshold}{unit} "
            f"on equipment {rule.equipment.name} ({rule.equipment.asset_tag})"
        )
        
        return message
        
    except Exception as e:
        logger.error(f"Error generating alert message: {str(e)}")
        return f"Alert triggered for rule: {rule.name}"


@shared_task(name='alerts.cleanup_old_alerts')
def cleanup_old_alerts_task(days=90):
    """
    Clean up old resolved alerts to keep the database lean.
    
    Args:
        days: Number of days to keep resolved alerts (default: 90)
    
    Returns:
        Number of alerts deleted
    """
    from apps.alerts.models import Alert
    
    cutoff_date = timezone.now() - timedelta(days=days)
    
    # Delete old resolved alerts
    deleted_count, _ = Alert.objects.filter(
        resolved=True,
        resolved_at__lt=cutoff_date
    ).delete()
    
    logger.info(f"Cleaned up {deleted_count} old alerts (resolved before {cutoff_date})")
    
    return deleted_count
