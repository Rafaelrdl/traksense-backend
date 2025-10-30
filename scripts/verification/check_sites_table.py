"""
Script para verificar a estrutura da tabela sites em todos os schemas (tenants)
"""
import django
import os
import sys

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection
from apps.tenants.models import Tenant

def check_sites_table():
    print("\n" + "="*70)
    print("VERIFICANDO TABELA 'sites' EM TODOS OS TENANTS")
    print("="*70)
    
    # Listar todos os tenants
    tenants = Tenant.objects.all()
    print(f"\nTenants encontrados: {tenants.count()}")
    
    for tenant in tenants:
        schema = tenant.schema_name
        print(f"\n{'='*70}")
        print(f"SCHEMA: {schema} ({tenant.name})")
        print(f"{'='*70}")
        
        with connection.cursor() as cursor:
            # Definir o schema
            cursor.execute(f"SET search_path TO {schema}")
            
            # Verificar se a tabela existe
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = %s 
                    AND table_name = 'sites'
                )
            """, [schema])
            
            table_exists = cursor.fetchone()[0]
            
            if not table_exists:
                print(f"❌ Tabela 'sites' não existe no schema '{schema}'")
                continue
            
            # Buscar colunas
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'sites' 
                AND table_schema = %s
                ORDER BY ordinal_position
            """, [schema])
            
            columns = cursor.fetchall()
            
            if columns:
                print(f"\n{'Coluna':<25} {'Tipo':<20} {'NULL?':<8} {'Default':<15}")
                print("-"*70)
                for col in columns:
                    default = str(col[3])[:12] if col[3] else '-'
                    print(f"{col[0]:<25} {col[1]:<20} {col[2]:<8} {default:<15}")
                
                # Verificar se is_active existe
                has_is_active = any(col[0] == 'is_active' for col in columns)
                print("\n" + "-"*70)
                if has_is_active:
                    print("✅ Campo 'is_active' EXISTE na tabela")
                else:
                    print("❌ Campo 'is_active' NÃO EXISTE na tabela")
            else:
                print("⚠️  Nenhuma coluna encontrada")
    
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    check_sites_table()
