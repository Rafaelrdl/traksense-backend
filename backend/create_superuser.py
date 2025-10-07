"""
Script para criar superusuário e adicionar ao grupo internal_ops
"""
from django.contrib.auth.models import User, Group

# Criar superusuário
username = 'admin'
email = 'admin@traksense.local'
password = 'admin123'

user, created = User.objects.get_or_create(
    username=username,
    defaults={
        'email': email,
        'is_staff': True,
        'is_superuser': True
    }
)

if created:
    user.set_password(password)
    user.save()
    print(f"✅ Superusuário '{username}' criado")
    print(f"   Email: {email}")
    print(f"   Senha: {password}")
else:
    print(f"ℹ️  Superusuário '{username}' já existe")

# Adicionar ao grupo internal_ops
try:
    group = Group.objects.get(name='internal_ops')
    user.groups.add(group)
    print(f"✅ Usuário '{username}' adicionado ao grupo 'internal_ops'")
except Group.DoesNotExist:
    print("❌ Grupo 'internal_ops' não encontrado")

print("\n🎉 Superusuário configurado!")
print(f"\n📝 Para acessar o admin:")
print(f"   URL: http://localhost:8000/admin/")
print(f"   Username: {username}")
print(f"   Password: {password}")
