from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.conf import settings
from django.contrib.auth import get_user_model
import uuid
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

class Server(models.Model):
    """VPN server information"""
    name = models.CharField(_('Name'), max_length=100)
    host = models.CharField(_('Host'), max_length=255)
    port = models.PositiveIntegerField(_('Port'), default=443)
    panel_port = models.PositiveIntegerField(_('Panel Port'), null=True, blank=True)
    is_active = models.BooleanField(_('Is Active'), default=True)
    location = models.CharField(_('Location'), max_length=100, null=True, blank=True)
    country_code = models.CharField(_('Country Code'), max_length=2, null=True, blank=True)
    description = models.TextField(_('Description'), null=True, blank=True)
    icon = models.CharField(_('Icon'), max_length=50, null=True, blank=True)
    
    # Technical settings
    inbound_ids = models.JSONField(_('Inbound IDs'), default=list)
    protocols = models.JSONField(_('Protocols'), default=list, help_text=_('List of supported protocols'))
    max_clients = models.PositiveIntegerField(_('Max Clients'), default=0, help_text=_('0 for unlimited'))
    bandwidth_limit_mbps = models.PositiveIntegerField(_('Bandwidth Limit (Mbps)'), default=0, help_text=_('0 for unlimited'))
    
    # Status monitoring
    is_online = models.BooleanField(_('Is Online'), default=True)
    last_check = models.DateTimeField(_('Last Check'), null=True, blank=True)
    status_data = models.JSONField(_('Status Data'), null=True, blank=True)
    
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    
    class Meta:
        verbose_name = _('Server')
        verbose_name_plural = _('Servers')
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.host})"
    
    def check_status(self):
        """Check server status"""
        # This would be implemented to check server health
        # and update the is_online and status_data fields
        pass


class VPNAccount(models.Model):
    """User VPN account"""
    STATUS_CHOICES = [
        ('active', _('Active')),
        ('expired', _('Expired')),
        ('disabled', _('Disabled')),
        ('suspended', _('Suspended')),
        ('traffic_exceeded', _('Traffic Exceeded')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vpn_accounts')
    server = models.ForeignKey(Server, on_delete=models.SET_NULL, null=True, related_name='accounts')
    inbound_id = models.PositiveIntegerField(_('Inbound ID'))
    email = models.CharField(_('Email/Identifier'), max_length=255)
    protocol = models.CharField(_('Protocol'), max_length=20, default='vless')
    status = models.CharField(_('Status'), max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Account limits
    traffic_limit_bytes = models.BigIntegerField(_('Traffic Limit (bytes)'), default=0)
    upload_bytes = models.BigIntegerField(_('Upload (bytes)'), default=0)
    download_bytes = models.BigIntegerField(_('Download (bytes)'), default=0)
    
    # Time limits
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    expires_at = models.DateTimeField(_('Expires At'), null=True, blank=True)
    last_connection = models.DateTimeField(_('Last Connection'), null=True, blank=True)
    
    # Authentication and connection data
    uuid = models.CharField(_('UUID'), max_length=36, null=True, blank=True)
    subscription_url = models.TextField(_('Subscription URL'), null=True, blank=True)
    qr_code = models.ImageField(_('QR Code'), upload_to='qr_codes/', null=True, blank=True)
    
    # Related payment and plan
    payment = models.ForeignKey('payments.Payment', on_delete=models.SET_NULL, null=True, related_name='vpn_accounts')
    
    # Optional metadata
    metadata = models.JSONField(_('Metadata'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('VPN Account')
        verbose_name_plural = _('VPN Accounts')
        ordering = ['-created_at']
        unique_together = [('inbound_id', 'email')]
    
    def __str__(self):
        return f"{self.email} - {self.user.username}"
    
    @property
    def total_used_bytes(self):
        """Total bytes used"""
        return self.upload_bytes + self.download_bytes
    
    @property
    def traffic_percentage(self):
        """Percentage of traffic used"""
        if self.traffic_limit_bytes > 0:
            return (self.total_used_bytes / self.traffic_limit_bytes) * 100
        return 0
    
    @property
    def remaining_bytes(self):
        """Remaining bytes"""
        remaining = self.traffic_limit_bytes - self.total_used_bytes
        return max(0, remaining)
    
    @property
    def days_left(self):
        """Days left until expiration"""
        if not self.expires_at:
            return None
        
        now = timezone.now()
        if now > self.expires_at:
            return 0
        
        delta = self.expires_at - now
        return delta.days
    
    @property
    def is_active(self):
        """Check if account is active"""
        # Check status
        if self.status != 'active':
            return False
        
        # Check if expired
        if self.expires_at and timezone.now() > self.expires_at:
            return False
        
        # Check if traffic exceeded
        if self.traffic_limit_bytes > 0 and self.total_used_bytes >= self.traffic_limit_bytes:
            return False
        
        return True
    
    def update_status(self):
        """Update account status based on current conditions"""
        if self.status in ['disabled', 'suspended']:
            # Don't change these statuses as they are manually set
            return False
        
        now = timezone.now()
        
        # Check if expired
        if self.expires_at and now > self.expires_at:
            self.status = 'expired'
            self.save()
            return True
        
        # Check if traffic exceeded
        if self.traffic_limit_bytes > 0 and self.total_used_bytes >= self.traffic_limit_bytes:
            self.status = 'traffic_exceeded'
            self.save()
            return True
        
        # If previously expired or traffic exceeded, but now conditions are met
        if self.status in ['expired', 'traffic_exceeded']:
            self.status = 'active'
            self.save()
            return True
        
        return False
    
    def sync_with_panel(self):
        """Sync account data with panel"""
        # This would be implemented to fetch the latest data from the panel
        # and update the account information
        from accounts.services import AccountService
        
        try:
            client_status = AccountService.get_account_status(self.inbound_id, self.email)
            
            if 'error' in client_status:
                logger.error(f"Error syncing account {self.email}: {client_status['error']}")
                return False
            
            # Update traffic information
            self.upload_bytes = client_status.get('upload_bytes', 0)
            self.download_bytes = client_status.get('download_bytes', 0)
            
            # Update expiry information
            if client_status.get('expiry_timestamp'):
                self.expires_at = timezone.datetime.fromtimestamp(
                    client_status.get('expiry_timestamp') / 1000,
                    tz=timezone.get_current_timezone()
                )
            
            # Update subscription URL
            if client_status.get('subscription_link'):
                self.subscription_url = client_status.get('subscription_link')
            
            # Update status based on panel data
            if client_status.get('active'):
                self.status = 'active'
            elif client_status.get('expired'):
                self.status = 'expired'
            elif client_status.get('traffic_exceeded'):
                self.status = 'traffic_exceeded'
            elif not client_status.get('enabled'):
                self.status = 'disabled'
            
            self.save()
            return True
            
        except Exception as e:
            logger.exception(f"Error syncing account {self.email}: {str(e)}")
            return False


class AccountExtension(models.Model):
    """Track account extensions"""
    account = models.ForeignKey(VPNAccount, on_delete=models.CASCADE, related_name='extensions')
    days_added = models.PositiveIntegerField(_('Days Added'))
    traffic_added_bytes = models.BigIntegerField(_('Traffic Added (bytes)'), default=0)
    payment = models.ForeignKey('payments.Payment', on_delete=models.SET_NULL, null=True, related_name='account_extensions')
    
    previous_expiry = models.DateTimeField(_('Previous Expiry Date'), null=True, blank=True)
    new_expiry = models.DateTimeField(_('New Expiry Date'), null=True, blank=True)
    
    previous_traffic_limit = models.BigIntegerField(_('Previous Traffic Limit (bytes)'), default=0)
    new_traffic_limit = models.BigIntegerField(_('New Traffic Limit (bytes)'), default=0)
    
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='created_extensions'
    )
    
    class Meta:
        verbose_name = _('Account Extension')
        verbose_name_plural = _('Account Extensions')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.account.email} - {self.days_added} days - {self.created_at}" 