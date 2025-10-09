"""
TrakSense Authentication App

Responsável pela autenticação JWT:
- Login com username/password → retorna access + refresh tokens
- Refresh de access token usando refresh token
- Logout com blacklist de refresh token
"""
