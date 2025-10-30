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
    
    Args:
        rule: Rule model instance
    
    Returns:
        Alert instance if condition is met and alert was created, None otherwise
    """
    from apps.alerts.models import Alert
    from apps.ingest.models import Reading
    
    # Check cooldown - don't create multiple alerts too quickly
    cooldown_period = timedelta(minutes=rule.duration)  # Usar 'duration' em vez de cooldown_minutes
    last_alert = Alert.objects.filter(
        rule=rule,
        triggered_at__gte=timezone.now() - cooldown_period
    ).first()
    
    if last_alert:
        logger.debug(
            f"Rule {rule.id} is in cooldown period "
            f"(last alert at {last_alert.triggered_at})"
        )
        return None
    
    # Get latest telemetry reading for this equipment
    # Regras usam parameter_key que corresponde ao sensor_id nas readings
    try:
        # Buscar reading pelo sensor_id (parameter_key da regra)
        # e device_id (asset_tag do equipment)
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
        
        # Check if reading is recent enough (within last 15 minutes)
        if latest_reading.ts < timezone.now() - timedelta(minutes=15):
            logger.debug(
                f"Latest telemetry reading is too old "
                f"({latest_reading.ts}) for rule {rule.id}"
            )
            return None
        
        # Get the value to compare
        value = latest_reading.value
        
        # Evaluate the condition
        condition_met = evaluate_condition(
            value,
            rule.operator,
            rule.threshold
        )
        
        if not condition_met:
            logger.debug(
                f"Rule {rule.id} condition not met: "
                f"{value} {rule.operator} {rule.threshold} = False"
            )
            return None
        
        # Condition is met - create alert
        alert = Alert.objects.create(
            rule=rule,
            asset_tag=rule.equipment.asset_tag,
            equipment_name=rule.equipment.name,
            severity=rule.severity,
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
            f"Alert {alert.id} created for rule {rule.id}: "
            f"{value} {rule.operator} {rule.threshold}"
        )
        
        return alert
        
    except Exception as e:
        logger.error(
            f"Error evaluating rule {rule.id} for equipment "
            f"{rule.equipment.asset_tag}: {str(e)}"
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


def generate_alert_message(rule, reading, value):
    """
    Generate a human-readable alert message.
    
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
