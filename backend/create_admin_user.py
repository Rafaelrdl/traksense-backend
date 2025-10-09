#!/usr/bin/env python
"""
Script para criar superusuário admin com grupo internal_ops
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

User = get_user_model()

# Criar ou atualizar usuário admin
user, created = User.objects.get_or_create(
    username='admin',
    defaults={
        'email': 'admin@traksense.com',
        'is_superuser': True,
        'is_staff': True,
    }
)

# Sempre atualizar a senha
user.set_password('admin')
user.is_superuser = True
user.is_staff = True
user.save()

# Adicionar ao grupo internal_ops
group, _ = Group.objects.get_or_create(name='internal_ops')
user.groups.add(group)

if created:
    print('✅ Superuser "admin" created successfully!')
else:
    print('✅ Superuser "admin" already exists and was updated!')

print(f'   Username: {user.username}')
print(f'   Email: {user.email}')
print(f'   Groups: {[g.name for g in user.groups.all()]}')
print(f'   Is superuser: {user.is_superuser}')
print(f'   Is staff: {user.is_staff}')
