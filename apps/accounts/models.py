"""
User and membership models.

This module will be expanded in Phase 1 (Auth & User).
For Phase 0, we just need a basic placeholder.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser.
    
    This will be expanded in Phase 1 with:
    - Custom fields (avatar, phone, etc.)
    - Tenant membership relationships
    - Authentication methods
    
    For now, it's a placeholder to enable tenant seeding.
    """
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return self.email or self.username
