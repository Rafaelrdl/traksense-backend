"""
Verificar estrutura de tabelas no schema do tenant.
"""

CODE = """
from django.db import connection

# Verificar schema atual
with connection.cursor() as cursor:
    cursor.execute("SELECT current_schema();")
    schema = cursor.fetchone()[0]
    print(f'Schema atual: {schema}')
    
    cursor.execute(\"\"\"
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = %s 
        AND table_name IN ('reading', 'telemetry', 'alerts_rule', 'alerts_alert')
        ORDER BY table_name;
    \"\"\", [schema])
    
    tables = cursor.fetchall()
    print(f'\\nTabelas encontradas no schema {schema}:')
    if tables:
        for table in tables:
            print(f'  - {table[0]}')
            
            # Contar registros
            cursor.execute(f'SELECT COUNT(*) FROM {table[0]};')
            count = cursor.fetchone()[0]
            print(f'    Registros: {count}')
    else:
        print('  ❌ Nenhuma tabela encontrada!')
        
    # Listar todas as tabelas do schema
    print(f'\\nTodas as tabelas no schema {schema}:')
    cursor.execute(\"\"\"
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = %s 
        ORDER BY table_name
        LIMIT 20;
    \"\"\", [schema])
    
    all_tables = cursor.fetchall()
    for table in all_tables:
        print(f'  - {table[0]}')
"""

import subprocess

print('🔍 Verificando estrutura do banco de dados...\n')
result = subprocess.run(
    ['docker', 'exec', 'traksense-api', 'python', 'manage.py', 'shell', '-c', CODE],
    capture_output=True,
    text=True
)

print(result.stdout)
if result.stderr and ('ERROR' in result.stderr or 'Traceback' in result.stderr):
    print('❌ Erro:', result.stderr)
