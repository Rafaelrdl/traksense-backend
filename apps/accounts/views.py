"""
Authentication and user profile views.
"""

import io
import uuid
from datetime import datetime

from django.conf import settings
from django.contrib.auth import login, logout
from django.utils import timezone
from minio import Minio
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.accounts.models import User
from apps.accounts.serializers import (
    ChangePasswordSerializer,
    CustomTokenObtainPairSerializer,
    LoginSerializer,
    RegisterSerializer,
    UserSerializer,
    UserUpdateSerializer,
)
from apps.common.storage import get_minio_client


class RegisterView(generics.CreateAPIView):
    """
    User registration endpoint.
    
    POST /api/auth/register
    {
        "username": "johndoe",
        "email": "john@example.com",
        "password": "SecurePass123!",
        "password_confirm": "SecurePass123!",
        "first_name": "John",
        "last_name": "Doe"
    }
    """
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'message': 'Usuário registrado com sucesso!'
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """
    User login endpoint.
    
    POST /api/auth/login
    {
        "username_or_email": "john@example.com",
        "password": "SecurePass123!"
    }
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']
        
        # Update last login IP
        user.last_login_ip = self.get_client_ip(request)
        user.save(update_fields=['last_login_ip', 'last_login'])
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        response_data = {
            'user': UserSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'message': 'Login realizado com sucesso!'
        }
        
        # Create response with HttpOnly cookies
        response = Response(response_data, status=status.HTTP_200_OK)
        
        # Set cookies (optional - for cookie-based auth)
        response.set_cookie(
            key='access_token',
            value=str(refresh.access_token),
            httponly=True,
            secure=not settings.DEBUG,
            samesite='Lax',
            max_age=3600,  # 1 hour
        )
        response.set_cookie(
            key='refresh_token',
            value=str(refresh),
            httponly=True,
            secure=not settings.DEBUG,
            samesite='Lax',
            max_age=604800,  # 7 days
        )
        
        return response
    
    def get_client_ip(self, request):
        """Get client IP from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class LogoutView(APIView):
    """
    User logout endpoint.
    
    POST /api/auth/logout
    
    Note: In multi-tenant setup, token blacklist is disabled.
    Tokens will naturally expire based on their lifetime.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            response = Response({
                'message': 'Logout realizado com sucesso!'
            }, status=status.HTTP_200_OK)
            
            # Clear cookies
            response.delete_cookie('access_token')
            response.delete_cookie('refresh_token')
            
            return response
            
        except Exception as e:
            return Response({
                'error': 'Erro ao fazer logout.',
                'details': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom token obtain view with user data.
    """
    serializer_class = CustomTokenObtainPairSerializer


class MeView(APIView):
    """
    Current user profile endpoint.
    
    GET /api/users/me - Get current user
    PATCH /api/users/me - Update current user
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get current user profile."""
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    
    def patch(self, request):
        """Update current user profile."""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"🔄 PATCH /api/users/me/ - Data recebida: {request.data}")
        
        serializer = UserUpdateSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        # Refresh para pegar dados atualizados
        request.user.refresh_from_db()
        
        # Serializa usuário atualizado
        user_data = UserSerializer(request.user).data
        
        logger.info(f"✅ PATCH /api/users/me/ - User data serializado: {user_data}")
        logger.info(f"🕐 PATCH /api/users/me/ - time_format no response: {user_data.get('time_format', 'MISSING')}")
        
        return Response({
            'user': user_data,
            'message': 'Perfil atualizado com sucesso!'
        })


class ChangePasswordView(APIView):
    """
    Change password endpoint.
    
    POST /api/users/me/change-password
    {
        "old_password": "OldPass123!",
        "new_password": "NewPass123!",
        "new_password_confirm": "NewPass123!"
    }
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({
            'message': 'Senha alterada com sucesso!'
        }, status=status.HTTP_200_OK)


class AvatarUploadView(APIView):
    """
    Avatar upload endpoint using MinIO.
    
    POST /api/users/me/avatar
    Content-Type: multipart/form-data
    
    Body:
    - avatar: image file (jpg, png, gif)
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Upload user avatar to MinIO."""
        avatar_file = request.FILES.get('avatar')
        
        if not avatar_file:
            return Response({
                'error': 'Nenhum arquivo enviado.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate file type
        allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
        if avatar_file.content_type not in allowed_types:
            return Response({
                'error': 'Tipo de arquivo não permitido. Use JPG, PNG, GIF ou WebP.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate file size (max 5MB)
        max_size = 5 * 1024 * 1024  # 5MB
        if avatar_file.size > max_size:
            return Response({
                'error': 'Arquivo muito grande. Tamanho máximo: 5MB.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Get MinIO client
            minio_client = get_minio_client()
            
            # Ensure bucket exists
            bucket_name = settings.MINIO_BUCKET
            if not minio_client.bucket_exists(bucket_name):
                minio_client.make_bucket(bucket_name)
            
            # Generate unique filename
            file_extension = avatar_file.name.split('.')[-1]
            filename = f"avatars/{request.user.id}/{uuid.uuid4()}.{file_extension}"
            
            # Upload to MinIO
            minio_client.put_object(
                bucket_name,
                filename,
                avatar_file,
                length=avatar_file.size,
                content_type=avatar_file.content_type,
            )
            
            # Generate avatar URL
            avatar_url = f"http://{settings.MINIO_ENDPOINT}/{bucket_name}/{filename}"
            
            # Update user avatar
            request.user.avatar = avatar_url
            request.user.save(update_fields=['avatar'])
            
            return Response({
                'avatar': avatar_url,
                'message': 'Avatar atualizado com sucesso!'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': 'Erro ao fazer upload do avatar.',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request):
        """Remove user avatar."""
        request.user.avatar = None
        request.user.save(update_fields=['avatar'])
        
        return Response({
            'message': 'Avatar removido com sucesso!'
        }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint for authentication service.
    """
    return Response({
        'status': 'ok',
        'service': 'authentication',
        'timestamp': timezone.now().isoformat(),
    })
