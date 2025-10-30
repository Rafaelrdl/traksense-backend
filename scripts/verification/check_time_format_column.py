"""
Script para verificar se a coluna time_format existe no schema umc
"""
from django.db import connection

# Define o schema para umc
connection.set_schema('umc')

cursor = connection.cursor()
cursor.execute("""
    SELECT column_name, data_type, column_default 
    FROM information_schema.columns 
    WHERE table_schema = 'umc' 
    AND table_name = 'accounts_user'
    ORDER BY ordinal_position
""")

columns = cursor.fetchall()

print("\n" + "="*80)
print("COLUNAS DA TABELA accounts_user (schema: umc)")
print("="*80)

# Encontrar colunas relacionadas
relevant_cols = []
for col in columns:
    col_name = col[0]
    if any(keyword in col_name.lower() for keyword in ['time', 'language', 'timezone']):
        relevant_cols.append(col)
        print(f"\n✅ {col_name}")
        print(f"   Tipo: {col[1]}")
        print(f"   Default: {col[2]}")

if not relevant_cols:
    print("\n❌ NENHUMA COLUNA ENCONTRADA!")
    print("\nTodas as colunas disponíveis:")
    for col in columns:
        print(f"  - {col[0]} ({col[1]})")

print("\n" + "="*80)
