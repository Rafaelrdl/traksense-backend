"""
Data Migration - RBAC Groups and Permissions

Cria grupos de usuários e suas permissões para controle de acesso.

Grupos criados:
--------------
1. internal_ops: Acesso completo (CRUD) a todos os modelos
2. customer_admin: Apenas visualização (view)
3. viewer: Apenas visualização (view)

Permissões:
----------
- internal_ops: add, change, delete, view em todos os modelos
- customer_admin: view em todos os modelos
- viewer: view em todos os modelos

Modelos:
-------
- DeviceTemplate, PointTemplate, Device, Point
- DashboardTemplate, DashboardConfig

Autor: TrakSense Team
Data: 2025-10-07 (Fase 2)
"""

from django.db import migrations
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType


def create_rbac_groups(apps, schema_editor):
    """
    Cria grupos e atribui permissões.
    
    Note: Usa apps registry para obter modelos (melhor prática em migrations)
    """
    
    # Obter modelos via apps registry
    DeviceTemplate = apps.get_model('devices', 'DeviceTemplate')
    PointTemplate = apps.get_model('devices', 'PointTemplate')
    Device = apps.get_model('devices', 'Device')
    Point = apps.get_model('devices', 'Point')
    DashboardTemplate = apps.get_model('dashboards', 'DashboardTemplate')
    DashboardConfig = apps.get_model('dashboards', 'DashboardConfig')
    
    # Lista de modelos para aplicar permissões
    models = [
        DeviceTemplate,
        PointTemplate,
        Device,
        Point,
        DashboardTemplate,
        DashboardConfig,
    ]
    
    # =========================================================================
    # GRUPO 1: internal_ops (Acesso completo)
    # =========================================================================
    
    internal_ops, created = Group.objects.get_or_create(name='internal_ops')
    
    if created:
        print("✓ Grupo 'internal_ops' criado")
    else:
        print("⚠ Grupo 'internal_ops' já existe")
    
    # Adicionar todas as permissões (add, change, delete, view)
    for model in models:
        content_type = ContentType.objects.get_for_model(model)
        permissions = Permission.objects.filter(content_type=content_type)
        internal_ops.permissions.add(*permissions)
    
    print(f"  → {internal_ops.permissions.count()} permissões atribuídas")
    
    # =========================================================================
    # GRUPO 2: customer_admin (Visualização apenas)
    # =========================================================================
    
    customer_admin, created = Group.objects.get_or_create(name='customer_admin')
    
    if created:
        print("✓ Grupo 'customer_admin' criado")
    else:
        print("⚠ Grupo 'customer_admin' já existe")
    
    # Adicionar apenas permissões de visualização (view)
    for model in models:
        content_type = ContentType.objects.get_for_model(model)
        view_perm = Permission.objects.filter(
            content_type=content_type,
            codename__startswith='view_'
        )
        customer_admin.permissions.add(*view_perm)
    
    print(f"  → {customer_admin.permissions.count()} permissões atribuídas")
    
    # =========================================================================
    # GRUPO 3: viewer (Visualização apenas)
    # =========================================================================
    
    viewer, created = Group.objects.get_or_create(name='viewer')
    
    if created:
        print("✓ Grupo 'viewer' criado")
    else:
        print("⚠ Grupo 'viewer' já existe")
    
    # Adicionar apenas permissões de visualização (view)
    for model in models:
        content_type = ContentType.objects.get_for_model(model)
        view_perm = Permission.objects.filter(
            content_type=content_type,
            codename__startswith='view_'
        )
        viewer.permissions.add(*view_perm)
    
    print(f"  → {viewer.permissions.count()} permissões atribuídas")
    
    print("\n✅ Grupos RBAC criados com sucesso!")


def remove_rbac_groups(apps, schema_editor):
    """
    Remove grupos criados (rollback).
    """
    Group.objects.filter(name__in=['internal_ops', 'customer_admin', 'viewer']).delete()
    print("✓ Grupos RBAC removidos")


class Migration(migrations.Migration):
    """
    Migration de dados para criar grupos RBAC.
    
    IMPORTANTE: Esta migration deve rodar APÓS as migrations que criam
                os modelos de devices e dashboards.
    """
    
    dependencies = [
        ('devices', '0001_initial'),  # Ajustar conforme número da migration
        ('dashboards', '0001_initial'),  # Ajustar conforme número da migration
        ('auth', '0012_alter_user_first_name_max_length'),  # Última migration do auth
    ]
    
    operations = [
        migrations.RunPython(create_rbac_groups, remove_rbac_groups),
    ]
