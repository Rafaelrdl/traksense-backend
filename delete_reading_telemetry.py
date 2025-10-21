#!/usr/bin/env python
"""
Script para apagar todas as linhas das tabelas `reading` e `telemetry` no schema do tenant UMC.
Uso:
  python delete_reading_telemetry.py --force

Sem --force o script apenas mostra os counts atuais.
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django_tenants.utils import schema_context
from apps.tenants.models import Tenant
from django.db import connection


def get_counts(tenant_schema='umc'):
    tenant = Tenant.objects.get(schema_name=tenant_schema)
    with schema_context(tenant.schema_name):
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM reading")
            reading_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM telemetry")
            telemetry_count = cursor.fetchone()[0]
    return reading_count, telemetry_count


def delete_data(tenant_schema='umc'):
    tenant = Tenant.objects.get(schema_name=tenant_schema)
    print(f"\n🔐 Excluindo dados no schema: {tenant.schema_name} ({tenant.name})")
    with schema_context(tenant.schema_name):
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM reading")
            reading_deleted = cursor.rowcount
            cursor.execute("DELETE FROM telemetry")
            telemetry_deleted = cursor.rowcount
    return reading_deleted, telemetry_deleted


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Apaga reading e telemetry do tenant UMC')
    parser.add_argument('--force', action='store_true', help='Executa a exclusão')
    args = parser.parse_args()

    try:
        print("="*70)
        print("🧹 SCRIPT DELETAR READING E TELEMETRY - UMC")
        print("="*70)

        reading_count, telemetry_count = get_counts('umc')
        print(f"\n📊 Contagem atual:")
        print(f"   • reading: {reading_count}")
        print(f"   • telemetry: {telemetry_count}")

        if not args.force:
            print("\n💡 Execute com --force para realmente deletar os dados")
            sys.exit(0)

        # Deletar
        reading_deleted, telemetry_deleted = delete_data('umc')

        print(f"\n🗑️  Linhas deletadas:")
        print(f"   • reading: {reading_deleted}")
        print(f"   • telemetry: {telemetry_deleted}")

        # Recontar
        reading_count_after, telemetry_count_after = get_counts('umc')
        print(f"\n📊 Contagem após exclusão:")
        print(f"   • reading: {reading_count_after}")
        print(f"   • telemetry: {telemetry_count_after}")

        print("\n✅ Operação concluída")
        print("="*70)
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
