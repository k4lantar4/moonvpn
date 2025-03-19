"""
VPN Account model for MoonVPN.

This module defines the VPN Account model for managing VPN accounts.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import uuid

class VPNAccount(models.Model):
    """Model for VPN accounts."""
    
    STATUS_CHOICES = [
        ('active', _('Active')),
        ('expired', _('Expired')),
        ('traffic_exceeded', _('Traffic Exceeded')),
        ('disabled', _('Disabled')),
        ('pending', _('Pending Creation')),
    ]
    
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='vpn_accounts',
        help_text=_("User who owns this account")
    )
    
    server = models.ForeignKey(
        'vpn.Server',
        on_delete=models.CASCADE,
        related_name='accounts',
        help_text=_("Server hosting this account")
    )
    
    email = models.EmailField(
        unique=True,
        help_text=_("Email identifier used in 3x-UI panel")
    )
    
    uuid = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        help_text=_("Unique identifier for this account")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    expires_at = models.DateTimeField(
        help_text=_("When this account expires")
    )
    
    last_sync = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("Last time this account was synchronized with the panel")
    )
    
    total_traffic_gb = models.IntegerField(
        help_text=_("Total traffic limit in GB")
    )
    
    used_traffic_gb = models.IntegerField(
        default=0,
        help_text=_("Used traffic in GB")
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text=_("Current status of this account")
    )
    
    remark = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text=_("Custom name in panel")
    )
    
    connection_string = models.TextField(
        null=True,
        blank=True,
        help_text=_("Cached connection config")
    )
    
    max_connections = models.IntegerField(
        default=1,
        help_text=_("Maximum number of concurrent connections")
    )
    
    def get_remaining_traffic(self):
        """Get the remaining traffic for this account."""
        return max(0, self.total_traffic_gb - self.used_traffic_gb)
    
    def get_remaining_days(self):
        """Get the number of days remaining until expiration."""
        if self.expires_at > timezone.now():
            return (self.expires_at - timezone.now()).days
        return 0
    
    def is_expired(self):
        """Check if this account is expired."""
        return self.expires_at < timezone.now()
    
    def has_traffic(self):
        """Check if this account has remaining traffic."""
        return self.used_traffic_gb < self.total_traffic_gb
    
    def migrate_to_server(self, new_server, initiated_by='system'):
        """Migrate this account to a different server."""
        from backend.models.vpn.server import ServerMigration
        
        old_server = self.server
        self.server = new_server
        self.status = 'pending'  # Will be recreated on new server
        self.save(update_fields=['server', 'status', 'last_sync'])
        
        migration = ServerMigration.objects.create(
            vpn_account=self,
            from_server=old_server,
            to_server=new_server,
            initiated_by=initiated_by
        )
        
        # Update server statistics
        old_server.current_clients -= 1
        old_server.update_load_factor()
        
        new_server.current_clients += 1
        new_server.update_load_factor()
        
        return migration
    
    def __str__(self):
        return f"{self.email} ({self.user.username})"
    
    class Meta:
        verbose_name = _("VPN Account")
        verbose_name_plural = _("VPN Accounts")


class SubscriptionPlan(models.Model):
    """Model for subscription plans."""
    
    name = models.CharField(
        max_length=255,
        help_text=_("Plan name")
    )
    
    duration_days = models.IntegerField(
        help_text=_("Duration in days")
    )
    
    traffic_limit_gb = models.IntegerField(
        help_text=_("Traffic limit in GB")
    )
    
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text=_("Price in default currency")
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text=_("Whether this plan is active and available")
    )
    
    is_featured = models.BooleanField(
        default=False,
        help_text=_("Whether this plan should be featured")
    )
    
    max_connections = models.IntegerField(
        default=1,
        help_text=_("Maximum number of concurrent connections")
    )
    
    description = models.TextField(
        null=True,
        blank=True,
        help_text=_("Optional description for this plan")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def get_monthly_price(self):
        """Calculate the monthly equivalent price for comparison."""
        if self.duration_days >= 28:
            return (self.price / self.duration_days) * 30
        return self.price
    
    def __str__(self):
        return f"{self.name} ({self.duration_days} days, {self.traffic_limit_gb} GB)"
    
    class Meta:
        verbose_name = _("Subscription Plan")
        verbose_name_plural = _("Subscription Plans") 