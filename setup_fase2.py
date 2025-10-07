"""
Script de Setup - Fase 2

Executa todos os passos necessários para configurar a Fase 2:
1. Cria migrations
2. Aplica migrations
3. Cria grupos RBAC
4. Cria seeds de templates

Uso:
    python backend/setup_fase2.py

Autor: TrakSense Team
Data: 2025-10-07
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
django.setup()

from django.core.management import call_command


def print_step(msg):
    """Print formatado para steps"""
    print(f"\n{'='*70}")
    print(f"🚀 {msg}")
    print('='*70 + '\n')


def main():
    """Executa setup completo da Fase 2"""
    
    print_step("SETUP FASE 2 - MODELOS DE DOMÍNIO")
    
    # Step 1: Makemigrations
    print_step("Step 1: Criando migrations para devices e dashboards")
    try:
        call_command('makemigrations', 'devices', interactive=False)
        call_command('makemigrations', 'dashboards', interactive=False)
        print("✅ Migrations criadas com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao criar migrations: {e}")
        return
    
    # Step 2: Migrate shared apps
    print_step("Step 2: Aplicando migrations (shared apps)")
    try:
        call_command('migrate_schemas', '--shared', interactive=False)
        print("✅ Migrations aplicadas (shared)!")
    except Exception as e:
        print(f"⚠️ Aviso: {e}")
    
    # Step 3: Migrate tenant apps
    print_step("Step 3: Aplicando migrations (tenant apps)")
    try:
        call_command('migrate_schemas', interactive=False)
        print("✅ Migrations aplicadas (todos os schemas)!")
    except Exception as e:
        print(f"⚠️ Aviso: {e}")
    
    # Step 4: Seed device templates
    print_step("Step 4: Criando templates de devices")
    try:
        call_command('seed_device_templates')
        print("✅ Device templates criados!")
    except Exception as e:
        print(f"❌ Erro ao criar device templates: {e}")
        return
    
    # Step 5: Seed dashboard templates
    print_step("Step 5: Criando templates de dashboards")
    try:
        call_command('seed_dashboard_templates')
        print("✅ Dashboard templates criados!")
    except Exception as e:
        print(f"❌ Erro ao criar dashboard templates: {e}")
        return
    
    # Summary
    print_step("✅ SETUP FASE 2 CONCLUÍDO COM SUCESSO!")
    print("""
Próximos passos:

1. Criar superusuário (se ainda não existe):
   python manage.py createsuperuser

2. Adicionar usuário ao grupo internal_ops:
   python manage.py shell
   >>> from django.contrib.auth.models import User, Group
   >>> user = User.objects.get(username='seu_usuario')
   >>> group = Group.objects.get(name='internal_ops')
   >>> user.groups.add(group)

3. Acessar Django Admin:
   python manage.py runserver
   Abrir: http://localhost:8000/admin/

4. Criar um Device e ver o provisionamento automático!

Para mais informações, consulte: backend/apps/README_FASE2.md
""")


if __name__ == '__main__':
    main()
