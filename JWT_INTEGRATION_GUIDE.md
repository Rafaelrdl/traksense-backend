# 🔐 Guia de Integração - JWT Authentication Backend

**Objetivo**: Configurar endpoints de autenticação JWT no backend Django para integrar com o frontend React.

---

## 📋 Pré-requisitos

- Django 4+
- Django REST Framework instalado
- Backend TrakSense rodando em `http://localhost:8000`

---

## 🚀 Passo 1: Instalar Simple JWT

```bash
cd traksense-backend/backend
pip install djangorestframework-simplejwt
pip freeze > requirements.txt
```

---

## ⚙️ Passo 2: Configurar `settings.py`

### 2.1 Adicionar ao INSTALLED_APPS

```python
# backend/core/settings.py

INSTALLED_APPS = [
    ...
    'rest_framework',
    'rest_framework_simplejwt',  # ← ADICIONAR
    'rest_framework_simplejwt.token_blacklist',  # ← Para logout (opcional)
]
```

### 2.2 Configurar REST_FRAMEWORK

```python
# backend/core/settings.py

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',  # ← JWT
        'rest_framework.authentication.SessionAuthentication',  # ← Manter para Swagger UI
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    ...
}
```

### 2.3 Configurar SIMPLE_JWT

```python
# backend/core/settings.py

from datetime import timedelta

SIMPLE_JWT = {
    # Tempo de vida dos tokens
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    
    # Rotação de refresh tokens (gera novo refresh a cada uso)
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,  # Blacklist tokens antigos
    
    # Algoritmo de assinatura
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    
    # Headers
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    
    # Claims do token
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    
    # Token customization
    'TOKEN_OBTAIN_SERIALIZER': 'apps.auth.serializers.CustomTokenObtainPairSerializer',  # ← Customizar depois
}
```

---

## 📁 Passo 3: Criar App de Autenticação

```bash
python manage.py startapp auth
# OU criar diretório manualmente: backend/apps/auth/
```

### 3.1 Estrutura de arquivos

```
backend/apps/auth/
├── __init__.py
├── serializers.py  ← Criar
├── views.py
└── urls.py  ← Criar
```

---

## 📝 Passo 4: Criar Serializer Customizado

**Arquivo**: `backend/apps/auth/serializers.py`

```python
"""
Auth Serializers - Customização de resposta de login
"""
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Serializer customizado para adicionar informações do usuário na resposta.
    
    Frontend espera:
    {
        "access": "...",
        "refresh": "...",
        "user": {
            "id": "uuid",
            "username": "admin",
            "email": "admin@example.com",
            "tenant_id": "uuid",
            "tenant_name": "Alpha Corp",
            "groups": ["internal_ops"]
        }
    }
    """
    
    def validate(self, attrs):
        # Obter tokens padrão
        data = super().validate(attrs)
        
        # Adicionar informações do usuário
        user = self.user
        
        data['user'] = {
            'id': str(user.id),
            'username': user.username,
            'email': user.email or '',
            'tenant_id': self._get_tenant_id(user),
            'tenant_name': self._get_tenant_name(user),
            'groups': list(user.groups.values_list('name', flat=True)),
        }
        
        return data
    
    def _get_tenant_id(self, user):
        """Obter tenant_id do usuário (depende da sua implementação)"""
        if hasattr(user, 'tenant_id'):
            return str(user.tenant_id)
        if hasattr(user, 'tenant'):
            return str(user.tenant.id)
        return None
    
    def _get_tenant_name(self, user):
        """Obter nome do tenant"""
        if hasattr(user, 'tenant') and user.tenant:
            return user.tenant.name
        return None


class LogoutSerializer(serializers.Serializer):
    """Serializer para logout (blacklist do refresh token)"""
    refresh = serializers.CharField()
    
    def validate(self, attrs):
        self.token = attrs['refresh']
        return attrs
    
    def save(self, **kwargs):
        from rest_framework_simplejwt.tokens import RefreshToken
        try:
            RefreshToken(self.token).blacklist()
        except Exception as e:
            raise serializers.ValidationError({'detail': 'Token inválido ou já expirado'})
```

---

## 🔗 Passo 5: Adicionar URLs

**Arquivo**: `backend/core/urls.py`

```python
# backend/core/urls.py

from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)
from apps.auth.views import CustomTokenObtainPairView, LogoutView

urlpatterns = [
    # ... outras URLs
    
    # ============================================================================
    # Authentication (JWT)
    # ============================================================================
    path('api/auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/logout/', LogoutView.as_view(), name='token_logout'),
    
    # ... resto das URLs
]
```

---

## 🎨 Passo 6: Criar Views Customizadas

**Arquivo**: `backend/apps/auth/views.py`

```python
"""
Auth Views - Endpoints de autenticação
"""
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .serializers import CustomTokenObtainPairSerializer, LogoutSerializer


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    POST /api/auth/login/
    
    Body:
    {
        "username": "admin",
        "password": "senha"
    }
    
    Response:
    {
        "access": "eyJ0eXAiOiJKV1QiLCJ...",
        "refresh": "eyJ0eXAiOiJKV1QiLCJ...",
        "user": {
            "id": "uuid",
            "username": "admin",
            "email": "admin@example.com",
            "tenant_id": "uuid",
            "tenant_name": "Alpha Corp",
            "groups": ["internal_ops"]
        }
    }
    """
    serializer_class = CustomTokenObtainPairSerializer


class LogoutView(APIView):
    """
    POST /api/auth/logout/
    
    Headers:
        Authorization: Bearer <access_token>
    
    Body:
    {
        "refresh": "eyJ0eXAiOiJKV1QiLCJ..."
    }
    
    Response:
    {
        "detail": "Logout realizado com sucesso"
    }
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {'detail': 'Logout realizado com sucesso'},
            status=status.HTTP_200_OK
        )
```

---

## 🗄️ Passo 7: Rodar Migrações (para blacklist)

```bash
python manage.py migrate
```

Isso criará as tabelas `token_blacklist` se você habilitou `BLACKLIST_AFTER_ROTATION`.

---

## 🧪 Passo 8: Testar Endpoints

### 8.1 Login

```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin"
  }'
```

**Resposta esperada** (200 OK):
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "admin",
    "email": "admin@traksense.com",
    "tenant_id": "11111111-1111-1111-1111-111111111111",
    "tenant_name": "Alpha Corp",
    "groups": ["internal_ops"]
  }
}
```

### 8.2 Refresh Token

```bash
curl -X POST http://localhost:8000/api/auth/refresh/ \
  -H "Content-Type: application/json" \
  -d '{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }'
```

**Resposta esperada** (200 OK):
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc... (novo token)",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc... (novo se ROTATE_REFRESH_TOKENS=True)"
}
```

### 8.3 Logout

```bash
curl -X POST http://localhost:8000/api/auth/logout/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..." \
  -d '{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }'
```

**Resposta esperada** (200 OK):
```json
{
  "detail": "Logout realizado com sucesso"
}
```

### 8.4 Acessar Endpoint Protegido

```bash
curl http://localhost:8000/api/data/points?device_id=xxx&point_id=yyy&from=2025-01-01T00:00:00Z&to=2025-01-02T00:00:00Z&agg=1h \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."
```

---

## 🔒 Passo 9: Configurar CORS

**Arquivo**: `backend/core/settings.py`

```python
# Adicionar frontend ao CORS_ALLOWED_ORIGINS
CORS_ALLOWED_ORIGINS = [
    'http://localhost:5173',  # Vite dev server
    'http://localhost:3000',  # Alternativo
]

# Permitir credentials (cookies + Authorization header)
CORS_ALLOW_CREDENTIALS = True

# Headers permitidos
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]
```

---

## ✅ Passo 10: Testar Integração Frontend

### 10.1 Iniciar backend

```bash
cd traksense-backend/infra
docker compose up -d
```

### 10.2 Iniciar frontend

```bash
cd traksense-frontend
npm run dev
```

### 10.3 Testar fluxo

1. **Acesse**: http://localhost:5173/login
2. **Credenciais**: `admin` / `admin` (ou crie superuser)
3. **Esperado**: Login bem-sucedido, toast de "Bem-vindo", redirect para `/`
4. **Verificar**: localStorage deve conter `traksense_access_token`
5. **Testar rota protegida**: http://localhost:5173/devices/test-device
6. **Logout**: Clicar no avatar → "Sair"

---

## 🐛 Troubleshooting

### Problema: CORS error
**Solução**: Verificar `CORS_ALLOWED_ORIGINS` inclui `http://localhost:5173`

### Problema: 401 Unauthorized em endpoints protegidos
**Solução**: Verificar se token está sendo enviado no header `Authorization: Bearer <token>`

### Problema: Token expirado muito rápido
**Solução**: Aumentar `ACCESS_TOKEN_LIFETIME` em `SIMPLE_JWT`

### Problema: Refresh token não funciona
**Solução**: Verificar se `ROTATE_REFRESH_TOKENS` e `BLACKLIST_AFTER_ROTATION` estão configurados

### Problema: Usuário não tem tenant_id
**Solução**: Adicionar campo `tenant_id` ao modelo User ou usar relacionamento ForeignKey

---

## 📚 Documentação Adicional

- [djangorestframework-simplejwt](https://django-rest-framework-simplejwt.readthedocs.io/)
- [Django REST Framework Authentication](https://www.django-rest-framework.org/api-guide/authentication/)
- [JWT.io - Debugger](https://jwt.io/)

---

## 🎉 Conclusão

Após seguir este guia, você terá:
- ✅ Endpoints `/api/auth/login/`, `/api/auth/refresh/`, `/api/auth/logout/` funcionando
- ✅ Tokens JWT gerados e validados
- ✅ Frontend integrado e autenticando corretamente
- ✅ Proteção de rotas funcionando
- ✅ Refresh automático de tokens

**Próximo passo**: Testar end-to-end e ajustar conforme necessário!
