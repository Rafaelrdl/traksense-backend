"""
Tenancy Admin - Interface administrativa para gestão de tenants e domínios

Este módulo registra os modelos de tenancy no Django Admin.

Admin classes:
-------------
1. ClientAdmin (TenantAdminMixin):
   - Gerencia tenants (Client model)
   - Permite criar/editar/deletar tenants
   - Exibe schema_name, is_active, created_on
   - Herda de TenantAdminMixin (validações específicas de django-tenants)

2. DomainAdmin:
   - Gerencia domínios (Domain model)
   - Associa domínios a tenants
   - Exibe domain, tenant, is_primary

Acesso:
------
URL: http://localhost:8000/admin/tenancy/

Segurança:
---------
- Apenas internal_ops deve ter acesso ao admin de tenancy
- Clientes (customer_admin) NÃO devem gerenciar tenants/domínios
- Use Django permissions ou custom permission classes

Fluxo de criação de tenant:
--------------------------
1. Admin acessa /admin/tenancy/client/add/
2. Preenche: schema_name='novo_cliente', name='Novo Cliente'
3. Salva → schema criado automaticamente (auto_create_schema=True)
4. Migrações TENANT_APPS executadas no novo schema
5. Cria domínio: /admin/tenancy/domain/add/
6. Preenche: domain='novo.traksense.local', tenant=novo_cliente, is_primary=True
7. Pronto! Tenant acessível via novo.traksense.local

Notas:
-----
- TenantAdminMixin: adiciona validações de schema_name
- auto_create_schema=True: cria schema ao salvar (útil em dev)
- Produção: usar manage.py migrate_schemas --tenant=<schema_name>

Autor: TrakSense Team
Data: 2025-10-07
"""
from django.contrib import admin
from django_tenants.admin import TenantAdminMixin
from .models import Client, Domain


@admin.register(Client)
class ClientAdmin(TenantAdminMixin, admin.ModelAdmin):
    """
    Admin para modelo Client (Tenant).
    
    Herda de TenantAdminMixin para validações específicas:
    - schema_name: apenas [a-z0-9_], começa com letra
    - schema_name: não pode ser 'public' ou schema existente
    - Criação de schema automática (se auto_create_schema=True)
    
    List display:
    - name: nome amigável do tenant
    - schema_name: identificador do schema PostgreSQL
    - is_active: flag de ativação
    - created_on: data de criação
    
    Filters:
    - is_active: filtrar tenants ativos/inativos
    - created_on: filtrar por data de criação
    
    Search:
    - name: buscar por nome amigável
    - schema_name: buscar por schema
    """
    # Colunas exibidas na lista
    list_display = ['name', 'schema_name', 'is_active', 'created_on']
    
    # Filtros laterais
    list_filter = ['is_active', 'created_on']
    
    # Busca
    search_fields = ['name', 'schema_name']
    
    # Campos readonly (schema_name não deve ser editado após criação)
    readonly_fields = ['created_on', 'updated_on']
    
    # Organização do formulário
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('name', 'schema_name', 'is_active')
        }),
        ('Auditoria', {
            'fields': ('created_on', 'updated_on'),
            'classes': ('collapse',)
        }),
    )
    
    # Ordenação padrão
    ordering = ['-created_on']
    
    # Ações customizadas
    actions = ['activate_tenants', 'deactivate_tenants']
    
    def activate_tenants(self, request, queryset):
        """Ativa tenants selecionados."""
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} tenant(s) ativado(s).")
    activate_tenants.short_description = "Ativar tenants selecionados"
    
    def deactivate_tenants(self, request, queryset):
        """Desativa tenants selecionados."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} tenant(s) desativado(s).")
    deactivate_tenants.short_description = "Desativar tenants selecionados"


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    """
    Admin para modelo Domain (mapeamento domínio → tenant).
    
    List display:
    - domain: domínio completo (ex: "climatrak.traksense.local")
    - tenant: tenant associado (Client)
    - is_primary: se é domínio primário do tenant
    
    Filters:
    - is_primary: filtrar domínios primários/secundários
    
    Search:
    - domain: buscar por domínio
    
    Notas:
    -----
    - Validar domínio manualmente (django-tenants não valida formato)
    - Apenas um domínio primário por tenant (validar em clean())
    - Em produção: configurar DNS + certificados SSL
    """
    # Colunas exibidas na lista
    list_display = ['domain', 'tenant', 'is_primary']
    
    # Filtros laterais
    list_filter = ['is_primary']
    
    # Busca
    search_fields = ['domain', 'tenant__name', 'tenant__schema_name']
    
    # Organização do formulário
    fieldsets = (
        (None, {
            'fields': ('domain', 'tenant', 'is_primary')
        }),
    )
    
    # Ordenação padrão
    ordering = ['tenant__name', '-is_primary', 'domain']
    
    # Raw ID fields (para muitos tenants)
    # raw_id_fields = ['tenant']  # Descomentar se > 100 tenants
