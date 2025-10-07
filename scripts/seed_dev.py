"""
Script de seed para ambiente de desenvolvimento.

Este script popula o banco de dados com dados de teste para facilitar
o desenvolvimento e testes manuais da aplicação TrakSense.

IMPORTANTE: Este script deve ser executado APENAS em ambiente de desenvolvimento.
           Nunca execute em produção!

Funcionalidades:
- Cria tenants de exemplo (empresas/clientes)
- Cria domínios para roteamento multi-tenant
- Cria sites (localizações físicas)
- Cria devices (equipamentos IoT) com templates
- Cria points (pontos de medição/sensores)
- Popula dados históricos de telemetria para testes

Uso:
    python scripts/seed_dev.py
    
    Ou via Docker:
    docker compose -f infra/docker-compose.yml exec api python scripts/seed_dev.py

Autor: TrakSense Team
Data: 2025-10-07
"""

import os
import sys
import django
from pathlib import Path

# ============================================================================
# CONFIGURAÇÃO DO AMBIENTE DJANGO
# ============================================================================
# Adiciona o diretório backend ao path para permitir imports dos apps Django
backend_path = Path(__file__).resolve().parent.parent / 'backend'
sys.path.insert(0, str(backend_path))

# Configura as settings do Django antes de importar models
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

# ============================================================================
# IMPORTS APÓS CONFIGURAÇÃO DO DJANGO
# ============================================================================
# IMPORTANTE: Todos os imports de models Django devem vir DEPOIS do django.setup()
from django.db import connection, transaction
from tenancy.models import Client, Domain
import uuid
from datetime import datetime, timedelta
import random


# ============================================================================
# CONSTANTES E CONFIGURAÇÕES
# ============================================================================

# Configurações de seed - ajuste conforme necessário
SEED_CONFIG = {
    'tenants': [
        {
            'schema_name': 'alpha_corp',
            'name': 'Alpha Corporation',
            'domain': 'alpha.traksense.local',
            'sites': 2,  # Número de sites por tenant
            'devices_per_site': 3,  # Número de devices por site
        },
        {
            'schema_name': 'beta_industries',
            'name': 'Beta Industries',
            'domain': 'beta.traksense.local',
            'sites': 1,
            'devices_per_site': 2,
        },
    ],
    'telemetry': {
        'days_history': 7,  # Dias de histórico para gerar
        'samples_per_hour': 12,  # Amostras por hora (1 a cada 5 minutos)
    }
}


# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def print_header(message):
    """
    Imprime um cabeçalho formatado para melhor visualização no console.
    
    Args:
        message (str): Mensagem a ser exibida no cabeçalho
    """
    separator = "=" * 80
    print(f"\n{separator}")
    print(f"  {message}")
    print(f"{separator}\n")


def print_step(step_number, total_steps, message):
    """
    Imprime o progresso de um passo da execução.
    
    Args:
        step_number (int): Número do passo atual
        total_steps (int): Total de passos
        message (str): Descrição do passo
    """
    print(f"[{step_number}/{total_steps}] {message}")


def print_success(message):
    """Imprime mensagem de sucesso."""
    print(f"  ✓ {message}")


def print_warning(message):
    """Imprime mensagem de aviso."""
    print(f"  ⚠ {message}")


def print_error(message):
    """Imprime mensagem de erro."""
    print(f"  ✗ {message}")


# ============================================================================
# FUNÇÕES DE SEED
# ============================================================================

def clear_existing_data():
    """
    Remove todos os dados de teste existentes.
    
    ATENÇÃO: Esta função trunca tabelas. Use apenas em desenvolvimento!
    
    Estratégia:
    1. Trunca tabela de telemetria (public.ts_measure)
    2. Remove domains e tenants (cascade remove os schemas)
    """
    print_step(1, 5, "Limpando dados existentes...")
    
    try:
        with connection.cursor() as cursor:
            # Trunca telemetria (hypertable)
            cursor.execute("TRUNCATE TABLE public.ts_measure CASCADE")
            print_success("Telemetria limpa")
        
        # Remove domains (cascade remove tenants)
        domain_count = Domain.objects.all().count()
        Domain.objects.all().delete()
        print_success(f"{domain_count} domínios removidos")
        
        # Remove tenants (e seus schemas)
        tenant_count = Client.objects.all().count()
        Client.objects.all().delete()
        print_success(f"{tenant_count} tenants removidos (schemas serão dropados automaticamente)")
        
    except Exception as e:
        print_error(f"Erro ao limpar dados: {e}")
        raise


def create_tenants():
    """
    Cria tenants (clientes/empresas) e seus domínios.
    
    Multi-tenancy (django-tenants):
    - Cada tenant recebe um schema PostgreSQL isolado
    - Domínio é usado para roteamento de requisições HTTP
    - O schema 'public' contém dados compartilhados e telemetria
    
    Returns:
        list: Lista de objetos Client criados
    """
    print_step(2, 5, "Criando tenants e domínios...")
    
    tenants = []
    
    for tenant_config in SEED_CONFIG['tenants']:
        # Verifica se tenant já existe
        if Client.objects.filter(schema_name=tenant_config['schema_name']).exists():
            print_warning(f"Tenant '{tenant_config['name']}' já existe, pulando...")
            tenant = Client.objects.get(schema_name=tenant_config['schema_name'])
            tenants.append(tenant)
            continue
        
        # Cria o tenant (schema é criado automaticamente)
        tenant = Client.objects.create(
            schema_name=tenant_config['schema_name'],
            name=tenant_config['name'],
            # auto_create_schema=True é padrão no model
        )
        print_success(f"Tenant '{tenant.name}' criado (schema: {tenant.schema_name})")
        
        # Cria o domínio para roteamento
        domain = Domain.objects.create(
            domain=tenant_config['domain'],
            tenant=tenant,
            is_primary=True  # Domínio principal do tenant
        )
        print_success(f"Domínio '{domain.domain}' associado")
        
        tenants.append(tenant)
    
    return tenants


def create_sites_devices_points(tenants):
    """
    Cria sites, devices e points para cada tenant.
    
    Hierarquia (a ser implementada na Fase 2):
    Tenant (empresa)
      └─> Site (localização física, ex: "Fábrica SP")
            └─> Device (equipamento IoT, ex: "Inversor Solar 01")
                  └─> Point (sensor/medição, ex: "Temperatura água")
    
    NOTA: Como os models de Site/Device/Point ainda não foram implementados,
          esta função serve como placeholder e pode ser expandida na Fase 2.
    
    Args:
        tenants (list): Lista de tenants criados
        
    Returns:
        dict: Dicionário com estrutura {tenant_id: [device_ids]}
    """
    print_step(3, 5, "Criando sites, devices e points...")
    
    # Placeholder: retorna estrutura vazia
    # TODO: Implementar quando models Device/Point estiverem prontos
    
    print_warning("Sites/Devices/Points serão implementados na Fase 2")
    print_warning("Por enquanto, apenas tenants foram criados")
    
    # Retorna estrutura vazia por enquanto
    tenant_devices = {}
    for tenant in tenants:
        tenant_devices[str(tenant.pk)] = []
    
    return tenant_devices


def populate_telemetry(tenant_devices):
    """
    Popula dados históricos de telemetria para testes.
    
    Estratégia:
    1. Gera dados sintéticos para os últimos N dias
    2. Insere em lotes (batch insert) para performance
    3. Configura GUC (app.tenant_id) para RLS funcionar
    4. Simula padrões realistas de dados de sensores
    
    Dados gerados:
    - Temperatura: 15°C a 30°C com variação gaussiana
    - Status: ON/OFF com transições realistas
    - Timestamp: distribuído uniformemente no período
    
    Args:
        tenant_devices (dict): Dicionário {tenant_id: [device_ids]}
    """
    print_step(4, 5, "Populando telemetria histórica...")
    
    if not tenant_devices or all(len(devices) == 0 for devices in tenant_devices.values()):
        print_warning("Nenhum device criado, pulando telemetria")
        print_warning("Execute novamente após implementar Device/Point models")
        return
    
    # Configurações de geração
    days = SEED_CONFIG['telemetry']['days_history']
    samples_per_hour = SEED_CONFIG['telemetry']['samples_per_hour']
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=days)
    
    total_samples = 0
    
    # Itera por tenant
    for tenant_id, device_ids in tenant_devices.items():
        if not device_ids:
            continue
        
        # Configura GUC para RLS permitir inserção
        with connection.cursor() as cursor:
            cursor.execute("SET LOCAL app.tenant_id = %s", [tenant_id])
        
        batch = []
        
        # Itera por device
        for device_id in device_ids:
            # Gera point_id fictício (substituir por point real na Fase 2)
            point_id = uuid.uuid4()
            
            # Gera amostras distribuídas no tempo
            current_time = start_time
            time_delta = timedelta(hours=1) / samples_per_hour
            
            while current_time <= end_time:
                # Simula temperatura com variação gaussiana
                temperature = random.gauss(22.5, 3.0)  # média 22.5°C, desvio 3°C
                temperature = max(15.0, min(30.0, temperature))  # limita entre 15-30
                
                # Adiciona ao batch
                batch.append((
                    tenant_id,
                    device_id,
                    point_id,
                    current_time,
                    temperature,
                    None,  # v_bool
                    None,  # v_text
                    '°C',  # unit
                    0,     # qual (0 = boa qualidade)
                    None   # meta
                ))
                
                current_time += time_delta
                
                # Insere batch quando atingir tamanho adequado (10k)
                if len(batch) >= 10000:
                    with connection.cursor() as cursor:
                        cursor.executemany("""
                            INSERT INTO public.ts_measure 
                            (tenant_id, device_id, point_id, ts, v_num, v_bool, v_text, unit, qual, meta)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, batch)
                    total_samples += len(batch)
                    batch = []
        
        # Insere batch restante
        if batch:
            with connection.cursor() as cursor:
                cursor.executemany("""
                    INSERT INTO public.ts_measure 
                    (tenant_id, device_id, point_id, ts, v_num, v_bool, v_text, unit, qual, meta)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, batch)
            total_samples += len(batch)
    
    print_success(f"{total_samples:,} amostras de telemetria inseridas")


def run_migrations():
    """
    Executa migrações do django-tenants.
    
    Processo:
    1. migrate_schemas --shared: cria tabelas no schema public
    2. migrate_schemas --tenant: cria tabelas em cada schema de tenant
    
    NOTA: Esta função executa comandos via Django management commands
          programaticamente.
    """
    print_step(5, 5, "Executando migrações dos schemas...")
    
    try:
        from django.core.management import call_command
        
        # Migra schema public (shared)
        print("  Migrando schema public (shared)...")
        call_command('migrate_schemas', '--shared', verbosity=0)
        print_success("Schema public migrado")
        
        # Migra schemas de tenants
        print("  Migrando schemas de tenants...")
        call_command('migrate_schemas', '--tenant', verbosity=0)
        print_success("Schemas de tenants migrados")
        
    except Exception as e:
        print_error(f"Erro ao executar migrações: {e}")
        raise


# ============================================================================
# FUNÇÃO PRINCIPAL
# ============================================================================

def main():
    """
    Função principal que orquestra o processo de seed.
    
    Fluxo:
    1. Limpa dados existentes (desenvolvimento)
    2. Cria tenants e domínios
    3. Cria sites, devices e points (Fase 2)
    4. Popula telemetria histórica
    5. Executa migrações dos schemas
    
    Em caso de erro, faz rollback automático (transação).
    """
    print_header("SEED DE DESENVOLVIMENTO - TrakSense Backend")
    
    print("⚠️  ATENÇÃO: Este script deve ser usado APENAS em desenvolvimento!")
    print("⚠️  Todos os dados existentes serão removidos.\n")
    
    try:
        # Usa transação para garantir atomicidade
        with transaction.atomic():
            # 1. Limpa dados existentes
            clear_existing_data()
            
            # 2. Cria tenants
            tenants = create_tenants()
            
            # 3. Executa migrações dos schemas
            run_migrations()
            
            # 4. Cria sites/devices/points (Fase 2)
            tenant_devices = create_sites_devices_points(tenants)
            
            # 5. Popula telemetria
            populate_telemetry(tenant_devices)
        
        # Sucesso!
        print_header("✓ SEED CONCLUÍDO COM SUCESSO!")
        print("\nPróximos passos:")
        print("  1. Execute os testes: pytest backend/tests/")
        print("  2. Acesse a API: http://localhost:8000/api/")
        print("  3. Consulte telemetria: /api/timeseries/data/points")
        print("\nTenants criados:")
        for tenant_config in SEED_CONFIG['tenants']:
            print(f"  • {tenant_config['name']}: http://{tenant_config['domain']}:8000/")
        
    except Exception as e:
        print_header("✗ ERRO NO SEED")
        print_error(f"Erro: {e}")
        print("\nTransação revertida. Nenhum dado foi persistido.")
        sys.exit(1)


# ============================================================================
# PONTO DE ENTRADA
# ============================================================================

if __name__ == '__main__':
    main()
