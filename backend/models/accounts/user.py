"""
User models for MoonVPN.

This module defines the User model and related models for account management.
"""

from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import uuid
import secrets
import string

class UserManager(BaseUserManager):
    """Custom user manager."""
    
    def create_user(self, username, email=None, password=None, **extra_fields):
        """Create and save a regular user."""
        if not username:
            raise ValueError('Username is required')
            
        email = self.normalize_email(email) if email else None
        
        user = self.model(
            username=username,
            email=email,
            **extra_fields
        )
        
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
            
        user.save(using=self._db)
        return user
    
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        """Create and save a superuser."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 'admin')
        
        return self.create_user(username, email, password, **extra_fields)
    
    def create_from_telegram(self, telegram_id, first_name, username=None, last_name=None, **extra_fields):
        """Create a user from Telegram data."""
        # Generate a unique username if not provided
        if not username:
            username = f"tg_{telegram_id}"
            
        # Generate a random password
        alphabet = string.ascii_letters + string.digits
        password = ''.join(secrets.choice(alphabet) for _ in range(20))
        
        user = self.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            telegram_id=telegram_id,
            **extra_fields
        )
        
        return user


class User(AbstractUser):
    """Custom user model."""
    
    ROLE_CHOICES = [
        ('user', _('User')),
        ('admin', _('Admin')),
        ('seller', _('Seller')),
    ]
    
    telegram_id = models.BigIntegerField(
        null=True,
        blank=True,
        unique=True,
        help_text=_("Telegram user ID")
    )
    
    phone = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text=_("Phone number")
    )
    
    language = models.CharField(
        max_length=10,
        default='fa',
        help_text=_("Preferred language code")
    )
    
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='user',
        help_text=_("User role")
    )
    
    referral_code = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True,
        help_text=_("Referral code for inviting other users")
    )
    
    referred_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='referrals',
        help_text=_("User who referred this user")
    )
    
    objects = UserManager()
    
    def save(self, *args, **kwargs):
        """Generate a referral code if not set."""
        if not self.referral_code:
            self.referral_code = self._generate_referral_code()
        super().save(*args, **kwargs)
    
    def _generate_referral_code(self):
        """Generate a unique referral code."""
        while True:
            code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
            if not User.objects.filter(referral_code=code).exists():
                return code
    
    def is_admin(self):
        """Check if this user is an admin."""
        return self.role == 'admin' or self.is_superuser
    
    def is_seller(self):
        """Check if this user is a seller."""
        return self.role == 'seller'
    
    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")


class AdminGroup(models.Model):
    """Model for admin group chats in Telegram."""
    
    GROUP_TYPES = [
        ('management', _('Management')),
        ('reports', _('Reports')),
        ('logs', _('Logs')),
        ('orders', _('Orders')),
        ('outages', _('Outages')),
        ('sellers', _('Sellers')),
        ('backups', _('Backups')),
    ]
    
    name = models.CharField(
        max_length=255,
        help_text=_("Group name")
    )
    
    telegram_chat_id = models.BigIntegerField(
        unique=True,
        help_text=_("Telegram chat ID")
    )
    
    type = models.CharField(
        max_length=20,
        choices=GROUP_TYPES,
        help_text=_("Group type")
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text=_("Whether this group is active")
    )
    
    description = models.TextField(
        null=True,
        blank=True,
        help_text=_("Group description")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"
    
    class Meta:
        verbose_name = _("Admin Group")
        verbose_name_plural = _("Admin Groups")


class UserActivity(models.Model):
    """Model for tracking user activity."""
    
    ACTIVITY_TYPES = [
        ('login', _('Login')),
        ('purchase', _('Purchase')),
        ('renewal', _('Renewal')),
        ('referral', _('Referral')),
        ('traffic_alert', _('Traffic Alert')),
        ('expiration_alert', _('Expiration Alert')),
        ('support_request', _('Support Request')),
        ('wallet_deposit', _('Wallet Deposit')),
        ('account_creation', _('Account Creation')),
        ('settings_change', _('Settings Change')),
    ]
    
    user = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='activities',
        help_text=_("User who performed the activity")
    )
    
    activity_type = models.CharField(
        max_length=20,
        choices=ACTIVITY_TYPES,
        help_text=_("Type of activity")
    )
    
    description = models.TextField(
        null=True,
        blank=True,
        help_text=_("Activity description")
    )
    
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text=_("IP address where the activity originated")
    )
    
    user_agent = models.TextField(
        null=True,
        blank=True,
        help_text=_("User agent string")
    )
    
    metadata = models.JSONField(
        null=True,
        blank=True,
        help_text=_("Additional metadata about the activity")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.get_activity_type_display()} by {self.user.username}"
    
    class Meta:
        verbose_name = _("User Activity")
        verbose_name_plural = _("User Activities")
        ordering = ['-created_at'] 