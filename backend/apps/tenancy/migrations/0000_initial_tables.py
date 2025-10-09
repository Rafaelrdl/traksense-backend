# Generated migration for initial tenancy tables

from django.db import migrations


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        # Criar tabelas do django-tenants manualmente
        migrations.RunSQL(
            sql="""
            CREATE TABLE IF NOT EXISTS public.tenancy_client (
                id SERIAL PRIMARY KEY,
                schema_name VARCHAR(63) NOT NULL UNIQUE,
                name VARCHAR(200) NOT NULL,
                uuid UUID NULL UNIQUE,
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                created_on TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                updated_on TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                auto_create_schema BOOLEAN NOT NULL DEFAULT TRUE,
                auto_drop_schema BOOLEAN NOT NULL DEFAULT FALSE
            );
            
            CREATE TABLE IF NOT EXISTS public.tenancy_domain (
                id SERIAL PRIMARY KEY,
                domain VARCHAR(253) NOT NULL UNIQUE,
                tenant_id INTEGER NOT NULL REFERENCES public.tenancy_client(id) ON DELETE CASCADE,
                is_primary BOOLEAN NOT NULL DEFAULT TRUE
            );
            
            CREATE INDEX IF NOT EXISTS tenancy_domain_tenant_id_idx ON public.tenancy_domain(tenant_id);
            """,
            reverse_sql="""
            DROP TABLE IF EXISTS public.tenancy_domain CASCADE;
            DROP TABLE IF EXISTS public.tenancy_client CASCADE;
            """
        ),
    ]
