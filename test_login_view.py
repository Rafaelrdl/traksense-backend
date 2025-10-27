"""
Teste de login direto dentro do Django
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from rest_framework.test import APIRequestFactory, force_authenticate
from apps.accounts.views import LoginView

factory = APIRequestFactory()

# Criar requisição
request = factory.post(
    '/api/auth/login/',
    {'username_or_email': 'testuser', 'password': 'test123'},
    format='json'
)

# Chamar a view
view = LoginView.as_view()
response = view(request)

print(f"Status Code: {response.status_code}")
print(f"Data: {response.data}")
