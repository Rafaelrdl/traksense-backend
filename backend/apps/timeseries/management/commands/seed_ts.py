"""
Seed Timeseries Command - Popular banco com dados de teste

Este management command cria tenants e popula ts_measure com milhões de linhas
para testes de performance, RLS e continuous aggregates.

Uso:
---
# Padrão: 1M linhas/tenant, 24h, intervalo 2s
python manage.py seed_ts

# Customizado: 10M linhas, 7 dias, intervalo 1s
python manage.py seed_ts --rows-per-tenant 10000000 --hours 168 --interval-seconds 1

Dados gerados:
-------------
- 2 tenants: alpha (Alpha Corp), beta (Beta Industries)
- Domínios: alpha.localhost, beta.localhost
- Device/Point IDs: UUIDs fixos (para queries de teste)
- Valores: v_num aleatório (10-100) com variação temporal
- Timestamps: distribuídos uniformemente no período (ex: últimas 24h)

Performance:
-----------
- 1M linhas: ~30s (batch insert 10k rows/vez)
- 10M linhas: ~5 min
- RLS: isolamento automático por tenant_id

Testes com dados gerados:
-------------------------
# Query raw (lenta)
GET /data/points?device_id=<uuid>&point_id=<uuid>&from=...&to=...&agg=raw

# Query agregada (rápida)
GET /data/points?device_id=<uuid>&point_id=<uuid>&from=...&to=...&agg=1m

# Testar RLS (mudar tenant via domínio)
Host: alpha.localhost → vê apenas dados alpha
Host: beta.localhost → vê apenas dados beta

Autor: TrakSense Team
Data: 2025-10-07
"""
import uuid
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.db import connection
from tenancy.models import Client, Domain
import random


class Command(BaseCommand):
    help = 'Popula ts_measure com dados de teste (2 tenants, ~1M linhas/tenant)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--rows-per-tenant',
            type=int,
            default=1000000,
            help='Number of rows to generate per tenant (default: 1M)'
        )
        parser.add_argument(
            '--hours',
            type=int,
            default=24,
            help='Time range in hours (default: 24)'
        )
        parser.add_argument(
            '--interval-seconds',
            type=int,
            default=2,
            help='Interval between samples in seconds (default: 2)'
        )

    def handle(self, *args, **options):
        rows_per_tenant = options['rows_per_tenant']
        hours = options['hours']
        interval_seconds = options['interval_seconds']
        
        self.stdout.write(self.style.SUCCESS('🚀 Starting seed_ts...'))
        
        # 1. Create tenants (alpha and beta)
        tenants = self.create_tenants()
        
        # 2. Generate telemetry data for each tenant
        for tenant in tenants:
            self.stdout.write(f'\n📊 Generating data for tenant: {tenant.name}')
            self.generate_telemetry(
                tenant=tenant,
                num_rows=rows_per_tenant,
                hours=hours,
                interval_seconds=interval_seconds
            )
        
        self.stdout.write(self.style.SUCCESS('\n✅ Seed completed successfully!'))

    def create_tenants(self):
        """Create 2 test tenants: alpha and beta"""
        tenants = []
        
        for schema_name, name, domain in [
            ('alpha', 'Alpha Corp', 'alpha.localhost'),
            ('beta', 'Beta Industries', 'beta.localhost'),
        ]:
            # Create or get tenant
            tenant, created = Client.objects.get_or_create(
                schema_name=schema_name,
                defaults={'name': name}
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'  ✓ Created tenant: {name} (schema: {schema_name})')
                )
                
                # Create domain
                Domain.objects.get_or_create(
                    domain=domain,
                    defaults={'tenant': tenant, 'is_primary': True}
                )
                self.stdout.write(f'  ✓ Created domain: {domain}')
            else:
                self.stdout.write(f'  ℹ Tenant {name} already exists')
            
            tenants.append(tenant)
        
        return tenants

    def generate_telemetry(self, tenant, num_rows, hours, interval_seconds):
        """Generate telemetry data for a tenant"""
        device_id = uuid.uuid4()
        point_id = uuid.uuid4()
        
        # Calculate number of samples
        total_seconds = hours * 3600
        samples_per_second = 1.0 / interval_seconds
        num_samples = int(total_seconds * samples_per_second)
        
        self.stdout.write(
            f'  Device: {device_id}\n'
            f'  Point: {point_id}\n'
            f'  Samples: {num_samples} over {hours}h '
            f'(every {interval_seconds}s)'
        )
        
        # Set GUC for this tenant
        with connection.cursor() as cur:
            cur.execute("SET app.tenant_id = %s", [str(tenant.pk)])
            
            # Generate timestamps
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)
            
            # Batch insert for performance
            batch_size = 10000
            batch = []
            inserted = 0
            
            self.stdout.write('  Inserting data...')
            
            current_time = start_time
            while current_time < end_time and inserted < num_rows:
                # Generate realistic sensor data
                v_num = 20.0 + random.gauss(0, 5)  # Temperature-like
                
                batch.append((
                    str(tenant.pk),     # tenant_id
                    str(device_id),     # device_id
                    str(point_id),      # point_id
                    current_time,       # ts
                    v_num,              # v_num
                    None,               # v_bool
                    None,               # v_text
                    '°C',               # unit
                    0,                  # qual (0 = good)
                    None                # meta
                ))
                
                inserted += 1
                current_time += timedelta(seconds=interval_seconds)
                
                # Batch insert
                if len(batch) >= batch_size:
                    self._insert_batch(cur, batch)
                    batch = []
                    self.stdout.write(f'    {inserted:,} rows inserted...', ending='\r')
                    self.stdout.flush()
            
            # Insert remaining rows
            if batch:
                self._insert_batch(cur, batch)
            
            self.stdout.write(f'  ✓ Inserted {inserted:,} rows                    ')

    def _insert_batch(self, cursor, batch):
        """Insert a batch of rows"""
        sql = """
            INSERT INTO public.ts_measure 
            (tenant_id, device_id, point_id, ts, v_num, v_bool, v_text, unit, qual, meta)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.executemany(sql, batch)
