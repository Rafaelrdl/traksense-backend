"""
Tenancy Models - Multi-tenancy usando django-tenants (schema-per-tenant)

Este módulo define os modelos para multi-tenancy da plataforma TrakSense.

Arquitetura:
-----------
Schema-per-tenant (django-tenants):
- Cada tenant tem seu próprio schema PostgreSQL
- Metadados (Device, Site, Rules, Dashboards) → schemas de tenants
- Telemetria (time-series) → public.ts_measure (isolada por RLS)

Modelos:
-------
1. Client (TenantMixin):
   - Representa um tenant/cliente (ex: "Climatrak HQ", "Cliente ABC")
   - Cada Client possui um schema_name único (ex: "climatrak_hq")
   - Herda de TenantMixin (django-tenants)

2. Domain (DomainMixin):
   - Mapeia domínios para tenants (tenant routing)
   - Ex: "climatrak.traksense.local" → schema "climatrak_hq"
   - Suporta múltiplos domínios por tenant (is_primary flag)

Fluxo de requisição:
-------------------
1. Requisição chega (ex: climatrak.traksense.local/api/data)
2. TenantMainMiddleware:
   - Extrai domínio do request
   - Busca Domain.objects.get(domain='climatrak.traksense.local')
   - Obtém tenant (Client) associado
   - Seta connection.tenant = client
   - Executa SET search_path TO climatrak_hq, public
3. TenantGucMiddleware:
   - Executa SET LOCAL app.tenant_id = '<client.pk>'
   - Habilita RLS para telemetria
4. View executa queries:
   - Metadados: vêm do schema do tenant
   - Telemetria: vem de public.ts_measure (filtrada por RLS)

Exemplo:
-------
# Criar tenant + domínio
client = Client.objects.create(
    schema_name='climatrak_hq',
    name='Climatrak HQ'
)
Domain.objects.create(
    domain='climatrak.traksense.local',
    tenant=client,
    is_primary=True
)

# Schema criado automaticamente (auto_create_schema=True)
# Migrações TENANT_APPS executadas no schema

Notas:
-----
- schema_name: apenas [a-z0-9_], começa com letra
- domain: deve ser único (constraint)
- is_primary: apenas um domínio primário por tenant
- auto_create_schema: True em dev, False em prod (criar via migrate_schemas)

Autor: TrakSense Team
Data: 2025-10-07
"""
from django.db import models
from django_tenants.models import TenantMixin, DomainMixin


class Client(TenantMixin):
    """
    Tenant (Cliente) - Representa um tenant da plataforma.
    
    Cada Client tem:
    - schema_name: identificador do schema PostgreSQL (herdado de TenantMixin)
    - name: nome amigável do tenant
    - Schema dedicado: contém metadados (Device, Site, Rules, etc.)
    - Acesso isolado: RLS garante isolamento de telemetria
    
    Campos herdados de TenantMixin:
    -------------------------------
    - schema_name (CharField): nome do schema PostgreSQL
    - auto_create_schema (bool): se True, cria schema automaticamente
    - auto_drop_schema (bool): se True, deleta schema ao deletar tenant
    
    Campos customizados:
    -------------------
    - name: nome amigável (ex: "Climatrak HQ", "Cliente ABC")
    - is_active: flag para desativar tenant sem deletar
    - created_on: timestamp de criação
    - updated_on: timestamp de última atualização
    
    Uso:
    ---
    # Criar tenant
    tenant = Client.objects.create(
        schema_name='climatrak_hq',
        name='Climatrak HQ'
    )
    # Schema criado automaticamente se auto_create_schema=True
    
    # Acessar tenant em runtime
    from django.db import connection
    tenant = connection.tenant  # setado por TenantMainMiddleware
    """
    # Nome amigável do tenant
    name = models.CharField(
        max_length=200,
        help_text="Nome amigável do tenant/cliente (ex: 'Climatrak HQ')"
    )
    
    # Criar schema automaticamente ao salvar
    # True: conveniente em dev (cria schema + roda migrações)
    # False: recomendado em prod (usar manage.py migrate_schemas)
    auto_create_schema = True
    
    # Metadados de auditoria
    created_on = models.DateTimeField(
        auto_now_add=True,
        help_text="Data/hora de criação do tenant"
    )
    updated_on = models.DateTimeField(
        auto_now=True,
        help_text="Data/hora de última atualização"
    )
    
    # Flag para desativar tenant sem deletar
    is_active = models.BooleanField(
        default=True,
        help_text="Se False, tenant não pode acessar a plataforma"
    )
    
    class Meta:
        verbose_name = "Tenant"
        verbose_name_plural = "Tenants"
        ordering = ['name']
        # Adicionar índice em is_active para queries de listagem
        indexes = [
            models.Index(fields=['is_active', 'created_on']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.schema_name})"


class Domain(DomainMixin):
    """
    Domain - Mapeia domínios para tenants (tenant routing).
    
    django-tenants usa domínio do request para identificar o tenant:
    1. Extrai request.get_host() (ex: "climatrak.traksense.local")
    2. Busca Domain.objects.get(domain='climatrak.traksense.local')
    3. Obtém tenant associado (Domain.tenant)
    4. Seta connection.tenant e search_path
    
    Campos herdados de DomainMixin:
    -------------------------------
    - domain (CharField): domínio completo (ex: "climatrak.traksense.local")
    - tenant (ForeignKey): tenant associado (Client)
    - is_primary (BooleanField): se True, domínio primário do tenant
    
    Uso:
    ---
    # Criar domínio primário
    Domain.objects.create(
        domain='climatrak.traksense.local',
        tenant=tenant,
        is_primary=True
    )
    
    # Criar domínio adicional (alias)
    Domain.objects.create(
        domain='climatrak.traksense.com',
        tenant=tenant,
        is_primary=False
    )
    
    Notas:
    -----
    - domain: deve ser único (constraint de DB)
    - is_primary: apenas um domínio primário por tenant
    - Suporte a wildcards: "*.traksense.local" (config em TENANT_MODEL)
    - Porta é ignorada: "localhost:8000" → "localhost"
    
    TODO (Produção):
    ---------------
    - Configurar DNS: CNAME para cada tenant
    - Certificados SSL: wildcard ou por domínio
    - Validação: rejeitar domínios inválidos (sem TLD, etc.)
    """
    # Todos os campos são herdados de DomainMixin
    # Não adicionar campos aqui (django-tenants espera modelo simples)
    
    class Meta:
        # Sobrescrever meta se necessário
        verbose_name = "Domínio"
        verbose_name_plural = "Domínios"
    
    def __str__(self):
        primary = " (primário)" if self.is_primary else ""
        return f"{self.domain} → {self.tenant.name}{primary}"
