"""
Script para criar tenant 'localhost' para desenvolvimento local.

Este tenant é usado quando acessamos a API via localhost:8000.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.tenancy.models import Client, Domain

# Criar tenant localhost (se não existir)
try:
    client, created = Client.objects.get_or_create(
        schema_name='public',
        defaults={
            'name': 'Public Tenant',
            'code': 'PUBLIC',
        }
    )
    if created:
        print(f"✅ Tenant '{client.schema_name}' criado com sucesso!")
    else:
        print(f"ℹ️  Tenant '{client.schema_name}' já existe.")
    
    # Criar domínio localhost
    domain, created = Domain.objects.get_or_create(
        domain='localhost',
        defaults={'tenant': client, 'is_primary': True}
    )
    if created:
        print(f"✅ Domínio 'localhost' criado e associado ao tenant '{client.schema_name}'!")
    else:
        print(f"ℹ️  Domínio 'localhost' já existe.")
        
    print("\n🎉 Setup conclu��do! Agora você pode acessar http://localhost:8000/health")
    
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()
