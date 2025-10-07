"""
Tenancy App Config - Configuração do app de multi-tenancy

Este módulo define a configuração do app 'tenancy' no Django.

App Purpose:
-----------
Gerencia multi-tenancy usando django-tenants (schema-per-tenant):
- Client model (TenantMixin): representa tenants
- Domain model (DomainMixin): mapeia domínios para tenants
- Admin interface para gestão de tenants/domínios

Django App System:
-----------------
AppConfig define metadados e comportamento do app:
- name: nome do app (deve corresponder ao diretório)
- default_auto_field: tipo de campo para PKs automáticas
- ready(): hook para inicialização (signals, checks, etc.)

Registro:
--------
Registrado em settings.py:
- SHARED_APPS: ['tenancy', ...]  # Tabelas no schema 'public'
- TENANT_MODEL: 'tenancy.Client'
- TENANT_DOMAIN_MODEL: 'tenancy.Domain'

Autor: TrakSense Team
Data: 2025-10-07
"""
from django.apps import AppConfig


class TenancyConfig(AppConfig):
    """
    Configuração do app Tenancy.
    
    Configurações:
    -------------
    - default_auto_field: 'django.db.models.BigAutoField'
      → PKs automáticas usam BigAutoField (8 bytes, até 9 quintilhões)
      → Padrão Django 3.2+, recomendado para novos projetos
    
    - name: 'tenancy'
      → Nome do app, deve corresponder ao diretório
      → Usado em INSTALLED_APPS e referências (ex: 'tenancy.Client')
    
    Hooks:
    -----
    - ready(): chamado quando app é carregado
      → Útil para registrar signals, checks, etc.
      → Não implementado aqui (sem signals customizados)
    
    Uso:
    ---
    # Referência ao app
    from django.apps import apps
    tenancy_config = apps.get_app_config('tenancy')
    
    # Obter modelos do app
    Client = apps.get_model('tenancy', 'Client')
    Domain = apps.get_model('tenancy', 'Domain')
    """
    # Tipo de campo padrão para chaves primárias
    # BigAutoField: 8 bytes, até 9.223.372.036.854.775.807
    # (vs AutoField: 4 bytes, até 2.147.483.647)
    default_auto_field = 'django.db.models.BigAutoField'
    
    # Nome do app (deve corresponder ao diretório)
    name = 'tenancy'
    
    # Nome amigável (exibido no Django Admin)
    verbose_name = 'Multi-Tenancy'
    
    # TODO (opcional): implementar ready() se necessário
    # def ready(self):
    #     """
    #     Hook chamado quando app é carregado.
    #     Útil para:
    #     - Registrar signals
    #     - Registrar checks customizados
    #     - Inicializar cache/conexões
    #     """
    #     import tenancy.signals  # Registrar signals
    #     pass
