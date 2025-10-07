"""
Timeseries App Config - Telemetria IoT com TimescaleDB

Este módulo define a configuração do app 'timeseries' no Django.

App Purpose:
-----------
Gerencia telemetria IoT (time-series) usando TimescaleDB:
- Hypertable: public.ts_measure (tabela particionada por tempo)
- Continuous aggregates: ts_measure_1m, ts_measure_5m, ts_measure_1h
- Row Level Security (RLS): isolamento por tenant_id
- Compression: dados > 7 dias
- Retention: dados > 365 dias são deletados

Diferenças vs apps tradicionais:
-------------------------------
- SEM Django models (models.py vazio)
- Tabelas criadas via SQL migration (RunSQL)
- Queries via raw SQL (connection.cursor())
- Ingest via asyncpg (serviço separado)

Estrutura:
---------
- models.py: vazio (tabelas via SQL)
- views.py: endpoints para queries (DRF)
- dbutils.py: helpers (set_tenant_guc_for_conn, get_aggregate_view_name)
- migrations/0001_ts_schema.py: DDL completo (hypertable, RLS, aggregates)
- management/commands/seed_ts.py: popular dados de teste

Registro:
--------
Em settings.py:
- SHARED_APPS: ['timeseries', ...]  # Schema public (ts_measure)
- RLS habilitado via GUC (app.tenant_id)
- TenantGucMiddleware seta GUC em cada requisição

Autor: TrakSense Team
Data: 2025-10-07
"""
from django.apps import AppConfig


class TimeseriesConfig(AppConfig):
    """
    Configuração do app Timeseries.
    
    Configurações:
    -------------
    - default_auto_field: 'django.db.models.BigAutoField'
      → PKs automáticas usam BigAutoField (8 bytes)
      → Padrão Django 3.2+
    
    - name: 'timeseries'
      → Nome do app, deve corresponder ao diretório
      → Usado em INSTALLED_APPS e referências
    
    - verbose_name: 'Time Series (Telemetria)'
      → Nome amigável exibido no Django Admin
      → Útil para identificar app na interface
    
    Características:
    ---------------
    - SEM models Django (tabelas via SQL migration)
    - Queries via raw SQL (connection.cursor())
    - TimescaleDB features: hypertables, continuous aggregates, RLS
    - Ingest assíncrono via asyncpg (serviço separado)
    
    Hooks:
    -----
    - ready(): não implementado (sem signals customizados)
    
    TODO (opcional):
    ---------------
    - Implementar ready() para registrar checks customizados
    - Validar se TimescaleDB extension está habilitada
    - Validar se RLS está habilitado em ts_measure
    """
    # Tipo de campo padrão para chaves primárias
    # BigAutoField: 8 bytes, até 9 quintilhões
    default_auto_field = 'django.db.models.BigAutoField'
    
    # Nome do app (deve corresponder ao diretório)
    name = 'timeseries'
    
    # Nome amigável (exibido no Django Admin)
    verbose_name = 'Time Series (Telemetria)'
    
    # TODO (opcional): implementar ready() para checks
    # def ready(self):
    #     """
    #     Hook chamado quando app é carregado.
    #     
    #     Checks úteis:
    #     - Verificar se TimescaleDB extension está instalada
    #     - Verificar se RLS está habilitado em ts_measure
    #     - Verificar se continuous aggregates existem
    #     """
    #     from django.core.checks import register, Warning
    #     from timeseries.dbutils import verify_rls_enabled
    #     
    #     @register()
    #     def check_rls(app_configs, **kwargs):
    #         errors = []
    #         if not verify_rls_enabled():
    #             errors.append(Warning(
    #                 'RLS não habilitado em ts_measure',
    #                 hint='Execute migrations: python manage.py migrate',
    #                 id='timeseries.W001'
    #             ))
    #         return errors
