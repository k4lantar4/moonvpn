from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
import uuid
import json
from django.utils import timezone
from django.conf import settings
import secrets
from .permissions import Permission, PermissionGroup, get_role_permissions
from encrypted_model_fields.fields import EncryptedCharField
from django.core.validators import MinValueValidator, MaxValueValidator

# Create your models here.

class Role(models.Model):
    """Model for user roles and permissions."""
    ROLE_CHOICES = (
        ('admin', _('Administrator')),
        ('seller', _('Seller')),
        ('vip', _('VIP Customer')),
        ('user', _('Regular User')),
    )
    
    name = models.CharField(max_length=20, choices=ROLE_CHOICES, unique=True)
    description = models.TextField(blank=True)
    permissions = models.JSONField(default=list)
    is_custom = models.BooleanField(default=False)
    priority = models.IntegerField(default=0)
    max_users = models.IntegerField(null=True, blank=True)
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = 'main'
        ordering = ['-priority', 'name']
        verbose_name = _('Role')
        verbose_name_plural = _('Roles')
    
    def __str__(self):
        return self.get_name_display()
    
    def save(self, *args, **kwargs):
        if not self.permissions:
            self.permissions = get_role_permissions(self.name)
        super().save(*args, **kwargs)
    
    def has_permission(self, permission: Permission) -> bool:
        """Check if role has a specific permission."""
        return permission in self.permissions
    
    def has_group_permissions(self, group: PermissionGroup) -> bool:
        """Check if role has all permissions in a group."""
        group_permissions = get_role_permissions(self.name)
        return all(p in self.permissions for p in group_permissions)

class User(AbstractUser):
    """Extended user model with role-based access and VPN-specific fields."""
    
    # Basic user information
    telegram_id = models.BigIntegerField(null=True, blank=True, unique=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    language_code = models.CharField(max_length=10, default='fa')
    
    # Role and permissions
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)
    is_admin = models.BooleanField(default=False)
    
    # Financial information
    wallet_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    total_sales = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Referral system
    referral_code = models.CharField(max_length=20, unique=True, blank=True)
    referred_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    
    # VPN-specific fields
    traffic_limit = models.BigIntegerField(default=0, help_text=_('Traffic limit in bytes'))
    traffic_used = models.BigIntegerField(default=0, help_text=_('Traffic used in bytes'))
    subscription_expires = models.DateTimeField(null=True, blank=True)
    
    # Points system
    points = models.IntegerField(default=0, help_text=_('User points balance'))
    
    # Security and preferences
    api_key = EncryptedCharField(max_length=64, null=True, blank=True)
    two_factor_enabled = models.BooleanField(default=False)
    notification_preferences = models.JSONField(default=dict)
    
    # User settings
    notifications_enabled = models.BooleanField(default=True, help_text=_('Enable/disable notifications'))
    language = models.CharField(max_length=10, default='fa', help_text=_('User interface language'))
    theme = models.CharField(max_length=20, default='light', help_text=_('User interface theme'))
    timezone = models.CharField(max_length=50, default='Asia/Tehran', help_text=_('User timezone'))
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        app_label = 'main'
        verbose_name = _('User')
        verbose_name_plural = _('Users')
    
    def __str__(self):
        return self.username
    
    def save(self, *args, **kwargs):
        if not self.referral_code:
            self.referral_code = secrets.token_hex(10)
        super().save(*args, **kwargs)
    
    def add_points(self, points: int, description: str = '') -> None:
        """Add points to user balance."""
        self.points += points
        self.save()
        
        # Create points transaction
        from points.models import PointsTransaction
        PointsTransaction.objects.create(
            user=self,
            type='earn',
            points=points,
            description=description
        )
    
    def get_permissions(self) -> list:
        """Get all user permissions."""
        if self.is_admin:
            return [p for group in PermissionGroup for p in get_role_permissions(group)]
        if not self.role:
            return []
        return self.role.permissions
    
    def has_active_subscription(self) -> bool:
        """Check if user has an active subscription."""
        if not self.subscription_expires:
            return False
        return timezone.now() < self.subscription_expires
    
    def get_traffic_usage_percent(self) -> float:
        """Get traffic usage as a percentage."""
        if self.traffic_limit == 0:
            return 0
        return (self.traffic_used / self.traffic_limit) * 100
    
    def can_use_traffic(self) -> bool:
        """Check if user can use more traffic."""
        return self.has_active_subscription() and (self.traffic_limit == 0 or self.traffic_used < self.traffic_limit)

class Server(models.Model):
    """Model for V2Ray servers with synchronization support."""
    
    name = models.CharField(max_length=100)
    host = models.CharField(max_length=255)
    port = models.IntegerField()
    # Add panel credentials and related fields
    url = models.CharField(max_length=255, blank=True, null=True, help_text="Full URL of the 3x-UI panel (e.g., https://panel.example.com:2053)")
    username = models.CharField(max_length=100, blank=True, null=True, help_text="Admin username for the 3x-UI panel")
    password = models.CharField(max_length=100, blank=True, null=True, help_text="Admin password for the 3x-UI panel")
    location = models.CharField(max_length=100, default="Unknown", help_text="Geographic location of the server")
    country_code = models.CharField(max_length=2, blank=True, null=True, help_text="Two-letter country code (e.g., IR, US)")
    type = models.CharField(max_length=20, default="v2ray", choices=[("v2ray", "V2Ray"), ("xray", "XRay")], help_text="Server type")
    cpu_usage = models.FloatField(default=0, help_text="Current CPU usage percentage")
    memory_usage = models.FloatField(default=0, help_text="Current memory usage percentage")
    disk_usage = models.FloatField(default=0, help_text="Current disk usage percentage")
    protocol = models.CharField(max_length=20, default='vmess')
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    sync_id = models.CharField(max_length=50, unique=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_synced = models.BooleanField(default=False)
    last_sync = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.host})"
    
    def save(self, *args, **kwargs):
        if not self.sync_id:
            self.sync_id = f"server_{uuid.uuid4().hex[:8]}"
        super().save(*args, **kwargs)
    
    def generate_remark(self, user: User) -> str:
        """Generate unique remark for user subscription."""
        return f"MoonVpn-{self.name}-{user.id}-{uuid.uuid4().hex[:4]}"
    
    class Meta:
        app_label = 'main'

class SubscriptionPlan(models.Model):
    """Model for subscription plans"""
    TYPE_CHOICES = (
        ('data', _('Data Based')),
        ('time', _('Time Based')),
        ('both', _('Data & Time Based')),
    )
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='both')
    data_limit_gb = models.PositiveIntegerField(default=0, help_text="Data limit in GB (0 means unlimited)")
    duration_days = models.PositiveIntegerField(default=30, help_text="Duration in days")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        app_label = 'main'


class Subscription(models.Model):
    """Model for user subscriptions"""
    STATUS_CHOICES = (
        ('active', _('Active')),
        ('expired', _('Expired')),
        ('suspended', _('Suspended')),
        ('cancelled', _('Cancelled')),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='v2ray_subscriptions')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    server = models.ForeignKey(Server, on_delete=models.CASCADE)
    # Store the inbound ID and client email from 3x-UI
    inbound_id = models.PositiveIntegerField(null=True, blank=True)
    client_email = models.EmailField(null=True, blank=True)
    # Store the full client config as JSON
    client_config = models.JSONField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    data_usage_gb = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    data_limit_gb = models.PositiveIntegerField(default=0)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.plan.name}"
    
    def is_expired(self):
        return timezone.now() > self.end_date
    
    def remaining_days(self):
        if self.is_expired():
            return 0
        delta = self.end_date - timezone.now()
        return max(0, delta.days)
    
    def data_usage_percentage(self):
        if self.data_limit_gb == 0:  # Unlimited
            return 0
        return min(100, (self.data_usage_gb / self.data_limit_gb) * 100)
    
    class Meta:
        app_label = 'main'


class Payment(models.Model):
    """Model for payments"""
    PAYMENT_TYPES = (
        ('card', _('Card to Card')),
        ('zarinpal', _('Zarinpal')),
        ('wallet', _('Wallet')),
        ('admin', _('Admin')),
    )
    
    STATUS_CHOICES = (
        ('pending', _('Pending')),
        ('completed', _('Completed')),
        ('failed', _('Failed')),
        ('expired', _('Expired')),
        ('refunded', _('Refunded')),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='v2ray_payments')
    subscription = models.ForeignKey(Subscription, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    type = models.CharField(max_length=20, choices=PAYMENT_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    transaction_data = models.JSONField(null=True, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.amount} - {self.type}"
    
    class Meta:
        app_label = 'main'


class CardPayment(models.Model):
    """Model for card to card payments"""
    STATUS_CHOICES = (
        ('pending', _('Pending')),
        ('verified', _('Verified')),
        ('rejected', _('Rejected')),
        ('expired', _('Expired')),
    )
    
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name='card_payment')
    card_number = models.CharField(max_length=20)
    reference_number = models.CharField(max_length=100)
    transfer_time = models.DateTimeField()
    verification_code = models.CharField(max_length=10, unique=True)
    expires_at = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_note = models.TextField(blank=True)
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='v2ray_verified_payments')
    verified_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.payment.user.username} - {self.verification_code}"
    
    def save(self, *args, **kwargs):
        if not self.verification_code:
            self.verification_code = secrets.token_hex(5)[:10]
        super().save(*args, **kwargs)
    
    class Meta:
        app_label = 'main'


class ZarinpalPayment(models.Model):
    """Model for Zarinpal payments"""
    STATUS_CHOICES = (
        ('pending', _('Pending')),
        ('verified', _('Verified')),
        ('failed', _('Failed')),
    )
    
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name='zarinpal_payment')
    authority = models.CharField(max_length=100, blank=True, null=True)
    ref_id = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    def __str__(self):
        return f"{self.payment.user.username} - {self.authority}"
    
    class Meta:
        app_label = 'main'


class Discount(models.Model):
    """Model for discount codes"""
    TYPE_CHOICES = (
        ('percentage', _('Percentage')),
        ('fixed', _('Fixed Amount')),
    )
    
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='percentage')
    value = models.DecimalField(max_digits=10, decimal_places=2)
    valid_from = models.DateTimeField(default=timezone.now)
    valid_until = models.DateTimeField(null=True, blank=True)
    max_uses = models.PositiveIntegerField(default=0, help_text="0 means unlimited")
    times_used = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.code
    
    def is_valid(self):
        if not self.is_active:
            return False
        
        now = timezone.now()
        if now < self.valid_from:
            return False
        
        if self.valid_until and now > self.valid_until:
            return False
        
        if self.max_uses > 0 and self.times_used >= self.max_uses:
            return False
        
        return True
    
    class Meta:
        app_label = 'main'


class TelegramMessage(models.Model):
    """Model for storing Telegram message templates"""
    name = models.CharField(max_length=100)
    content = models.TextField()
    language_code = models.CharField(max_length=10, default='fa')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.language_code})"
    
    class Meta:
        app_label = 'main'


class ServerMonitor(models.Model):
    """Model for server monitoring data"""
    HEALTH_STATUS = (
        ('healthy', _('Healthy')),
        ('warning', _('Warning')),
        ('critical', _('Critical')),
        ('offline', _('Offline')),
    )
    
    server = models.ForeignKey(Server, on_delete=models.CASCADE, related_name='monitoring_data')
    health_status = models.CharField(max_length=20, choices=HEALTH_STATUS, default='healthy')
    cpu_usage = models.FloatField(null=True, blank=True)
    memory_usage = models.FloatField(null=True, blank=True)
    disk_usage = models.FloatField(null=True, blank=True)
    uptime_seconds = models.PositiveIntegerField(null=True, blank=True)
    active_connections = models.PositiveIntegerField(null=True, blank=True)
    network_in = models.BigIntegerField(null=True, blank=True, help_text="Network input in bytes")
    network_out = models.BigIntegerField(null=True, blank=True, help_text="Network output in bytes")
    network_speed_in = models.FloatField(null=True, blank=True, help_text="Network input speed in bytes/s")
    network_speed_out = models.FloatField(null=True, blank=True, help_text="Network output speed in bytes/s")
    load_average_1min = models.FloatField(null=True, blank=True)
    load_average_5min = models.FloatField(null=True, blank=True)
    load_average_15min = models.FloatField(null=True, blank=True)
    swap_usage = models.FloatField(null=True, blank=True)
    io_read = models.BigIntegerField(null=True, blank=True, help_text="Disk read in bytes")
    io_write = models.BigIntegerField(null=True, blank=True, help_text="Disk write in bytes")
    io_speed_read = models.FloatField(null=True, blank=True, help_text="Disk read speed in bytes/s")
    io_speed_write = models.FloatField(null=True, blank=True, help_text="Disk write speed in bytes/s")
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.server.name} - {self.health_status} - {self.timestamp}"
    
    def calculate_health_status(self) -> str:
        """Calculate server health status based on metrics."""
        if not all([self.cpu_usage, self.memory_usage, self.disk_usage]):
            return 'offline'
        
        # Check critical conditions
        if (
            self.cpu_usage > 95 or
            self.memory_usage > 95 or
            self.disk_usage > 95 or
            self.load_average_1min > 10 or
            self.active_connections > 1000
        ):
            return 'critical'
        
        # Check warning conditions
        if (
            self.cpu_usage > 80 or
            self.memory_usage > 80 or
            self.disk_usage > 80 or
            self.load_average_1min > 5 or
            self.active_connections > 500
        ):
            return 'warning'
        
        return 'healthy'
    
    def get_network_usage_gb(self) -> float:
        """Get total network usage in GB."""
        if not all([self.network_in, self.network_out]):
            return 0
        return round((self.network_in + self.network_out) / (1024 * 1024 * 1024), 2)
    
    def get_network_speed_mbps(self) -> tuple[float, float]:
        """Get network speed in Mbps."""
        if not all([self.network_speed_in, self.network_speed_out]):
            return 0, 0
        return (
            round(self.network_speed_in * 8 / (1024 * 1024), 2),
            round(self.network_speed_out * 8 / (1024 * 1024), 2)
        )
    
    def get_io_speed_mbps(self) -> tuple[float, float]:
        """Get disk I/O speed in MB/s."""
        if not all([self.io_speed_read, self.io_speed_write]):
            return 0, 0
        return (
            round(self.io_speed_read / (1024 * 1024), 2),
            round(self.io_speed_write / (1024 * 1024), 2)
        )
    
    def get_uptime_days(self) -> float:
        """Get server uptime in days."""
        if not self.uptime_seconds:
            return 0
        return round(self.uptime_seconds / (24 * 60 * 60), 2)
    
    class Meta:
        app_label = 'main'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['server', 'timestamp']),
            models.Index(fields=['health_status']),
        ]


class APIKey(models.Model):
    """Model for API keys used for external services"""
    name = models.CharField(max_length=100)
    key = models.CharField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.key:
            self.key = secrets.token_hex(32)
        super().save(*args, **kwargs)
    
    def is_valid(self):
        if not self.is_active:
            return False
        
        if self.expires_at and timezone.now() > self.expires_at:
            return False
        
        return True
    
    class Meta:
        app_label = 'main'

class UserUsagePattern(models.Model):
    """Model for tracking user's usage patterns."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='usage_pattern')
    average_daily_usage_gb = models.FloatField(default=0)
    peak_hours = models.JSONField(default=list)  # List of hours with highest usage
    preferred_protocols = models.JSONField(default=list)  # List of preferred protocols
    last_updated = models.DateTimeField(auto_now=True)

    def update_patterns(self, usage_data):
        """Update usage patterns based on new data."""
        self.average_daily_usage_gb = usage_data.get('average_daily_usage_gb', 0)
        self.peak_hours = usage_data.get('peak_hours', [])
        self.preferred_protocols = usage_data.get('preferred_protocols', [])
        self.save()
    
    class Meta:
        app_label = 'main'

class PlanSuggestion(models.Model):
    """Model for plan suggestions."""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    duration_days = models.IntegerField(blank=True, null=True)
    traffic_gb = models.IntegerField(blank=True, null=True)
    is_accepted = models.BooleanField(default=False)
    accepted_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'main'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} by {self.user.username}"

    def accept(self):
        """Mark suggestion as accepted."""
        self.is_accepted = True
        self.accepted_at = timezone.now()
        self.save()

class AllowedGroup(models.Model):
    """Model for storing Telegram groups where the bot is allowed to operate."""
    group_id = models.BigIntegerField(unique=True, help_text=_('Telegram group/chat ID'))
    title = models.CharField(max_length=255, help_text=_('Group/chat title'))
    username = models.CharField(max_length=255, blank=True, null=True, help_text=_('Group username if available'))
    invite_link = models.CharField(max_length=255, blank=True, null=True, help_text=_('Group invite link if available'))
    members_count = models.IntegerField(default=0, help_text=_('Number of members in the group'))
    added_by = models.BigIntegerField(help_text=_('Telegram ID of the admin who added this group'))
    is_active = models.BooleanField(default=True, help_text=_('Whether the bot is active in this group'))
    joined_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} ({self.group_id})"
    
    class Meta:
        app_label = 'main'
        verbose_name = _('Allowed Group')
        verbose_name_plural = _('Allowed Groups')

class BotManagementGroup(models.Model):
    """Model for storing special management groups used by the bot for different purposes."""
    
    GROUP_TYPES = (
        ('MANAGE', _('Main Management')),
        ('REPORTS', _('System Reports')),
        ('LOGS', _('User Logs')),
        ('TRANSACTIONS', _('Payment Transactions')),
        ('OUTAGES', _('Service Outages')),
        ('SELLERS', _('Resellers')),
        ('BACKUPS', _('Backups')),
        ('OTHER', _('Other')),
    )
    
    group_type = models.CharField(max_length=20, choices=GROUP_TYPES, unique=True, 
                                help_text=_('Type of management group'))
    group = models.ForeignKey(AllowedGroup, on_delete=models.CASCADE, related_name='management_functions',
                            help_text=_('The allowed group serving this management function'))
    description = models.TextField(blank=True, help_text=_('Description of this management group purpose'))
    icon = models.CharField(max_length=10, default='📊', help_text=_('Emoji icon for this group type'))
    notification_level = models.CharField(max_length=20, default='NORMAL', 
                                        choices=[('LOW', _('Low')), ('NORMAL', _('Normal')), ('HIGH', _('High'))],
                                        help_text=_('Notification importance level for this group'))
    is_active = models.BooleanField(default=True, help_text=_('Whether notifications to this group are active'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.get_group_type_display()} ({self.group.title})"
    
    class Meta:
        app_label = 'main'
        verbose_name = _('Bot Management Group')
        verbose_name_plural = _('Bot Management Groups')
        ordering = ['group_type']

class UserActivity(models.Model):
    """Model for tracking user activities."""
    
    ACTIVITY_TYPES = (
        ('login', _('Login')),
        ('logout', _('Logout')),
        ('profile_update', _('Profile Update')),
        ('password_change', _('Password Change')),
        ('subscription_purchase', _('Subscription Purchase')),
        ('subscription_renewal', _('Subscription Renewal')),
        ('payment', _('Payment')),
        ('vpn_usage', _('VPN Usage')),
        ('other', _('Other')),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=50, choices=ACTIVITY_TYPES)
    description = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.get_activity_type_display()} - {self.created_at}"
    
    class Meta:
        app_label = 'main'
        verbose_name = _('User Activity')
        verbose_name_plural = _('User Activities')
        ordering = ['-created_at']

class Wallet(models.Model):
    """Model for user wallets."""
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default='IRR')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s Wallet"
    
    class Meta:
        app_label = 'main'
        verbose_name = _('Wallet')
        verbose_name_plural = _('Wallets')

class Transaction(models.Model):
    """Model for wallet transactions."""
    
    TYPE_CHOICES = (
        ('deposit', _('Deposit')),
        ('withdrawal', _('Withdrawal')),
        ('subscription', _('Subscription')),
        ('refund', _('Refund')),
        ('commission', _('Commission')),
        ('other', _('Other')),
    )
    
    STATUS_CHOICES = (
        ('pending', _('Pending')),
        ('completed', _('Completed')),
        ('failed', _('Failed')),
        ('cancelled', _('Cancelled')),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wallet_transactions')
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    description = models.TextField(blank=True)
    reference_id = models.CharField(max_length=100, blank=True)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.get_type_display()} - {self.amount}"
    
    class Meta:
        app_label = 'main'
        verbose_name = _('Transaction')
        verbose_name_plural = _('Transactions')
        ordering = ['-created_at']

class Order(models.Model):
    """Model for subscription orders."""
    
    STATUS_CHOICES = (
        ('pending', _('Pending')),
        ('paid', _('Paid')),
        ('failed', _('Failed')),
        ('cancelled', _('Cancelled')),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    subscription_plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=50)
    payment_id = models.CharField(max_length=100, blank=True)
    voucher = models.ForeignKey('Voucher', on_delete=models.SET_NULL, null=True, blank=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.subscription_plan.name} - {self.amount}"
    
    class Meta:
        app_label = 'main'
        verbose_name = _('Order')
        verbose_name_plural = _('Orders')
        ordering = ['-created_at']

class Voucher(models.Model):
    """Model for discount vouchers."""
    
    TYPE_CHOICES = (
        ('fixed', _('Fixed Amount')),
        ('percentage', _('Percentage')),
    )
    
    code = models.CharField(max_length=20, unique=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='percentage')
    value = models.DecimalField(max_digits=10, decimal_places=2)
    max_uses = models.IntegerField(default=0)
    used_count = models.IntegerField(default=0)
    min_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    max_discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.code} - {self.get_type_display()} - {self.value}"
    
    class Meta:
        app_label = 'main'
        verbose_name = _('Voucher')
        verbose_name_plural = _('Vouchers')
        ordering = ['-created_at']
    
    def is_valid(self, order_amount: float = None) -> bool:
        """Check if voucher is valid."""
        now = timezone.now()
        
        # Check if voucher is active
        if not self.is_active:
            return False
        
        # Check if voucher has expired
        if self.end_date and now > self.end_date:
            return False
        
        # Check if voucher has started
        if now < self.start_date:
            return False
        
        # Check if voucher has reached max uses
        if self.max_uses > 0 and self.used_count >= self.max_uses:
            return False
        
        # Check minimum order amount
        if order_amount is not None and order_amount < self.min_order_amount:
            return False
        
        return True
    
    def calculate_discount(self, order_amount: float) -> float:
        """Calculate discount amount."""
        if not self.is_valid(order_amount):
            return 0
        
        if self.type == 'fixed':
            discount = min(self.value, order_amount)
        else:  # percentage
            discount = order_amount * (self.value / 100)
        
        # Apply maximum discount limit
        if self.max_discount_amount > 0:
            discount = min(discount, self.max_discount_amount)
        
        return discount

class PanelConfig(models.Model):
    """Model for managing 3x-UI panel configurations."""
    
    name = models.CharField(max_length=100, help_text="Panel name for identification")
    server_id = models.IntegerField(unique=True, help_text="Unique server ID")
    domain = models.CharField(max_length=255, help_text="Panel domain or IP address")
    port = models.IntegerField(help_text="Panel port number")
    username = EncryptedCharField(max_length=100, help_text="Panel admin username")
    password = EncryptedCharField(max_length=100, help_text="Panel admin password")
    location = models.CharField(max_length=2, help_text="Two-letter country code (e.g., DE)")
    base_path = models.CharField(max_length=100, help_text="Panel base path")
    api_path = models.CharField(max_length=100, default='/panel/api', help_text="Panel API path")
    use_ssl = models.BooleanField(default=False, help_text="Whether to use HTTPS")
    disable_check = models.BooleanField(default=False, help_text="Disable panel connectivity check")
    is_active = models.BooleanField(default=True, help_text="Whether this panel is active")
    last_check = models.DateTimeField(null=True, blank=True, help_text="Last successful connectivity check")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Panel Configuration"
        verbose_name_plural = "Panel Configurations"
        ordering = ['server_id']
    
    def __str__(self):
        return f"{self.name} ({self.domain}:{self.port})"
    
    @property
    def panel_url(self):
        """Get full panel URL."""
        scheme = 'https' if self.use_ssl else 'http'
        return f"{scheme}://{self.domain}:{self.port}/{self.base_path}"
    
    @property
    def api_url(self):
        """Get full API URL."""
        scheme = 'https' if self.use_ssl else 'http'
        return f"{scheme}://{self.domain}:{self.port}{self.api_path}"
    
    def save(self, *args, **kwargs):
        """Override save to ensure base_path doesn't start with /."""
        if self.base_path.startswith('/'):
            self.base_path = self.base_path[1:]
        super().save(*args, **kwargs)
