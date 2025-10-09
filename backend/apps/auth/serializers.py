"""
Serializers para autenticação JWT

CustomTokenObtainPairSerializer: Adiciona dados do usuário (user object) na resposta de login
LogoutSerializer: Serializa refresh token para blacklist
"""

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Serializer customizado para obter tokens JWT.
    
    Adiciona dados do usuário na resposta:
    {
        "access": "<access_token>",
        "refresh": "<refresh_token>",
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
        # Chama validação padrão (retorna access + refresh tokens)
        data = super().validate(attrs)
        
        # Adiciona dados do usuário
        user = self.user
        
        # Obter tenant_id do usuário (se existir relação)
        tenant_id = None
        tenant_name = None
        if hasattr(user, 'tenant'):
            tenant_id = str(user.tenant.id) if user.tenant else None
            tenant_name = user.tenant.name if user.tenant else None
        
        # Obter grupos do usuário
        groups = list(user.groups.values_list('name', flat=True))
        
        data['user'] = {
            'id': str(user.id),
            'username': user.username,
            'email': user.email,
            'tenant_id': tenant_id,
            'tenant_name': tenant_name,
            'groups': groups,
        }
        
        return data


class LogoutSerializer(serializers.Serializer):
    """
    Serializer para logout.
    
    Recebe refresh token e adiciona à blacklist.
    """
    refresh = serializers.CharField(required=True, help_text="Refresh token to blacklist")
    
    def validate(self, attrs):
        self.token = attrs['refresh']
        return attrs
    
    def save(self, **kwargs):
        try:
            from rest_framework_simplejwt.tokens import RefreshToken
            token = RefreshToken(self.token)
            token.blacklist()
        except Exception as e:
            raise serializers.ValidationError(f"Token inválido: {str(e)}")
