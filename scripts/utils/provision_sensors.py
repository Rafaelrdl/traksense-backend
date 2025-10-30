"""
Script de Provisionamento de Sensores em Lote

Permite provisionar múltiplos sensores e vinculá-los aos ativos através de um arquivo CSV.
Ideal para instalações em massa de novos clientes.

Uso:
    python provision_sensors.py --tenant umc --file sensores_cliente.csv

Formato do CSV:
    sensor_tag,asset_tag,metric_type,unit,mqtt_client_id
    CH-001-TEMP-SUPPLY,CH-001,temp_supply,°C,GW-CH-001
    CH-001-TEMP-RETURN,CH-001,temp_return,°C,GW-CH-001
    CH-001-POWER-KW,CH-001,power_kw,kW,GW-CH-001
    AHU-001-TEMP-SUPPLY,AHU-001,temp_supply,°C,GW-AHU-001

Campos do CSV:
    - sensor_tag: Tag única do sensor (ex: CH-001-TEMP-SUPPLY)
    - asset_tag: Tag do ativo ao qual vincular (ex: CH-001)
    - metric_type: Tipo de métrica (deve ser um dos SENSOR_TYPE_CHOICES)
    - unit: Unidade de medida (ex: °C, kW, Pa, %)
    - mqtt_client_id: ID do dispositivo MQTT (opcional, será gerado se vazio)
"""

import csv
import sys
import os
import argparse
from datetime import datetime

# Setup Django
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.db import connection
from apps.tenants.models import Tenant
from apps.assets.models import Asset, Device, Sensor


class SensorProvisioner:
    """Classe para provisionar sensores em lote"""
    
    def __init__(self, tenant_slug):
        """
        Inicializa o provisionador para um tenant específico.
        
        Args:
            tenant_slug (str): Slug do tenant (ex: "umc")
        """
        try:
            connection.set_schema_to_public()
            self.tenant = Tenant.objects.get(slug=tenant_slug)
            connection.set_tenant(self.tenant)
            print(f"✅ Conectado ao tenant: {self.tenant.name}")
        except Tenant.DoesNotExist:
            print(f"❌ Tenant '{tenant_slug}' não encontrado")
            sys.exit(1)
    
    def validate_metric_type(self, metric_type):
        """
        Valida se o metric_type é válido.
        
        Args:
            metric_type (str): Tipo de métrica a validar
        
        Returns:
            bool: True se válido, False caso contrário
        """
        valid_types = [choice[0] for choice in Sensor.SENSOR_TYPE_CHOICES]
        return metric_type in valid_types
    
    def provision_from_csv(self, csv_file_path, dry_run=False):
        """
        Provisiona sensores a partir de um arquivo CSV.
        
        Args:
            csv_file_path (str): Caminho do arquivo CSV
            dry_run (bool): Se True, apenas simula sem criar nada
        
        Returns:
            dict: Estatísticas do provisionamento
        """
        stats = {
            'total_rows': 0,
            'sensors_created': 0,
            'sensors_updated': 0,
            'devices_created': 0,
            'errors': []
        }
        
        print(f"\n{'='*60}")
        print(f"🚀 Iniciando provisionamento de sensores")
        print(f"Tenant: {self.tenant.name}")
        print(f"Arquivo: {csv_file_path}")
        print(f"Modo: {'DRY RUN (simulação)' if dry_run else 'PRODUÇÃO'}")
        print(f"{'='*60}\n")
        
        try:
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                # Valida headers
                required_fields = ['sensor_tag', 'asset_tag', 'metric_type', 'unit']
                if not all(field in reader.fieldnames for field in required_fields):
                    print(f"❌ CSV deve ter os campos: {', '.join(required_fields)}")
                    print(f"   Campos encontrados: {', '.join(reader.fieldnames)}")
                    return stats
                
                for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is 1)
                    stats['total_rows'] += 1
                    
                    sensor_tag = row['sensor_tag'].strip()
                    asset_tag = row['asset_tag'].strip()
                    metric_type = row['metric_type'].strip()
                    unit = row['unit'].strip()
                    mqtt_client_id = row.get('mqtt_client_id', '').strip() or f'GW-{asset_tag}'
                    
                    # Valida campos obrigatórios
                    if not all([sensor_tag, asset_tag, metric_type, unit]):
                        error = f"Linha {row_num}: Campos obrigatórios vazios"
                        print(f"⚠️  {error}")
                        stats['errors'].append(error)
                        continue
                    
                    # Valida metric_type
                    if not self.validate_metric_type(metric_type):
                        error = f"Linha {row_num}: metric_type '{metric_type}' inválido"
                        print(f"⚠️  {error}")
                        stats['errors'].append(error)
                        continue
                    
                    try:
                        # Busca o ativo
                        try:
                            asset = Asset.objects.get(tag=asset_tag, is_active=True)
                        except Asset.DoesNotExist:
                            error = f"Linha {row_num}: Asset '{asset_tag}' não encontrado"
                            print(f"❌ {error}")
                            stats['errors'].append(error)
                            continue
                        
                        if not dry_run:
                            # Busca ou cria o Device
                            device, device_created = Device.objects.get_or_create(
                                mqtt_client_id=mqtt_client_id,
                                defaults={
                                    'asset': asset,
                                    'name': f'Gateway {asset_tag}',
                                    'serial_number': f'SN-{mqtt_client_id}',
                                    'device_type': 'GATEWAY',
                                    'status': 'OFFLINE'
                                }
                            )
                            
                            if device_created:
                                stats['devices_created'] += 1
                                print(f"   ✨ Device criado: {device.mqtt_client_id}")
                            
                            # Cria ou atualiza o Sensor
                            sensor, sensor_created = Sensor.objects.update_or_create(
                                tag=sensor_tag,
                                defaults={
                                    'device': device,
                                    'metric_type': metric_type,
                                    'unit': unit,
                                    'is_active': True
                                }
                            )
                            
                            if sensor_created:
                                stats['sensors_created'] += 1
                                print(f"✅ Sensor criado: {sensor_tag} → {asset_tag} ({metric_type})")
                            else:
                                stats['sensors_updated'] += 1
                                print(f"🔄 Sensor atualizado: {sensor_tag} → {asset_tag} ({metric_type})")
                        else:
                            print(f"[DRY RUN] Criaria sensor: {sensor_tag} → {asset_tag} ({metric_type})")
                            stats['sensors_created'] += 1
                    
                    except Exception as e:
                        error = f"Linha {row_num}: Erro ao processar '{sensor_tag}': {e}"
                        print(f"❌ {error}")
                        stats['errors'].append(error)
        
        except FileNotFoundError:
            print(f"❌ Arquivo não encontrado: {csv_file_path}")
            return stats
        except Exception as e:
            print(f"❌ Erro ao ler CSV: {e}")
            return stats
        
        # Exibe resumo
        print(f"\n{'='*60}")
        print(f"📊 RESUMO DO PROVISIONAMENTO")
        print(f"{'='*60}")
        print(f"Total de linhas processadas: {stats['total_rows']}")
        print(f"Sensores criados: {stats['sensors_created']}")
        print(f"Sensores atualizados: {stats['sensors_updated']}")
        print(f"Devices criados: {stats['devices_created']}")
        print(f"Erros: {len(stats['errors'])}")
        
        if stats['errors']:
            print(f"\n⚠️  ERROS ENCONTRADOS:")
            for error in stats['errors']:
                print(f"   - {error}")
        
        print(f"{'='*60}\n")
        
        return stats


def main():
    """Função principal do script"""
    parser = argparse.ArgumentParser(
        description='Provisiona sensores em lote a partir de arquivo CSV',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplo de uso:
    python provision_sensors.py --tenant umc --file sensores.csv
    python provision_sensors.py --tenant umc --file sensores.csv --dry-run

Formato do CSV:
    sensor_tag,asset_tag,metric_type,unit,mqtt_client_id
    CH-001-TEMP-SUPPLY,CH-001,temp_supply,°C,GW-CH-001
    CH-001-TEMP-RETURN,CH-001,temp_return,°C,GW-CH-001
        """
    )
    
    parser.add_argument(
        '--tenant',
        required=True,
        help='Slug do tenant (ex: umc)'
    )
    
    parser.add_argument(
        '--file',
        required=True,
        help='Caminho do arquivo CSV com os sensores'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simula o provisionamento sem criar nada no banco'
    )
    
    args = parser.parse_args()
    
    # Executa o provisionamento
    provisioner = SensorProvisioner(args.tenant)
    stats = provisioner.provision_from_csv(args.file, dry_run=args.dry_run)
    
    # Exit code baseado em erros
    if stats['errors']:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
