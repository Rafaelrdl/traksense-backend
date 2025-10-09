"""
Views para autenticação JWT

CustomTokenObtainPairView: Login retornando tokens + user object
LogoutView: Logout com blacklist de refresh token
"""

from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import CustomTokenObtainPairSerializer, LogoutSerializer


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    View de login customizada.
    
    POST /api/auth/login/
    Body: {"username": "admin", "password": "admin"}
    Response: {
        "access": "<access_token>",
        "refresh": "<refresh_token>",
        "user": {...}
    }
    """
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [AllowAny]


class LogoutView(APIView):
    """
    View de logout.
    
    Adiciona refresh token à blacklist para invalidar.
    
    POST /api/auth/logout/
    Headers: Authorization: Bearer <access_token>
    Body: {"refresh": "<refresh_token>"}
    Response: {"detail": "Logout realizado com sucesso"}
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(
            {"detail": "Logout realizado com sucesso"},
            status=status.HTTP_200_OK
        )
