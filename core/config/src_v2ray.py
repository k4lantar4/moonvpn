"""
Models for V2Ray management system.
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import uuid
from main.models import Server, User
from django.core.validators import MinValueValidator, MaxValueValidator

# Create your models here.

class Inbound(models.Model):
    """Model for V2Ray inbounds."""
    server = models.ForeignKey(Server, on_delete=models.CASCADE, related_name='v2ray_inbounds')
    port = models.PositiveIntegerField()
    protocol = models.CharField(max_length=20)
    settings = models.JSONField()
    stream_settings = models.JSONField()
    remark = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = 'v2ray'
        unique_together = ['server', 'port']
        ordering = ['port']
    
    def __str__(self):
        return f"{self.server.name} - {self.protocol}:{self.port}"

class Client(models.Model):
    """Model for V2Ray clients."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='v2ray_clients')
    inbound = models.ForeignKey(Inbound, on_delete=models.CASCADE, related_name='v2ray_clients')
    email = models.EmailField()
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    flow = models.CharField(max_length=50, blank=True)
    total_gb = models.PositiveIntegerField(default=0)
    expire_days = models.PositiveIntegerField(default=0)
    enable = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = 'v2ray'
        unique_together = ['inbound', 'email']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.email}"
    
    def is_expired(self):
        if self.expire_days == 0:
            return False
        return timezone.now() > (self.created_at + timezone.timedelta(days=self.expire_days))
    
    def remaining_days(self):
        if self.expire_days == 0:
            return 0
        delta = (self.created_at + timezone.timedelta(days=self.expire_days)) - timezone.now()
        return max(0, delta.days)

class ServerMetrics(models.Model):
    """Model for server performance metrics."""
    server = models.ForeignKey(Server, on_delete=models.CASCADE, related_name='v2ray_metrics')
    cpu_usage = models.FloatField()
    memory_usage = models.FloatField()
    disk_usage = models.FloatField()
    network_in = models.BigIntegerField()
    network_out = models.BigIntegerField()
    active_connections = models.PositiveIntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        app_label = 'v2ray'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['server', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.server.name} - {self.timestamp}"

class ServerHealthCheck(models.Model):
    """Model for server health check results."""
    STATUS_CHOICES = (
        ('healthy', _('Healthy')),
        ('warning', _('Warning')),
        ('critical', _('Critical')),
        ('offline', _('Offline')),
    )
    
    server = models.ForeignKey(Server, on_delete=models.CASCADE, related_name='v2ray_health_checks')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    cpu_usage = models.FloatField()
    memory_usage = models.FloatField()
    disk_usage = models.FloatField()
    uptime = models.PositiveIntegerField()
    error_message = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        app_label = 'v2ray'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['server', 'timestamp']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.server.name} - {self.status} - {self.timestamp}"
    
    def calculate_status(self):
        """Calculate health status based on metrics."""
        if self.error_message:
            return 'offline'
        
        if (
            self.cpu_usage > 95 or
            self.memory_usage > 95 or
            self.disk_usage > 95
        ):
            return 'critical'
        
        if (
            self.cpu_usage > 80 or
            self.memory_usage > 80 or
            self.disk_usage > 80
        ):
            return 'warning'
        
        return 'healthy'

class ServerRotationLog(models.Model):
    """Model for server rotation logs."""
    STATUS_CHOICES = (
        ('success', _('Success')),
        ('failed', _('Failed')),
        ('skipped', _('Skipped')),
    )
    
    subscription = models.ForeignKey('main.Subscription', on_delete=models.CASCADE, related_name='v2ray_rotation_logs')
    old_server = models.ForeignKey(Server, on_delete=models.CASCADE, related_name='v2ray_rotated_from')
    new_server = models.ForeignKey(Server, on_delete=models.CASCADE, related_name='v2ray_rotated_to')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    error_message = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        app_label = 'v2ray'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['subscription', 'timestamp']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.subscription.id} - {self.old_server.name} -> {self.new_server.name} - {self.status}"

class SyncLog(models.Model):
    """Model for 3x-UI sync logs"""
    STATUS_CHOICES = (
        ('success', _('Success')),
        ('failed', _('Failed')),
        ('partial', _('Partial Success')),
    )
    
    server = models.ForeignKey(Server, on_delete=models.CASCADE, related_name='v2ray_sync_logs')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    message = models.TextField(blank=True)
    details = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        app_label = 'v2ray'
    
    def __str__(self):
        return f"{self.server.name} - {self.status} - {self.created_at}"

class ClientConfig(models.Model):
    """Model for storing client configuration links"""
    client = models.OneToOneField(Client, on_delete=models.CASCADE, related_name='v2ray_config')
    vmess_link = models.TextField(blank=True, null=True)
    vless_link = models.TextField(blank=True, null=True)
    trojan_link = models.TextField(blank=True, null=True)
    shadowsocks_link = models.TextField(blank=True, null=True)
    subscription_url = models.URLField(blank=True, null=True)
    qrcode_data = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = 'v2ray'
    
    def __str__(self):
        return f"Config for {self.client.email}"

class V2RayServer(models.Model):
    """Model for storing 3x-UI server connection details."""
    
    name = models.CharField(_("Server Name"), max_length=100)
    host = models.CharField(_("Host"), max_length=255)
    port = models.IntegerField(
        _("Port"),
        validators=[MinValueValidator(1), MaxValueValidator(65535)],
        default=443
    )
    username = models.CharField(_("Username"), max_length=100)
    password = models.CharField(_("Password"), max_length=255)
    is_active = models.BooleanField(_("Active"), default=True)
    
    # Server capacity and load balancing
    max_users = models.IntegerField(
        _("Maximum Users"),
        validators=[MinValueValidator(1)],
        default=1000
    )
    current_users = models.IntegerField(
        _("Current Users"),
        validators=[MinValueValidator(0)],
        default=0
    )
    
    # Health monitoring
    last_check = models.DateTimeField(_("Last Health Check"), null=True, blank=True)
    is_healthy = models.BooleanField(_("Healthy"), default=True)
    health_check_failures = models.IntegerField(_("Health Check Failures"), default=0)
    
    # Traffic stats
    total_upload = models.BigIntegerField(_("Total Upload"), default=0)
    total_download = models.BigIntegerField(_("Total Download"), default=0)
    
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("V2Ray Server")
        verbose_name_plural = _("V2Ray Servers")
        ordering = ["name"]
    
    def __str__(self):
        return f"{self.name} ({self.host})"
    
    @property
    def load_percentage(self):
        """Calculate server load percentage."""
        if self.max_users > 0:
            return (self.current_users / self.max_users) * 100
        return 0
    
    @property
    def api_url(self):
        """Get the API URL for this server."""
        return f"http://{self.host}:{self.port}"

class V2RayInbound(models.Model):
    """Model for storing V2Ray inbound configurations."""
    
    server = models.ForeignKey(
        V2RayServer,
        on_delete=models.CASCADE,
        related_name="v2ray_inbounds"
    )
    inbound_id = models.IntegerField(_("Inbound ID"))
    tag = models.CharField(_("Tag"), max_length=100)
    protocol = models.CharField(_("Protocol"), max_length=50)
    port = models.IntegerField(
        _("Port"),
        validators=[MinValueValidator(1), MaxValueValidator(65535)]
    )
    
    # Settings and stream settings stored as JSON
    settings = models.JSONField(_("Settings"), default=dict)
    stream_settings = models.JSONField(_("Stream Settings"), default=dict)
    
    # Sniffing configuration
    sniffing_enabled = models.BooleanField(_("Sniffing Enabled"), default=True)
    sniffing_dest_override = models.JSONField(
        _("Sniffing Destination Override"),
        default=list
    )
    
    is_active = models.BooleanField(_("Active"), default=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("V2Ray Inbound")
        verbose_name_plural = _("V2Ray Inbounds")
        unique_together = ["server", "inbound_id"]
        ordering = ["server", "port"]
    
    def __str__(self):
        return f"{self.server.name} - {self.protocol}:{self.port}"

class V2RayTraffic(models.Model):
    """Model for storing user traffic data."""
    
    user = models.ForeignKey(
        User,  # Use the User model from main app
        on_delete=models.CASCADE,
        related_name="v2ray_traffic_records"
    )
    server = models.ForeignKey(
        V2RayServer,
        on_delete=models.CASCADE,
        related_name="v2ray_traffic_records"
    )
    inbound = models.ForeignKey(
        V2RayInbound,
        on_delete=models.CASCADE,
        related_name="v2ray_traffic_records"
    )
    
    upload = models.BigIntegerField(_("Upload"), default=0)
    download = models.BigIntegerField(_("Download"), default=0)
    
    recorded_at = models.DateTimeField(_("Recorded At"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("Traffic Record")
        verbose_name_plural = _("Traffic Records")
        ordering = ["-recorded_at"]
    
    def __str__(self):
        return f"{self.user} - {self.server} ({self.recorded_at})"
    
    @property
    def total_traffic(self):
        """Get total traffic (upload + download)."""
        return self.upload + self.download
