#!/usr/bin/env python
"""
Script para criar superuser no schema public do Django.
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

from django.contrib.auth import get_user_model
from django.db import connection

User = get_user_model()

def create_superuser():
    """Cria superuser no schema public"""
    
    # Garantir que está no schema public
    with connection.cursor() as cursor:
        cursor.execute("SET search_path TO public;")
    
    username = "admin"
    email = "admin@traksense.local"
    password = "Admin@123456"
    
    # Verificar se já existe
    if User.objects.filter(username=username).exists():
        print(f"✅ Superuser '{username}' já existe!")
        user = User.objects.get(username=username)
        print(f"   Email: {user.email}")
        print(f"   Is Staff: {user.is_staff}")
        print(f"   Is Superuser: {user.is_superuser}")
        
        # Atualizar senha se necessário
        user.set_password(password)
        user.is_staff = True
        user.is_superuser = True
        user.save()
        print(f"\n✅ Senha atualizada para: {password}")
    else:
        # Criar novo superuser
        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
            first_name="Admin",
            last_name="TrakSense"
        )
        print(f"✅ Superuser criado com sucesso!")
        print(f"   Username: {username}")
        print(f"   Email: {email}")
        print(f"   Password: {password}")
    
    print("\n" + "="*80)
    print("📝 CREDENCIAIS DO DJANGO ADMIN")
    print("="*80)
    print(f"URL: http://localhost:8000/admin/")
    print(f"Username: {username}")
    print(f"Password: {password}")
    print("="*80)

if __name__ == "__main__":
    create_superuser()
