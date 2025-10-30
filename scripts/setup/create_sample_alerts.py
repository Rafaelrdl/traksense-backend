"""
Script to create sample rules and alerts for testing.

Usage:
    docker exec traksense-api python create_sample_alerts.py
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.db import connection
from apps.alerts.models import Rule, Alert, NotificationPreference
from apps.assets.models import Asset
from apps.accounts.models import User


def create_sample_rules():
    """Create sample monitoring rules."""
    print("\n" + "="*60)
    print("Creating Sample Rules...")
    print("="*60)
    
    # Set tenant schema
    schema_name = input("Enter tenant schema name (e.g., 'umc'): ").strip()
    connection.set_schema(schema_name)
    
    # Get first equipment
    equipment = Asset.objects.filter(asset_type='DEVICE').first()
    
    if not equipment:
        print("❌ No equipment found. Please create equipment first.")
        return
    
    print(f"\n✅ Found equipment: {equipment.name} ({equipment.asset_tag})")
    
    # Get admin user
    admin = User.objects.filter(is_staff=True).first()
    
    if not admin:
        print("❌ No admin user found.")
        return
    
    # Create Critical Rule - High Temperature
    rule1, created = Rule.objects.get_or_create(
        name="High Temperature Alert",
        equipment=equipment,
        defaults={
            'description': 'Alert when temperature exceeds 30°C',
            'parameter_key': 'temperature',
            'variable_key': 'value',
            'operator': '>',
            'threshold': 30.0,
            'severity': 'CRITICAL',
            'actions': ['EMAIL', 'IN_APP', 'SMS'],
            'enabled': True,
            'cooldown_minutes': 15,
            'created_by': admin,
        }
    )
    
    if created:
        print(f"\n✅ Created rule: {rule1.name}")
        print(f"   - Equipment: {rule1.equipment.name}")
        print(f"   - Condition: {rule1.parameter_key} {rule1.operator} {rule1.threshold}")
        print(f"   - Severity: {rule1.severity}")
        print(f"   - Actions: {', '.join(rule1.actions)}")
    else:
        print(f"\n⚠️  Rule already exists: {rule1.name}")
    
    # Create High Rule - Low Humidity
    rule2, created = Rule.objects.get_or_create(
        name="Low Humidity Alert",
        equipment=equipment,
        defaults={
            'description': 'Alert when humidity drops below 30%',
            'parameter_key': 'humidity',
            'variable_key': 'value',
            'operator': '<',
            'threshold': 30.0,
            'severity': 'HIGH',
            'actions': ['EMAIL', 'IN_APP'],
            'enabled': True,
            'cooldown_minutes': 30,
            'created_by': admin,
        }
    )
    
    if created:
        print(f"\n✅ Created rule: {rule2.name}")
        print(f"   - Equipment: {rule2.equipment.name}")
        print(f"   - Condition: {rule2.parameter_key} {rule2.operator} {rule2.threshold}")
        print(f"   - Severity: {rule2.severity}")
        print(f"   - Actions: {', '.join(rule2.actions)}")
    else:
        print(f"\n⚠️  Rule already exists: {rule2.name}")
    
    # Create Medium Rule - High Power Consumption
    rule3, created = Rule.objects.get_or_create(
        name="High Power Consumption",
        equipment=equipment,
        defaults={
            'description': 'Alert when power consumption exceeds 5000W',
            'parameter_key': 'power',
            'variable_key': 'value',
            'operator': '>',
            'threshold': 5000.0,
            'severity': 'MEDIUM',
            'actions': ['EMAIL'],
            'enabled': True,
            'cooldown_minutes': 60,
            'created_by': admin,
        }
    )
    
    if created:
        print(f"\n✅ Created rule: {rule3.name}")
        print(f"   - Equipment: {rule3.equipment.name}")
        print(f"   - Condition: {rule3.parameter_key} {rule3.operator} {rule3.threshold}")
        print(f"   - Severity: {rule3.severity}")
        print(f"   - Actions: {', '.join(rule3.actions)}")
    else:
        print(f"\n⚠️  Rule already exists: {rule3.name}")
    
    # Create Low Rule - Equipment Offline
    rule4, created = Rule.objects.get_or_create(
        name="Equipment Offline",
        equipment=equipment,
        defaults={
            'description': 'Alert when equipment goes offline',
            'parameter_key': 'status',
            'variable_key': 'online',
            'operator': '==',
            'threshold': 0,
            'severity': 'LOW',
            'actions': ['IN_APP'],
            'enabled': True,
            'cooldown_minutes': 120,
            'created_by': admin,
        }
    )
    
    if created:
        print(f"\n✅ Created rule: {rule4.name}")
        print(f"   - Equipment: {rule4.equipment.name}")
        print(f"   - Condition: {rule4.parameter_key} {rule4.operator} {rule4.threshold}")
        print(f"   - Severity: {rule4.severity}")
        print(f"   - Actions: {', '.join(rule4.actions)}")
    else:
        print(f"\n⚠️  Rule already exists: {rule4.name}")
    
    print("\n" + "="*60)
    print(f"✅ Total rules: {Rule.objects.count()}")
    print("="*60)


def create_sample_alert():
    """Create a sample alert for testing."""
    print("\n" + "="*60)
    print("Creating Sample Alert...")
    print("="*60)
    
    # Set tenant schema
    schema_name = input("Enter tenant schema name (e.g., 'umc'): ").strip()
    connection.set_schema(schema_name)
    
    # Get first rule
    rule = Rule.objects.filter(enabled=True).first()
    
    if not rule:
        print("❌ No rules found. Please create rules first.")
        return
    
    print(f"\n✅ Found rule: {rule.name}")
    
    # Create alert
    alert = Alert.objects.create(
        rule=rule,
        asset_tag=rule.equipment.asset_tag,
        equipment_name=rule.equipment.name,
        severity=rule.severity,
        message=f"Test alert: {rule.parameter_key} exceeded threshold of {rule.threshold}",
        raw_data={
            'test': True,
            'parameter_key': rule.parameter_key,
            'value': rule.threshold + 10,
            'threshold': rule.threshold,
        }
    )
    
    print(f"\n✅ Created alert: {alert.id}")
    print(f"   - Rule: {alert.rule.name}")
    print(f"   - Equipment: {alert.equipment_name} ({alert.asset_tag})")
    print(f"   - Severity: {alert.severity}")
    print(f"   - Message: {alert.message}")
    print(f"   - Status: {'Active' if alert.is_active else 'Inactive'}")
    
    print("\n" + "="*60)
    print(f"✅ Total alerts: {Alert.objects.count()}")
    print("="*60)


def setup_user_preferences():
    """Setup notification preferences for users."""
    print("\n" + "="*60)
    print("Setting up User Notification Preferences...")
    print("="*60)
    
    # Set tenant schema
    schema_name = input("Enter tenant schema name (e.g., 'umc'): ").strip()
    connection.set_schema(schema_name)
    
    users = User.objects.filter(is_active=True)
    
    if not users.exists():
        print("❌ No users found.")
        return
    
    created_count = 0
    
    for user in users:
        pref, created = NotificationPreference.objects.get_or_create(
            user=user,
            defaults={
                'email_enabled': True,
                'push_enabled': True,
                'sound_enabled': True,
                'sms_enabled': False,  # Disabled by default (requires phone)
                'whatsapp_enabled': False,  # Disabled by default (requires phone)
                'critical_alerts': True,
                'high_alerts': True,
                'medium_alerts': True,
                'low_alerts': False,  # Low priority disabled by default
            }
        )
        
        if created:
            created_count += 1
            print(f"✅ Created preferences for: {user.email}")
        else:
            print(f"⚠️  Preferences already exist for: {user.email}")
    
    print("\n" + "="*60)
    print(f"✅ Total user preferences: {NotificationPreference.objects.count()}")
    print(f"✅ Created: {created_count}")
    print("="*60)


def main():
    """Main function."""
    print("\n" + "="*60)
    print("SAMPLE ALERTS DATA CREATION")
    print("="*60)
    print("\nOptions:")
    print("1. Create sample rules")
    print("2. Create sample alert")
    print("3. Setup user preferences")
    print("4. All of the above")
    print("5. Exit")
    
    choice = input("\nEnter your choice (1-5): ").strip()
    
    if choice == '1':
        create_sample_rules()
    elif choice == '2':
        create_sample_alert()
    elif choice == '3':
        setup_user_preferences()
    elif choice == '4':
        create_sample_rules()
        create_sample_alert()
        setup_user_preferences()
    elif choice == '5':
        print("Exiting...")
        sys.exit(0)
    else:
        print("❌ Invalid choice")
        sys.exit(1)
    
    print("\n✅ Done!")


if __name__ == '__main__':
    main()
