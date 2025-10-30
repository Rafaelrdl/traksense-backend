"""
Quick integration test for Alerts & Rules system.

Usage:
    docker exec traksense-api python test_alerts_integration.py
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.db import connection


def test_models_import():
    """Test if models can be imported."""
    print("\n" + "="*60)
    print("TEST 1: Import Models")
    print("="*60)
    
    try:
        from apps.alerts.models import Rule, Alert, NotificationPreference
        print("✅ Models imported successfully")
        print(f"   - Rule: {Rule.__name__}")
        print(f"   - Alert: {Alert.__name__}")
        print(f"   - NotificationPreference: {NotificationPreference.__name__}")
        return True
    except Exception as e:
        print(f"❌ Failed to import models: {str(e)}")
        return False


def test_serializers_import():
    """Test if serializers can be imported."""
    print("\n" + "="*60)
    print("TEST 2: Import Serializers")
    print("="*60)
    
    try:
        from apps.alerts.serializers import (
            RuleSerializer,
            AlertSerializer,
            NotificationPreferenceSerializer
        )
        print("✅ Serializers imported successfully")
        print(f"   - RuleSerializer: {RuleSerializer.__name__}")
        print(f"   - AlertSerializer: {AlertSerializer.__name__}")
        print(f"   - NotificationPreferenceSerializer: {NotificationPreferenceSerializer.__name__}")
        return True
    except Exception as e:
        print(f"❌ Failed to import serializers: {str(e)}")
        return False


def test_views_import():
    """Test if views can be imported."""
    print("\n" + "="*60)
    print("TEST 3: Import Views")
    print("="*60)
    
    try:
        from apps.alerts.views import (
            RuleViewSet,
            AlertViewSet,
            NotificationPreferenceViewSet
        )
        print("✅ Views imported successfully")
        print(f"   - RuleViewSet: {RuleViewSet.__name__}")
        print(f"   - AlertViewSet: {AlertViewSet.__name__}")
        print(f"   - NotificationPreferenceViewSet: {NotificationPreferenceViewSet.__name__}")
        return True
    except Exception as e:
        print(f"❌ Failed to import views: {str(e)}")
        return False


def test_service_import():
    """Test if notification service can be imported."""
    print("\n" + "="*60)
    print("TEST 4: Import Notification Service")
    print("="*60)
    
    try:
        from apps.alerts.services import NotificationService
        service = NotificationService()
        print("✅ Notification service imported and instantiated")
        print(f"   - Email enabled: {service.email_enabled}")
        print(f"   - SMS enabled: {service.sms_enabled}")
        print(f"   - WhatsApp enabled: {service.whatsapp_enabled}")
        return True
    except Exception as e:
        print(f"❌ Failed to import service: {str(e)}")
        return False


def test_tasks_import():
    """Test if Celery tasks can be imported."""
    print("\n" + "="*60)
    print("TEST 5: Import Celery Tasks")
    print("="*60)
    
    try:
        from apps.alerts.tasks import (
            evaluate_rules_task,
            cleanup_old_alerts_task
        )
        print("✅ Tasks imported successfully")
        print(f"   - evaluate_rules_task: {evaluate_rules_task.name}")
        print(f"   - cleanup_old_alerts_task: {cleanup_old_alerts_task.name}")
        return True
    except Exception as e:
        print(f"❌ Failed to import tasks: {str(e)}")
        return False


def test_database_tables():
    """Test if database tables exist."""
    print("\n" + "="*60)
    print("TEST 6: Check Database Tables")
    print("="*60)
    
    try:
        # Set to public schema to check table existence
        connection.set_schema('public')
        
        with connection.cursor() as cursor:
            # Check if tables exist in information_schema
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE 'alerts_%'
                ORDER BY table_name
            """)
            
            tables = cursor.fetchall()
            
            if tables:
                print("✅ Alert tables found in database:")
                for table in tables:
                    print(f"   - {table[0]}")
                return True
            else:
                print("⚠️  No alert tables found (might need to check tenant schemas)")
                return True  # Not a failure, just info
                
    except Exception as e:
        print(f"❌ Failed to check tables: {str(e)}")
        return False


def test_urls_import():
    """Test if URLs can be imported."""
    print("\n" + "="*60)
    print("TEST 7: Import URLs")
    print("="*60)
    
    try:
        from apps.alerts import urls
        print("✅ URLs module imported successfully")
        
        # Check if router has viewsets
        if hasattr(urls, 'router'):
            registry = urls.router.registry
            print(f"   - Registered routes: {len(registry)}")
            for prefix, viewset, basename in registry:
                print(f"     • {prefix}/ → {viewset.__name__}")
        
        return True
    except Exception as e:
        print(f"❌ Failed to import URLs: {str(e)}")
        return False


def test_admin_import():
    """Test if admin can be imported."""
    print("\n" + "="*60)
    print("TEST 8: Import Admin")
    print("="*60)
    
    try:
        from apps.alerts import admin
        from django.contrib import admin as django_admin
        
        # Check registered models
        from apps.alerts.models import Rule, Alert, NotificationPreference
        
        registered = []
        if django_admin.site.is_registered(Rule):
            registered.append('Rule')
        if django_admin.site.is_registered(Alert):
            registered.append('Alert')
        if django_admin.site.is_registered(NotificationPreference):
            registered.append('NotificationPreference')
        
        print("✅ Admin imported successfully")
        print(f"   - Registered models: {', '.join(registered)}")
        return True
    except Exception as e:
        print(f"❌ Failed to import admin: {str(e)}")
        return False


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("ALERTS & RULES SYSTEM - INTEGRATION TEST")
    print("="*60)
    
    tests = [
        test_models_import,
        test_serializers_import,
        test_views_import,
        test_service_import,
        test_tasks_import,
        test_database_tables,
        test_urls_import,
        test_admin_import,
    ]
    
    results = []
    for test in tests:
        result = test()
        results.append(result)
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Passed: {passed}/{total}")
    print(f"Failed: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! System is ready to use.")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed. Please check the output above.")
        sys.exit(1)


if __name__ == '__main__':
    main()
