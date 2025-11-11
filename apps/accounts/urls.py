"""
URL Configuration for accounts app (authentication & user management).
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.accounts import views
from apps.accounts.views_team import TeamMemberViewSet, InviteViewSet

app_name = 'accounts'

# Router for team management
router = DefaultRouter()
router.register(r'team/members', TeamMemberViewSet, basename='team-members')
router.register(r'team/invites', InviteViewSet, basename='team-invites')

urlpatterns = [
    # Health check
    path('health/', views.health_check, name='health'),
    
    # Authentication
    path('auth/register/', views.RegisterView.as_view(), name='register'),
    path('auth/login/', views.LoginView.as_view(), name='login'),
    path('auth/logout/', views.LogoutView.as_view(), name='logout'),
    # 🔐 SECURITY: Use cookie-based token refresh (not standard TokenRefreshView)
    path('auth/token/refresh/', views.CookieTokenRefreshView.as_view(), name='token_refresh'),
    
    # User profile
    path('users/me/', views.MeView.as_view(), name='me'),
    path('users/me/avatar/', views.AvatarUploadView.as_view(), name='avatar_upload'),
    path('users/me/change-password/', views.ChangePasswordView.as_view(), name='change_password'),
    
    # Team management (router)
    path('', include(router.urls)),
]
