"""
Management Command: seed_demo_je02

Cria seed completo de dados demo para JE02:
- Tenant 'demo'
- Site 'plant-01'
- 7 Devices: INV-01, INV-02, ..., INV-07
- DeviceTemplate: inverter_je02_v1
- Provisioning EMQX com credenciais + ACL
- DashboardConfig instanciado do DashboardTemplate

Uso:
    # Executar seed:
    docker compose exec api python manage.py seed_demo_je02
    
    # Limpar e recriar:
    docker compose exec api python manage.py seed_demo_je02 --clean

Autor: TrakSense Team
Data: 2025-10-08 (Fase D - JE02)
"""

import json
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction, connection
from apps.tenancy.models import Client, Domain
from apps.templates.models import DeviceTemplate as GlobalDeviceTemplate, DashboardTemplate as GlobalDashboardTemplate
from apps.devices.models import Device, Point, DeviceTemplate
from apps.dashboards.models import DashboardConfig
from apps.devices.services import provision_emqx_for_device


class Command(BaseCommand):
    """
    Management command para criar seed de dados demo JE02.
    """
    
    help = (
        "Cria seed completo de dados demo para JE02:\n"
        "- Tenant 'demo'\n"
        "- Site 'plant-01'\n"
        "- 7 Devices: INV-01, INV-02, ..., INV-07\n"
        "- Provisioning EMQX + DashboardConfig\n\n"
        "Uso: python manage.py seed_demo_je02"
    )
    
    def add_arguments(self, parser):
        """Define argumentos do comando."""
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Limpar dados existentes antes de criar novos'
        )
    
    def handle(self, *args, **options):
        """Executa o comando de seed."""
        clean = options['clean']
        
        self.stdout.write("="*70)
        self.stdout.write(self.style.SUCCESS("🌱 SEED DEMO JE02 - Inversores IoT"))
        self.stdout.write("="*70)
        self.stdout.write("")
        
        try:
            # Step 1: Criar/obter tenant 'demo'
            tenant = self._create_tenant(clean)
            
            # Step 2: Mudar para schema do tenant
            connection.set_tenant(tenant)
            
            # Step 3: Obter DeviceTemplate e DashboardTemplate
            device_template, dashboard_template = self._get_templates()
            
            # Step 4: Criar 7 devices
            devices = self._create_devices(device_template, clean)
            
            # Step 5: Provisionar EMQX para cada device
            mqtt_creds = self._provision_devices(devices)
            
            # Step 6: Criar DashboardConfig para cada device
            self._create_dashboards(devices, dashboard_template)
            
            # Step 7: Resumo final
            self._print_summary(tenant, devices, mqtt_creds)
            
        except Exception as e:
            raise CommandError(f"❌ Erro ao executar seed: {e}")
    
    def _create_tenant(self, clean: bool) -> Client:
        """Cria ou obtém tenant 'demo'."""
        self.stdout.write("📦 Step 1: Criando tenant 'demo'...")
        
        if clean:
            # Remover tenant existente
            Client.objects.filter(schema_name='demo').delete()
            self.stdout.write("   🗑️  Tenant 'demo' removido")
        
        tenant, created = Client.objects.get_or_create(
            schema_name='demo',
            defaults={
                'name': 'Demo Company',
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS("   ✅ Tenant criado: demo"))
        else:
            self.stdout.write("   ℹ️  Tenant já existe: demo")
        
        # Criar domínio
        domain, created = Domain.objects.get_or_create(
            domain='demo.localhost',
            defaults={'tenant': tenant, 'is_primary': True}
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS("   ✅ Domain criado: demo.localhost"))
        else:
            self.stdout.write("   ℹ️  Domain já existe: demo.localhost")
        
        self.stdout.write("")
        return tenant
    
    def _get_templates(self):
        """Obtém/cria DeviceTemplate no tenant a partir do global."""
        self.stdout.write("📦 Step 2: Buscando/criando templates JE02...")
        
        # Buscar template global do public schema
        try:
            global_template = GlobalDeviceTemplate.objects.get(
                code='inverter_je02_v1',
                version=1,
                is_global=True
            )
            self.stdout.write(self.style.SUCCESS(f"   ✅ DeviceTemplate global encontrado: {global_template.code}"))
        except GlobalDeviceTemplate.DoesNotExist:
            raise CommandError(
                "❌ DeviceTemplate global 'inverter_je02_v1' não encontrado!\n"
                "Execute as migrations primeiro:\n"
                "  docker compose exec api python manage.py migrate templates"
            )
        
        # Criar/obter template local no tenant
        device_template, created = DeviceTemplate.objects.get_or_create(
            code=global_template.code,
            version=global_template.version,
            defaults={
                'name': global_template.name,
                'description': global_template.description,
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f"   ✅ DeviceTemplate local criado: {device_template.code}"))
            
            # Copiar PointTemplates também
            from apps.templates.models import PointTemplate as GlobalPointTemplate
            from apps.devices.models import PointTemplate
            
            for gpt in global_template.point_templates.all():
                PointTemplate.objects.get_or_create(
                    device_template=device_template,
                    name=gpt.name,
                    defaults={
                        'label': gpt.name.replace('_', ' ').title(),
                        'ptype': gpt.ptype,
                        'unit': gpt.unit or '',
                        'default_limits': gpt.default_limits or {},
                    }
                )
            self.stdout.write(f"   ✅ {global_template.point_templates.count()} PointTemplates copiados")
        else:
            self.stdout.write(f"   ℹ️  DeviceTemplate local já existe: {device_template.code}")
        
        # Buscar DashboardTemplate global
        try:
            dashboard_template = GlobalDashboardTemplate.objects.get(
                device_template=global_template,
                version=1
            )
            self.stdout.write(self.style.SUCCESS("   ✅ DashboardTemplate encontrado"))
        except GlobalDashboardTemplate.DoesNotExist:
            raise CommandError(
                "❌ DashboardTemplate para 'inverter_je02_v1' não encontrado!\n"
                "Execute as migrations primeiro:\n"
                "  docker compose exec api python manage.py migrate templates"
            )
        
        self.stdout.write("")
        return device_template, dashboard_template
    
    def _create_devices(self, device_template: DeviceTemplate, clean: bool):
        """Cria 7 devices INV-01 a INV-07."""
        self.stdout.write("📦 Step 3: Criando 7 devices (INV-01 ... INV-07)...")
        
        if clean:
            Device.objects.all().delete()
            self.stdout.write("   🗑️  Devices existentes removidos")
        
        devices = []
        device_names = [f"INV-{i:02d}" for i in range(1, 8)]  # INV-01, INV-02, ..., INV-07
        
        for name in device_names:
            device, created = Device.objects.get_or_create(
                name=name,
                defaults={
                    'template': device_template,  # Agora usa o template local
                    'topic_base': f"traksense/demo/plant-01/{name.lower()}",
                }
            )
            
            # Criar Points para o device (baseado nos PointTemplates)
            if created:
                for pt in device_template.point_templates.all():
                    Point.objects.get_or_create(
                        device=device,
                        name=pt.name,
                        defaults={
                            'point_type': pt.point_type,
                            'unit': pt.unit,
                            'description': pt.description,
                        }
                    )
                
                self.stdout.write(f"   ✅ Device criado: {device.name} ({device.id})")
            else:
                self.stdout.write(f"   ℹ️  Device já existe: {device.name}")
            
            devices.append(device)
        
        self.stdout.write("")
        return devices
    
    def _provision_devices(self, devices):
        """Provisiona EMQX para cada device."""
        self.stdout.write("📦 Step 4: Provisionando EMQX (credenciais + ACL)...")
        
        mqtt_creds = []
        
        for device in devices:
            try:
                # Provisionar device no EMQX
                mqtt_info = provision_emqx_for_device(
                    device=device,
                    site_slug='plant-01',
                    password_length=20
                )
                
                # Salvar credentials_id no device
                device.credentials_id = mqtt_info['mqtt']['client_id']
                device.save(update_fields=['credentials_id'])
                
                mqtt_creds.append({
                    'device': device.name,
                    'username': mqtt_info['mqtt']['username'],
                    'password': mqtt_info['mqtt']['password'],
                    'topic_base': device.topic_base
                })
                
                self.stdout.write(f"   ✅ Provisionado: {device.name}")
                
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f"   ⚠️  Falha ao provisionar {device.name}: {e}")
                )
        
        self.stdout.write("")
        return mqtt_creds
    
    def _create_dashboards(self, devices, dashboard_template: GlobalDashboardTemplate):
        """Cria DashboardConfig para cada device."""
        self.stdout.write("📦 Step 5: Criando DashboardConfigs...")
        
        for device in devices:
            # Instanciar DashboardConfig do template
            config, created = DashboardConfig.objects.get_or_create(
                device=device,
                defaults={
                    'json': dashboard_template.json,  # Copiar JSON do template
                }
            )
            
            if created:
                self.stdout.write(f"   ✅ Dashboard criado: {device.name}")
            else:
                self.stdout.write(f"   ℹ️  Dashboard já existe: {device.name}")
        
        self.stdout.write("")
    
    def _print_summary(self, tenant: Client, devices, mqtt_creds):
        """Exibe resumo final."""
        self.stdout.write("="*70)
        self.stdout.write(self.style.SUCCESS("✅ SEED CONCLUÍDO COM SUCESSO!"))
        self.stdout.write("="*70)
        self.stdout.write("")
        
        self.stdout.write("📊 Resumo:")
        self.stdout.write(f"   Tenant:          {tenant.schema_name}")
        self.stdout.write(f"   Site:            plant-01")
        self.stdout.write(f"   Devices criados: {len(devices)}")
        self.stdout.write("")
        
        self.stdout.write("🔐 Credenciais MQTT:")
        for cred in mqtt_creds:
            self.stdout.write(f"\n   Device: {cred['device']}")
            self.stdout.write(f"   Username: {cred['username']}")
            self.stdout.write(self.style.WARNING(f"   Password: {cred['password']}"))
            self.stdout.write(f"   Topic:    {cred['topic_base']}/telem")
        
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("🚀 Próximos passos:"))
        self.stdout.write("   1. Executar simulador MQTT:")
        self.stdout.write("      python scripts/sim_je02.py --config sim_inv01.json")
        self.stdout.write("")
        self.stdout.write("   2. Verificar dados no TimescaleDB:")
        self.stdout.write("      SELECT * FROM demo.ts_measure_1m ORDER BY ts DESC LIMIT 10;")
        self.stdout.write("")
        self.stdout.write("   3. Testar API de dashboards:")
        self.stdout.write("      GET /api/dashboards/?device=<device_id>")
        self.stdout.write("")
