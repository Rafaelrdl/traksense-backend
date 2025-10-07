"""
Script para criar grupos RBAC manualmente
Cria 3 grupos: internal_ops, customer_admin, viewer
"""
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from apps.devices.models import Device, DeviceTemplate, PointTemplate, Point
from apps.dashboards.models import DashboardTemplate, DashboardConfig

print("=== Criando grupos RBAC ===\n")

# 1. internal_ops (acesso total)
internal_ops, created = Group.objects.get_or_create(name='internal_ops')
if created:
    print("✅ Grupo 'internal_ops' criado")
    # Adicionar todas as permissões de Device, DeviceTemplate, PointTemplate
    for model in [Device, DeviceTemplate, PointTemplate, Point, DashboardTemplate, DashboardConfig]:
        ct = ContentType.objects.get_for_model(model)
        perms = Permission.objects.filter(content_type=ct)
        internal_ops.permissions.add(*perms)
    print(f"   {internal_ops.permissions.count()} permissões adicionadas")
else:
    print(f"ℹ️  Grupo 'internal_ops' já existe ({internal_ops.permissions.count()} permissões)")

# 2. customer_admin (view + commands)
customer_admin, created = Group.objects.get_or_create(name='customer_admin')
if created:
    print("✅ Grupo 'customer_admin' criado")
    # Adicionar apenas permissões de view para Device e Point
    for model in [Device, Point, DashboardConfig]:
        ct = ContentType.objects.get_for_model(model)
        view_perm = Permission.objects.filter(content_type=ct, codename__startswith='view')
        customer_admin.permissions.add(*view_perm)
    print(f"   {customer_admin.permissions.count()} permissões adicionadas")
else:
    print(f"ℹ️  Grupo 'customer_admin' já existe ({customer_admin.permissions.count()} permissões)")

# 3. viewer (somente leitura)
viewer, created = Group.objects.get_or_create(name='viewer')
if created:
    print("✅ Grupo 'viewer' criado")
    # Adicionar apenas permissões de view
    for model in [Device, Point, DashboardConfig]:
        ct = ContentType.objects.get_for_model(model)
        view_perm = Permission.objects.filter(content_type=ct, codename__startswith='view')
        viewer.permissions.add(*view_perm)
    print(f"   {viewer.permissions.count()} permissões adicionadas")
else:
    print(f"ℹ️  Grupo 'viewer' já existe ({viewer.permissions.count()} permissões)")

print("\n=== Resumo ===")
for group in Group.objects.all():
    print(f"✅ {group.name}: {group.permissions.count()} permissões")

print("\n🎉 Grupos RBAC criados com sucesso!")
