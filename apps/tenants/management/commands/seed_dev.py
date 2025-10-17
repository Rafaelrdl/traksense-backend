"""
Management command to seed development data.

This command creates:
1. The "Uberlandia Medical Center" tenant with schema
2. Domain mapping to umc.localhost
3. An owner user (owner@umc.localhost)
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import connection

from apps.tenants.models import Domain, Tenant

User = get_user_model()


class Command(BaseCommand):
    """Seed development tenant and owner user."""
    
    help = 'Creates development tenant (Uberlandia Medical Center) and owner user'
    
    def handle(self, *args, **options):
        """Execute the seed command."""
        
        self.stdout.write(self.style.MIGRATE_HEADING('\n=== Seeding Development Data ===\n'))
        
        # 1. Ensure we're in the public schema
        connection.set_schema_to_public()
        
        # 2. Create or get the tenant
        tenant_name = "Uberlandia Medical Center"
        tenant_slug = "uberlandia-medical-center"
        schema_name = "uberlandia_medical_center"
        
        tenant, created = Tenant.objects.get_or_create(
            slug=tenant_slug,
            defaults={
                'name': tenant_name,
                'schema_name': schema_name,
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Created tenant: {tenant_name}'))
            self.stdout.write(f'  Schema: {tenant.schema_name}')
        else:
            self.stdout.write(self.style.WARNING(f'⚠ Tenant already exists: {tenant_name}'))
        
        # 3. Create or get the domain
        domain_host = "umc.localhost"
        
        domain, created = Domain.objects.get_or_create(
            domain=domain_host,
            defaults={
                'tenant': tenant,
                'is_primary': True,
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Created domain: {domain_host}'))
        else:
            self.stdout.write(self.style.WARNING(f'⚠ Domain already exists: {domain_host}'))
        
        # 4. Switch to the tenant schema to create the user
        connection.set_tenant(tenant)
        
        # 5. Create or get the owner user
        owner_email = "owner@umc.localhost"
        owner_username = "owner"
        owner_password = "Dev@123456"
        
        user, created = User.objects.get_or_create(
            username=owner_username,
            defaults={
                'email': owner_email,
                'first_name': 'Owner',
                'last_name': 'User',
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
            }
        )
        
        if created:
            user.set_password(owner_password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f'✓ Created owner user: {owner_email}'))
            self.stdout.write(f'  Username: {owner_username}')
            self.stdout.write(f'  Password: {owner_password}')
        else:
            self.stdout.write(self.style.WARNING(f'⚠ Owner user already exists: {owner_email}'))
        
        # 6. Summary
        self.stdout.write(self.style.MIGRATE_HEADING('\n=== Seed Complete ===\n'))
        self.stdout.write(self.style.SUCCESS('Development environment ready!'))
        self.stdout.write('\nAccess information:')
        self.stdout.write(f'  URL: http://{domain_host}')
        self.stdout.write(f'  Email: {owner_email}')
        self.stdout.write(f'  Password: {owner_password}')
        self.stdout.write('')
        
        # Switch back to public schema
        connection.set_schema_to_public()
