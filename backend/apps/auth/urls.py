"""
URLs para autenticação JWT

Endpoints:
- POST /login/ → Login com username/password
- POST /refresh/ → Refresh access token
- POST /logout/ → Logout com blacklist
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import CustomTokenObtainPairView, LogoutView

urlpatterns = [
    # Login: username/password → access + refresh tokens + user object
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    
    # Refresh: refresh token → new access token
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Logout: blacklist refresh token
    path('logout/', LogoutView.as_view(), name='logout'),
]
