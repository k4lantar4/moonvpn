"""
Models for VPN module
"""

from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField
import uuid
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _

User = get_user_model()

class Server(models.Model):
    """Model for storing VPN server information"""
    name = models.CharField(_("Server Name"), max_length=100)
    description = models.TextField(_("Description"), blank=True)
    type = models.CharField(_("Server Type"), max_length=50, choices=[
        ('standard', 'Standard'),
        ('premium', 'Premium'),
        ('enterprise', 'Enterprise')
    ], default='standard')
    ip_address = models.GenericIPAddressField(_("IP Address"), null=True, blank=True)
    port = models.IntegerField(_("Port"), validators=[MinValueValidator(1), MaxValueValidator(65535)])
    username = models.CharField(_("Panel Username"), max_length=50)
    password = models.CharField(_("Panel Password"), max_length=50)
    location = models.CharField(_("Location"), max_length=50)
    country = models.CharField(_("Country"), max_length=50)
    country_code = models.CharField(_("Country Code"), max_length=2)
    panel_path = models.CharField(_("Panel Path"), max_length=100, default="/panel")
    is_active = models.BooleanField(_("Is Active"), default=True)
    max_clients = models.IntegerField(_("Maximum Clients"), default=0)  # 0 means unlimited
    bandwidth_limit = models.BigIntegerField(_("Bandwidth Limit (bytes)"), default=0)  # 0 means unlimited
    protocols = ArrayField(
        models.CharField(max_length=20),
        verbose_name=_("Supported Protocols"),
        default=list
    )
    default_protocol = models.CharField(_("Default Protocol"), max_length=20, default='vmess')
    config = models.JSONField(_("Configuration"), default=dict, blank=True)
    status = models.CharField(_("Status"), max_length=20, choices=[
        ('online', 'Online'),
        ('offline', 'Offline'),
        ('maintenance', 'Maintenance')
    ], default='offline')
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("Server")
        verbose_name_plural = _("Servers")
        ordering = ["name"]
    
    def __str__(self):
        return f"{self.name} ({self.location})"
    
    @property
    def panel_url(self):
        """Get full panel URL"""
        protocol = "https" if self.port in [443, 2053, 2083, 2087, 2096] else "http"
        return f"{protocol}://{self.ip_address}:{self.port}{self.panel_path}"
    
    @property
    def host(self):
        """Get server host"""
        return f"{self.ip_address}:{self.port}"
    
    @property
    def url(self):
        """Get server URL"""
        return self.panel_url
    
    @property
    def cpu_usage(self):
        """Get latest CPU usage"""
        latest = self.status_history.order_by('-timestamp').first()
        return latest.cpu_usage if latest else 0
    
    @property
    def memory_usage(self):
        """Get latest memory usage"""
        latest = self.status_history.order_by('-timestamp').first()
        return latest.memory_usage if latest else 0
    
    @property
    def disk_usage(self):
        """Get latest disk usage"""
        latest = self.status_history.order_by('-timestamp').first()
        return latest.disk_usage if latest else 0
    
    @property
    def last_sync(self):
        """Get last sync time"""
        latest = self.status_history.order_by('-timestamp').first()
        return latest.timestamp if latest else None
    
    def get_active_users_count(self):
        """Get count of active clients on this server"""
        return self.client_set.filter(is_active=True).count()
    
    def is_at_capacity(self):
        """Check if server has reached its maximum client capacity"""
        return self.max_clients > 0 and self.get_active_users_count() >= self.max_clients

class ServerStatus(models.Model):
    """Model for storing server status history"""
    server = models.ForeignKey(Server, on_delete=models.CASCADE, related_name="status_history")
    cpu_usage = models.FloatField(_("CPU Usage %"), validators=[MinValueValidator(0), MaxValueValidator(100)])
    memory_usage = models.FloatField(_("Memory Usage %"), validators=[MinValueValidator(0), MaxValueValidator(100)])
    disk_usage = models.FloatField(_("Disk Usage %"), validators=[MinValueValidator(0), MaxValueValidator(100)])
    network_in = models.BigIntegerField(_("Network In (bytes)"))
    network_out = models.BigIntegerField(_("Network Out (bytes)"))
    timestamp = models.DateTimeField(_("Timestamp"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("Server Status")
        verbose_name_plural = _("Server Status History")
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["server", "-timestamp"]),
        ]
    
    def __str__(self):
        return f"{self.server.name} Status at {self.timestamp}"
    
    @property
    def total_network(self):
        """Get total network traffic"""
        return self.network_in + self.network_out
    
    @property
    def network_in_gb(self):
        """Get incoming traffic in GB"""
        return round(self.network_in / (1024 ** 3), 2)
    
    @property
    def network_out_gb(self):
        """Get outgoing traffic in GB"""
        return round(self.network_out / (1024 ** 3), 2)

class Client(models.Model):
    """Model for storing VPN client information"""
    server = models.ForeignKey(Server, on_delete=models.CASCADE)
    email = models.EmailField(_("Email"))
    uuid = models.CharField(_("UUID"), max_length=36)
    traffic_limit = models.BigIntegerField(_("Traffic Limit (bytes)"), default=0)  # 0 means unlimited
    used_traffic = models.BigIntegerField(_("Used Traffic (bytes)"), default=0)
    expire_date = models.DateTimeField(_("Expire Date"), null=True, blank=True)
    is_active = models.BooleanField(_("Is Active"), default=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("Client")
        verbose_name_plural = _("Clients")
        unique_together = [["server", "email"]]
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"{self.email} on {self.server.name}"
    
    @property
    def traffic_limit_gb(self):
        """Get traffic limit in GB"""
        return round(self.traffic_limit / (1024 ** 3), 2) if self.traffic_limit > 0 else 0
    
    @property
    def used_traffic_gb(self):
        """Get used traffic in GB"""
        return round(self.used_traffic / (1024 ** 3), 2)
    
    @property
    def remaining_traffic_gb(self):
        """Get remaining traffic in GB"""
        if self.traffic_limit == 0:
            return float("inf")
        return max(0, self.traffic_limit_gb - self.used_traffic_gb)
    
    def has_expired(self):
        """Check if client has expired"""
        return self.expire_date and self.expire_date < timezone.now()
    
    def has_traffic_left(self):
        """Check if client has remaining traffic"""
        return self.traffic_limit == 0 or self.used_traffic < self.traffic_limit

class ServerMetrics(models.Model):
    """Server metrics history"""
    
    server = models.ForeignKey(
        Server,
        on_delete=models.CASCADE,
        related_name='metrics'
    )
    
    # Metrics
    cpu_usage = models.FloatField()
    memory_usage = models.FloatField()
    disk_usage = models.FloatField()
    active_users = models.IntegerField()
    total_traffic = models.BigIntegerField(help_text="Total traffic in bytes")
    
    # Timestamp
    timestamp = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Server Metrics'
        verbose_name_plural = 'Server Metrics'
        indexes = [
            models.Index(fields=['server', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.server.name} metrics at {self.timestamp}"

class Plan(models.Model):
    """Model for storing VPN service plans"""
    
    DURATION_CHOICES = [
        ('daily', _('Daily')),
        ('weekly', _('Weekly')),
        ('monthly', _('Monthly')),
        ('quarterly', _('Quarterly')),
        ('semi_annual', _('Semi-Annual')),
        ('annual', _('Annual')),
        ('custom', _('Custom')),
    ]
    
    STATUS_CHOICES = [
        ('active', _('Active')),
        ('disabled', _('Disabled')),
        ('archived', _('Archived')),
    ]
    
    name = models.CharField(_("Plan Name"), max_length=100)
    description = models.TextField(_("Description"), blank=True)
    duration_type = models.CharField(_("Duration Type"), max_length=20, choices=DURATION_CHOICES)
    duration_days = models.IntegerField(_("Duration in Days"))
    traffic_limit = models.BigIntegerField(_("Traffic Limit (bytes)"), default=0)  # 0 means unlimited
    price = models.DecimalField(_("Price"), max_digits=10, decimal_places=2)
    max_connections = models.IntegerField(_("Max Connections"), default=1)
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='active')
    features = ArrayField(
        models.CharField(max_length=100),
        verbose_name=_("Features"),
        default=list,
        blank=True
    )
    servers = models.ManyToManyField(
        Server,
        verbose_name=_("Available Servers"),
        related_name='available_plans',
        blank=True
    )
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("Plan")
        verbose_name_plural = _("Plans")
        ordering = ["price", "name"]
    
    def __str__(self):
        return f"{self.name} ({self.get_duration_type_display()})"
    
    @property
    def traffic_limit_gb(self):
        """Get traffic limit in GB"""
        return round(self.traffic_limit / (1024 ** 3), 2) if self.traffic_limit > 0 else 0
    
    def is_available(self):
        """Check if plan is available for purchase"""
        return self.status == 'active' and self.servers.filter(is_active=True).exists()

class Subscription(models.Model):
    """Model for storing client subscriptions"""
    
    STATUS_CHOICES = [
        ('active', _('Active')),
        ('expired', _('Expired')),
        ('cancelled', _('Cancelled')),
        ('suspended', _('Suspended')),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name=_("User")
    )
    plan = models.ForeignKey(
        Plan,
        on_delete=models.PROTECT,
        related_name='subscriptions',
        verbose_name=_("Plan")
    )
    client = models.OneToOneField(
        Client,
        on_delete=models.CASCADE,
        related_name='subscription',
        verbose_name=_("VPN Client")
    )
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='active')
    start_date = models.DateTimeField(_("Start Date"), default=timezone.now)
    end_date = models.DateTimeField(_("End Date"))
    last_renewal = models.DateTimeField(_("Last Renewal"), null=True, blank=True)
    auto_renew = models.BooleanField(_("Auto Renew"), default=False)
    notes = models.TextField(_("Notes"), blank=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("Subscription")
        verbose_name_plural = _("Subscriptions")
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"{self.user.email} - {self.plan.name}"
    
    def is_active(self):
        """Check if subscription is active"""
        return (
            self.status == 'active' and
            self.end_date > timezone.now() and
            self.client.is_active and
            not self.client.has_expired() and
            self.client.has_traffic_left()
        )
    
    def days_remaining(self):
        """Get number of days remaining in subscription"""
        if self.end_date < timezone.now():
            return 0
        return (self.end_date - timezone.now()).days
    
    def can_renew(self):
        """Check if subscription can be renewed"""
        return (
            self.status in ['active', 'expired'] and
            self.plan.is_available()
        )

class Transaction(models.Model):
    """Model for storing subscription transactions"""
    
    TYPE_CHOICES = [
        ('new', _('New Subscription')),
        ('renewal', _('Renewal')),
        ('upgrade', _('Plan Upgrade')),
        ('refund', _('Refund')),
    ]
    
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('completed', _('Completed')),
        ('failed', _('Failed')),
        ('refunded', _('Refunded')),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='vpn_transactions',
        verbose_name=_("User")
    )
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.SET_NULL,
        null=True,
        related_name='transactions',
        verbose_name=_("Subscription")
    )
    transaction_type = models.CharField(_("Type"), max_length=20, choices=TYPE_CHOICES)
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='pending')
    amount = models.DecimalField(_("Amount"), max_digits=10, decimal_places=2)
    payment_method = models.CharField(_("Payment Method"), max_length=50)
    payment_id = models.CharField(_("Payment ID"), max_length=100, blank=True)
    notes = models.TextField(_("Notes"), blank=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("Transaction")
        verbose_name_plural = _("Transactions")
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"{self.user.email} - {self.get_transaction_type_display()} - {self.amount}" 