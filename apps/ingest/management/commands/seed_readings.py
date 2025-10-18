"""
Management command to seed Reading data for development/testing.

Creates sample sensor readings for continuous aggregate validation.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import connection
from datetime import timedelta
import random

from apps.ingest.models import Reading
from apps.tenants.models import Tenant


class Command(BaseCommand):
    help = 'Seed Reading data for development (TimescaleDB Continuous Aggregates validation)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tenant',
            type=str,
            default='uberlandia_medical_center',
            help='Tenant schema name (default: uberlandia_medical_center)'
        )
        parser.add_argument(
            '--hours',
            type=int,
            default=24,
            help='Hours of data to generate (default: 24)'
        )
        parser.add_argument(
            '--interval',
            type=int,
            default=5,
            help='Interval between readings in seconds (default: 5)'
        )

    def handle(self, *args, **options):
        tenant_schema = options['tenant']
        hours = options['hours']
        interval_seconds = options['interval']

        # Get tenant
        try:
            tenant = Tenant.objects.get(schema_name=tenant_schema)
        except Tenant.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'❌ Tenant "{tenant_schema}" not found'))
            return

        # Switch to tenant schema
        connection.set_tenant(tenant)
        self.stdout.write(self.style.SUCCESS(f'📊 Seeding readings for tenant: {tenant.name} ({tenant_schema})'))

        # Generate readings
        devices = ['device_001', 'device_002', 'device_003']
        sensors_per_device = {
            'device_001': ['temp_01', 'humidity_01', 'pressure_01'],
            'device_002': ['temp_02', 'humidity_02'],
            'device_003': ['temp_03', 'humidity_03', 'pressure_03', 'co2_03'],
        }

        end_time = timezone.now()
        start_time = end_time - timedelta(hours=hours)
        current_time = start_time

        readings = []
        count = 0

        self.stdout.write(f'⏱️  Generating data from {start_time} to {end_time}...')

        while current_time <= end_time:
            for device_id in devices:
                for sensor_id in sensors_per_device[device_id]:
                    # Generate realistic values based on sensor type
                    if 'temp' in sensor_id:
                        base_value = 22.0
                        noise = random.uniform(-2.0, 2.0)
                        labels = {'unit': 'celsius', 'location': 'room_a'}
                    elif 'humidity' in sensor_id:
                        base_value = 55.0
                        noise = random.uniform(-5.0, 5.0)
                        labels = {'unit': 'percent', 'location': 'room_a'}
                    elif 'pressure' in sensor_id:
                        base_value = 1013.0
                        noise = random.uniform(-3.0, 3.0)
                        labels = {'unit': 'hPa', 'location': 'room_a'}
                    elif 'co2' in sensor_id:
                        base_value = 400.0
                        noise = random.uniform(-50.0, 50.0)
                        labels = {'unit': 'ppm', 'location': 'room_a'}
                    else:
                        base_value = 50.0
                        noise = random.uniform(-10.0, 10.0)
                        labels = {}

                    value = round(base_value + noise, 2)

                    readings.append(Reading(
                        device_id=device_id,
                        sensor_id=sensor_id,
                        value=value,
                        labels=labels,
                        ts=current_time,
                    ))
                    count += 1

            current_time += timedelta(seconds=interval_seconds)

            # Bulk insert every 1000 readings for performance
            if len(readings) >= 1000:
                Reading.objects.bulk_create(readings)
                self.stdout.write(f'  ✅ Inserted {count} readings...')
                readings = []

        # Insert remaining readings
        if readings:
            Reading.objects.bulk_create(readings)

        self.stdout.write(self.style.SUCCESS(f'✅ Seeded {count} readings successfully!'))
        self.stdout.write(f'📈 Data range: {start_time} → {end_time}')
        self.stdout.write(f'🔧 Devices: {len(devices)}')
        self.stdout.write(f'📡 Sensors: {sum(len(s) for s in sensors_per_device.values())}')
        self.stdout.write(f'⏱️  Interval: {interval_seconds}s')
        
        # Validate hypertable
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT table_name, hypertable_name 
                FROM timescaledb_information.hypertables 
                WHERE hypertable_name = 'reading';
            """)
            hypertable = cursor.fetchone()
            if hypertable:
                self.stdout.write(self.style.SUCCESS(f'✅ Hypertable confirmed: {hypertable[1]}'))
            else:
                self.stdout.write(self.style.WARNING('⚠️  Hypertable not found - run migrations'))
        
        # Check continuous aggregates
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT view_name, materialized_only
                FROM timescaledb_information.continuous_aggregates
                WHERE view_name LIKE 'reading_%';
            """)
            cas = cursor.fetchall()
            if cas:
                self.stdout.write(self.style.SUCCESS(f'✅ Continuous Aggregates: {len(cas)}'))
                for ca in cas:
                    self.stdout.write(f'   - {ca[0]}')
            else:
                self.stdout.write(self.style.WARNING('⚠️  No Continuous Aggregates - run migrations'))

        self.stdout.write(self.style.SUCCESS('\n🎉 Seeding complete!'))
        self.stdout.write('\n📖 Test API endpoints:')
        self.stdout.write(f'   curl "http://umc.localhost:8000/api/telemetry/readings/?sensor_id=temp_01&limit=10"')
        self.stdout.write(f'   curl "http://umc.localhost:8000/api/telemetry/series/?bucket=1m&sensor_id=temp_01&limit=50"')
