#!/usr/bin/env python
"""Script para definir senha do superuser admin no schema público"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from django.contrib.auth import get_user_model
from django.db import connection

# Garantir que estamos no schema público
connection.set_schema_to_public()

User = get_user_model()

try:
    user = User.objects.get(username='admin')
    user.set_password('Admin@123456')
    user.save()
    print(f'✅ Senha definida com sucesso para: {user.username}')
    print(f'   Email: {user.email}')
    print(f'   Schema: {connection.schema_name}')
    print(f'   Is Staff: {user.is_staff}')
    print(f'   Is Superuser: {user.is_superuser}')
except User.DoesNotExist:
    print('❌ Usuário admin não encontrado!')
