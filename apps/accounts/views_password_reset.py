"""
Password Reset Views.

Implements secure password reset flow:
1. User requests reset via email
2. System sends email with secure token
3. User clicks link and sets new password
"""

import secrets
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User, PasswordResetToken


class PasswordResetRequestView(APIView):
    """
    Request password reset email.
    
    POST /api/auth/password-reset/request/
    {
        "email": "user@example.com"
    }
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        email = request.data.get('email', '').lower().strip()
        
        if not email:
            return Response({
                'error': 'E-mail é obrigatório.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Always return success to prevent email enumeration
        success_response = Response({
            'message': 'Se o e-mail estiver cadastrado, você receberá um link para redefinir sua senha.'
        }, status=status.HTTP_200_OK)
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Return success anyway to prevent email enumeration
            return success_response
        
        # Invalidate any existing tokens for this user
        PasswordResetToken.objects.filter(user=user).delete()
        
        # Generate secure token
        token = secrets.token_urlsafe(32)
        expires_at = timezone.now() + timedelta(hours=1)
        
        # Save token
        PasswordResetToken.objects.create(
            user=user,
            token=token,
            expires_at=expires_at
        )
        
        # Build reset URL
        # Use frontend URL from request origin or settings
        frontend_url = request.headers.get('Origin', 'http://localhost:5173')
        reset_url = f"{frontend_url}/reset-password?token={token}"
        
        # Send email
        try:
            subject = 'Redefinição de Senha - Climatrak'
            
            html_message = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ text-align: center; padding: 20px 0; }}
                    .logo {{ font-size: 24px; font-weight: bold; color: #0d9488; }}
                    .content {{ background: #f9fafb; border-radius: 8px; padding: 30px; margin: 20px 0; }}
                    .button {{ display: inline-block; background: #0d9488; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; font-weight: 600; }}
                    .button:hover {{ background: #0f766e; }}
                    .footer {{ text-align: center; color: #6b7280; font-size: 12px; margin-top: 30px; }}
                    .warning {{ color: #dc2626; font-size: 14px; margin-top: 20px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <div class="logo">CLIMATRAK</div>
                    </div>
                    <div class="content">
                        <h2>Redefinição de Senha</h2>
                        <p>Olá, {user.first_name or user.username}!</p>
                        <p>Recebemos uma solicitação para redefinir a senha da sua conta.</p>
                        <p>Clique no botão abaixo para criar uma nova senha:</p>
                        <p style="text-align: center; margin: 30px 0;">
                            <a href="{reset_url}" class="button">Redefinir Senha</a>
                        </p>
                        <p class="warning">
                            ⚠️ Este link expira em 1 hora.<br>
                            Se você não solicitou esta redefinição, ignore este e-mail.
                        </p>
                    </div>
                    <div class="footer">
                        <p>Este é um e-mail automático, por favor não responda.</p>
                        <p>© {timezone.now().year} Climatrak. Todos os direitos reservados.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            plain_message = f"""
            Redefinição de Senha - Climatrak
            
            Olá, {user.first_name or user.username}!
            
            Recebemos uma solicitação para redefinir a senha da sua conta.
            
            Acesse o link abaixo para criar uma nova senha:
            {reset_url}
            
            ⚠️ Este link expira em 1 hora.
            Se você não solicitou esta redefinição, ignore este e-mail.
            
            ---
            Este é um e-mail automático, por favor não responda.
            © {timezone.now().year} Climatrak. Todos os direitos reservados.
            """
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )
            
        except Exception as e:
            # Log error but don't expose to user
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send password reset email: {e}")
        
        return success_response


class PasswordResetValidateView(APIView):
    """
    Validate password reset token.
    
    GET /api/auth/password-reset/validate/?token=xxx
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        token = request.query_params.get('token', '')
        
        if not token:
            return Response({
                'valid': False,
                'error': 'Token não fornecido.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            reset_token = PasswordResetToken.objects.get(token=token)
            
            if reset_token.is_expired():
                return Response({
                    'valid': False,
                    'error': 'Este link expirou. Solicite uma nova redefinição de senha.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if reset_token.used:
                return Response({
                    'valid': False,
                    'error': 'Este link já foi utilizado. Solicite uma nova redefinição de senha.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            return Response({
                'valid': True,
                'email': reset_token.user.email
            }, status=status.HTTP_200_OK)
            
        except PasswordResetToken.DoesNotExist:
            return Response({
                'valid': False,
                'error': 'Token inválido.'
            }, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmView(APIView):
    """
    Confirm password reset with new password.
    
    POST /api/auth/password-reset/confirm/
    {
        "token": "xxx",
        "password": "NewSecurePass123!",
        "password_confirm": "NewSecurePass123!"
    }
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        token = request.data.get('token', '')
        password = request.data.get('password', '')
        password_confirm = request.data.get('password_confirm', '')
        
        # Validate inputs
        if not token:
            return Response({
                'error': 'Token não fornecido.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not password or not password_confirm:
            return Response({
                'error': 'Senha e confirmação são obrigatórias.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if password != password_confirm:
            return Response({
                'error': 'As senhas não coincidem.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if len(password) < 6:
            return Response({
                'error': 'A senha deve ter pelo menos 6 caracteres.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            reset_token = PasswordResetToken.objects.get(token=token)
            
            if reset_token.is_expired():
                return Response({
                    'error': 'Este link expirou. Solicite uma nova redefinição de senha.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if reset_token.used:
                return Response({
                    'error': 'Este link já foi utilizado.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Update password
            user = reset_token.user
            user.set_password(password)
            user.save()
            
            # Mark token as used
            reset_token.used = True
            reset_token.save()
            
            return Response({
                'message': 'Senha redefinida com sucesso! Você já pode fazer login.'
            }, status=status.HTTP_200_OK)
            
        except PasswordResetToken.DoesNotExist:
            return Response({
                'error': 'Token inválido.'
            }, status=status.HTTP_400_BAD_REQUEST)
