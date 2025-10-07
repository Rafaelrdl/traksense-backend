#!/usr/bin/env python
"""
manage.py - Entry Point de Comandos Django - TrakSense Backend

Este é o ponto de entrada principal para todos os comandos administrativos
do Django na plataforma TrakSense.

Responsabilidades:
-----------------
- Configurar o módulo de settings (DJANGO_SETTINGS_MODULE)
- Carregar comandos do Django e apps personalizados
- Executar migrations, runserver, shell, testes, etc.

Comandos Mais Usados:
--------------------
Desenvolvimento:
  python manage.py runserver              # Inicia servidor dev (porta 8000)
  python manage.py shell                  # Shell Python com Django carregado
  python manage.py dbshell                # Shell PostgreSQL direto

Migrações (django-tenants):
  python manage.py migrate_schemas        # Migra todos os schemas (shared + tenants)
  python manage.py migrate_schemas --shared   # Apenas schema public
  python manage.py migrate_schemas --tenant   # Apenas schemas de tenants
  python manage.py migrate                # Django padrão (não usar com tenants!)

Admin e Usuários:
  python manage.py createsuperuser        # Criar admin
  python manage.py changepassword user    # Mudar senha

Seeds e Testes:
  python manage.py seed_ts                # Popular telemetria (comando custom)
  python manage.py test                   # Rodar testes Django
  pytest                                  # Rodar testes pytest (recomendado)

Timescale e Dados:
  python manage.py shell                  # Para queries manuais
  >>> from django.db import connection
  >>> cursor = connection.cursor()
  >>> cursor.execute("SELECT count(*) FROM public.ts_measure")

Produção:
  python manage.py collectstatic --noinput  # Coleta arquivos estáticos
  python manage.py check --deploy           # Valida configurações de produção

Docker:
  docker compose exec api python manage.py <comando>

Estrutura do Projeto:
--------------------
backend/
  ├── manage.py          ← Este arquivo (entry point)
  ├── core/              ← Configurações principais (settings, urls)
  ├── apps/              ← Apps Django (tenancy, timeseries, etc.)
  └── tests/             ← Testes pytest

Variáveis de Ambiente:
---------------------
- DJANGO_SETTINGS_MODULE: Módulo de settings (padrão: core.settings)
- Outras variáveis: ver infra/.env.api

Autor: TrakSense Team
Data: 2025-10-07
"""

import os
import sys


def main():
    """
    Executa tarefas administrativas do Django.
    
    Fluxo:
    1. Define DJANGO_SETTINGS_MODULE (padrão: core.settings)
    2. Importa execute_from_command_line do Django
    3. Passa argumentos da linha de comando (sys.argv)
    4. Django processa o comando e executa a ação correspondente
    
    Tratamento de Erros:
    - ImportError: Django não instalado ou ambiente virtual não ativado
    - Outros erros: Django exibe mensagem de erro apropriada
    
    Raises:
        ImportError: Se Django não estiver instalado ou acessível
    """
    # Define o módulo de settings padrão
    # Pode ser sobrescrito via variável de ambiente DJANGO_SETTINGS_MODULE
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    
    try:
        # Importa a função principal de execução de comandos do Django
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        # Django não encontrado: provavelmente não instalado ou venv não ativado
        raise ImportError(
            "Não foi possível importar Django. Você tem certeza de que está "
            "instalado e disponível na variável de ambiente PYTHONPATH? "
            "Você esqueceu de ativar um ambiente virtual?"
        ) from exc
    
    # Executa o comando Django passado via linha de comando
    # sys.argv[0]: nome do script (manage.py)
    # sys.argv[1]: comando (runserver, migrate, etc.)
    # sys.argv[2:]: argumentos do comando
    execute_from_command_line(sys.argv)


# ============================================================================
# PONTO DE ENTRADA
# ============================================================================
if __name__ == '__main__':
    # Executa main() apenas se o script for chamado diretamente
    # (não se for importado como módulo)
    main()
