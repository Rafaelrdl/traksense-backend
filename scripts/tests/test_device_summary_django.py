#!/usr/bin/env python
"""
Test DeviceSummary serializer using Django ORM directly
"""
import os
import sys
import json
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
django.setup()

from django_tenants.utils import schema_context
from apps.assets.models import Device, Site
from apps.assets.serializers import DeviceSummarySerializer


def test_device_summary():
    """Test single device summary"""
    print("\n" + "="*80)
    print("🧪 TEST: Device Summary (device_id=8)")
    print("="*80 + "\n")
    
    with schema_context('umc'):
        try:
            device = Device.objects.get(id=8)
            print(f"✅ Found device: {device.name} (mqtt_client_id={device.mqtt_client_id})")
            
            serializer = DeviceSummarySerializer(device)
            data = serializer.data
            
            print(f"\n📊 Device Summary:")
            print(f"   ID: {data['id']}")
            print(f"   Name: {data['name']}")
            print(f"   MQTT Client ID: {data['mqtt_client_id']}")
            print(f"   Device Type: {data['device_type']}")
            print(f"   Status: {data['status']}")
            print(f"   Device Status: {data['device_status']}")
            print(f"   Total Variables: {data['total_variables_count']}")
            print(f"   Online Variables: {data['online_variables_count']}")
            
            if data.get('asset_info'):
                print(f"\n🏢 Asset Info:")
                print(f"   Asset ID: {data['asset_info']['id']}")
                print(f"   Tag: {data['asset_info']['tag']}")
                print(f"   Name: {data['asset_info']['name']}")
                print(f"   Site: {data['asset_info']['site_name']}")
            
            print(f"\n📈 Variables ({len(data['variables'])}):")
            for i, var in enumerate(data['variables'], 1):
                status_icon = "🟢" if var['is_online'] else "🔴"
                print(f"   {i}. {status_icon} {var['name']}")
                print(f"      - Tag: {var['tag']}")
                print(f"      - Type: {var['metric_type']}")
                print(f"      - Unit: {var['unit']}")
                print(f"      - Last Value: {var['last_value']}")
                print(f"      - Last Reading: {var['last_reading_at']}")
            
            print("\n" + "="*80)
            print("✅ DeviceSummarySerializer TEST PASSED!")
            print("="*80 + "\n")
            
            # Print full JSON
            print("📄 Full JSON Response:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
        except Device.DoesNotExist:
            print("❌ ERROR: Device with id=8 not found")
        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()


def test_site_devices_summary():
    """Test site devices summary"""
    print("\n" + "="*80)
    print("🧪 TEST: Site Devices Summary (site_id=7)")
    print("="*80 + "\n")
    
    with schema_context('umc'):
        try:
            site = Site.objects.get(id=7)
            print(f"✅ Found site: {site.name}")
            
            devices = Device.objects.filter(
                asset__site=site
            ).select_related('asset', 'asset__site').prefetch_related('sensors')
            
            print(f"📊 Found {devices.count()} devices in site")
            
            serializer = DeviceSummarySerializer(devices, many=True)
            data = serializer.data
            
            print(f"\n📈 Devices Summary:")
            for i, device_data in enumerate(data, 1):
                print(f"\n   Device {i}: {device_data['name']}")
                print(f"   - MQTT Client ID: {device_data['mqtt_client_id']}")
                print(f"   - Status: {device_data['device_status']}")
                print(f"   - Variables: {device_data['total_variables_count']} total, {device_data['online_variables_count']} online")
                
                if device_data.get('asset_info'):
                    print(f"   - Asset: {device_data['asset_info']['tag']} - {device_data['asset_info']['name']}")
            
            print("\n" + "="*80)
            print("✅ Site Devices Summary TEST PASSED!")
            print("="*80 + "\n")
            
            # Print full JSON for first device
            if data:
                print("📄 Full JSON Response (first device):")
                print(json.dumps(data[0], indent=2, ensure_ascii=False))
            
        except Site.DoesNotExist:
            print("❌ ERROR: Site with id=1 not found")
        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()


if __name__ == '__main__':
    print("\n🚀 Starting Device Summary Tests...")
    
    # Test single device
    test_device_summary()
    
    # Test site devices
    test_site_devices_summary()
    
    print("\n✅ All tests completed!\n")
