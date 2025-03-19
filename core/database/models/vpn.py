"""
VPN-related models for MoonVPN.
Defines VPN accounts, servers, locations, and traffic logging.
"""

from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField
import uuid
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, BigInteger, JSON, Enum
from sqlalchemy.orm import relationship
import enum

User = get_user_model()

class ServerStatus(enum.Enum):
    """VPN server status."""
    ACTIVE = "active"
    MAINTENANCE = "maintenance"
    OFFLINE = "offline"
    OVERLOADED = "overloaded"

class VPNAccountStatus(enum.Enum):
    """VPN account status."""
    ACTIVE = "active"
    EXPIRED = "expired"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"

class Location(models.Model):
    """
    VPN server location model.
    Represents a geographical location where VPN servers are available.
    """
    
    name = models.CharField(max_length=100, null=False)
    country_code = models.CharField(max_length=2, null=False)
    city = models.CharField(max_length=100, null=True)
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(default=0)
    description = models.TextField(max_length=500, null=True)
    
    # Relationships
    servers = relationship("Server", back_populates="location", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Location(name='{self.name}', country='{self.country_code}')>"

class Server(models.Model):
    """
    VPN server model.
    Represents a physical or virtual VPN server instance.
    """
    
    name = models.CharField(max_length=100, null=False)
    host = models.CharField(max_length=255, null=False)
    port = models.IntegerField(null=False)
    status = models.CharField(max_length=20, choices=[
        ('active', 'Active'),
        ('maintenance', 'Maintenance'),
        ('offline', 'Offline'),
        ('overloaded', 'Overloaded')
    ], default='active', null=False)
    is_active = models.BooleanField(default=True)
    max_users = models.IntegerField(null=False)
    current_users = models.IntegerField(default=0)
    bandwidth_limit = models.BigIntegerField(null=True)  # in bytes
    panel_url = models.CharField(max_length=255, null=False)
    panel_username = models.CharField(max_length=100, null=False)
    panel_password = models.CharField(max_length=255, null=False)
    panel_cookie = models.CharField(max_length=1000, null=True)
    last_sync = models.DateTimeField(null=True)
    config = models.JSONField(null=True)
    
    # Relationships
    location_id = models.IntegerField(ForeignKey("location.id"), null=False)
    location = relationship("Location", back_populates="servers")
    vpn_accounts = relationship("VPNAccount", back_populates="server", cascade="all, delete-orphan")
    traffic_logs = relationship("TrafficLog", back_populates="server", cascade="all, delete-orphan")
    
    def update_status(self, status: ServerStatus) -> None:
        """Update server status and related fields."""
        self.status = status.value
        self.is_active = status == ServerStatus.ACTIVE
    
    def update_user_count(self, count: int) -> None:
        """Update current user count."""
        self.current_users = count
        if count >= self.max_users:
            self.status = ServerStatus.OVERLOADED.value
            self.is_active = False
    
    def sync_panel(self) -> None:
        """Update last sync time."""
        self.last_sync = datetime.utcnow()

class VPNAccount(models.Model):
    """
    VPN account model.
    Represents a user's VPN account with configuration and status.
    """
    
    username = models.CharField(max_length=100, unique=True, null=False)
    password = models.CharField(max_length=100, null=False)
    status = models.CharField(max_length=20, choices=[
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('suspended', 'Suspended'),
        ('cancelled', 'Cancelled')
    ], default='active', null=False)
    is_active = models.BooleanField(default=True)
    traffic_limit = models.BigIntegerField(null=True)  # in bytes
    upload_traffic = models.BigIntegerField(default=0)  # in bytes
    download_traffic = models.BigIntegerField(default=0)  # in bytes
    last_connection = models.DateTimeField(null=True)
    config = models.JSONField(null=True)
    
    # Relationships
    user_id = models.IntegerField(ForeignKey("user.id"), null=False)
    user = relationship("User", back_populates="vpn_accounts")
    server_id = models.IntegerField(ForeignKey("server.id"), null=False)
    server = relationship("Server", back_populates="vpn_accounts")
    traffic_logs = relationship("TrafficLog", back_populates="vpn_account", cascade="all, delete-orphan")
    
    def update_status(self, status: VPNAccountStatus) -> None:
        """Update account status and related fields."""
        self.status = status.value
        self.is_active = status == VPNAccountStatus.ACTIVE
    
    def update_traffic(self, upload: int, download: int) -> None:
        """Update traffic usage."""
        self.upload_traffic += upload
        self.download_traffic += download
    
    def has_traffic_limit(self) -> bool:
        """Check if account has traffic limit."""
        return self.traffic_limit is not None
    
    def has_exceeded_traffic_limit(self) -> bool:
        """Check if account has exceeded traffic limit."""
        if not self.has_traffic_limit():
            return False
        return (self.upload_traffic + self.download_traffic) >= self.traffic_limit

class TrafficLog(models.Model):
    """
    Traffic logging model.
    Records VPN traffic usage for accounts and servers.
    """
    
    upload_traffic = models.BigIntegerField(null=False)  # in bytes
    download_traffic = models.BigIntegerField(null=False)  # in bytes
    timestamp = models.DateTimeField(null=False)
    
    # Relationships
    vpn_account_id = models.IntegerField(ForeignKey("vpaccount.id"), null=False)
    vpn_account = relationship("VPNAccount", back_populates="traffic_logs")
    server_id = models.IntegerField(ForeignKey("server.id"), null=False)
    server = relationship("Server", back_populates="traffic_logs")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.timestamp:
            self.timestamp = datetime.utcnow()

class ServerStatusHistory(models.Model):
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