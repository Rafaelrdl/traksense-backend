"""
User and membership models for authentication and multi-tenant access.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    """
    Custom User model with additional fields for profile management.
    
    Extends Django's AbstractUser with:
    - Avatar image support (stored in MinIO)
    - Phone number
    - Bio/description
    - Email verification status
    - Timezone preference
    """
    
    # Profile fields
    email = models.EmailField('Email', unique=True)
    avatar = models.CharField('Avatar URL', max_length=500, blank=True, null=True)
    phone = models.CharField('Phone', max_length=20, blank=True, null=True)
    bio = models.TextField('Bio', blank=True, null=True)
    
    # Preferences
    timezone = models.CharField('Timezone', max_length=50, default='America/Sao_Paulo')
    language = models.CharField('Language', max_length=10, default='pt-br')
    
    # Status
    email_verified = models.BooleanField('Email Verified', default=False)
    last_login_ip = models.GenericIPAddressField('Last Login IP', blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField('Created At', auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField('Updated At', auto_now=True)
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.email or self.username
    
    @property
    def full_name(self):
        """Return the user's full name."""
        return f"{self.first_name} {self.last_name}".strip() or self.username
    
    @property
    def initials(self):
        """Return the user's initials for avatar fallback."""
        if self.first_name and self.last_name:
            return f"{self.first_name[0]}{self.last_name[0]}".upper()
        elif self.first_name:
            return self.first_name[0].upper()
        return self.username[0].upper() if self.username else "U"

