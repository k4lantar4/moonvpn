"""
Security-related database models.
"""

from django.db import models
from django.utils import timezone

class SecurityEvent(models.Model):
    """Security event log"""
    EVENT_TYPES = [
        ('blocked_ip', 'Blocked IP'),
        ('suspicious_activity', 'Suspicious Activity'),
        ('rate_limit_exceeded', 'Rate Limit Exceeded'),
        ('login_attempt', 'Login Attempt'),
        ('geolocation_anomaly', 'Geolocation Anomaly'),
    ]

    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    user_id = models.BigIntegerField(null=True, blank=True)
    ip_address = models.GenericIPAddressField()
    data = models.JSONField()
    timestamp = models.DateTimeField(default=timezone.now)
    resolved = models.BooleanField(default=False)
    resolution_notes = models.TextField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['event_type']),
            models.Index(fields=['user_id']),
            models.Index(fields=['ip_address']),
            models.Index(fields=['timestamp']),
        ]

class BlockedIP(models.Model):
    """Blocked IP addresses"""
    ip_address = models.GenericIPAddressField(unique=True)
    reason = models.CharField(max_length=255)
    blocked_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    blocked_by = models.CharField(max_length=50, default='system')

    class Meta:
        indexes = [
            models.Index(fields=['ip_address']),
            models.Index(fields=['expires_at']),
        ]

class UserLocation(models.Model):
    """User location history"""
    user_id = models.BigIntegerField()
    ip_address = models.GenericIPAddressField()
    country = models.CharField(max_length=2)
    city = models.CharField(max_length=100, null=True, blank=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    timestamp = models.DateTimeField(default=timezone.now)
    suspicious = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=['user_id']),
            models.Index(fields=['ip_address']),
            models.Index(fields=['timestamp']),
        ]

class RateLimitLog(models.Model):
    """Rate limit tracking"""
    key = models.CharField(max_length=255)  # IP or user_id based key
    action = models.CharField(max_length=50)  # login, payment, api, etc.
    count = models.IntegerField(default=0)
    window_start = models.DateTimeField()
    last_request = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=['key']),
            models.Index(fields=['action']),
            models.Index(fields=['window_start']),
        ]
        unique_together = ['key', 'action', 'window_start']

class LoginAttempt(models.Model):
    """Login attempt tracking"""
    user_id = models.BigIntegerField(null=True, blank=True)
    ip_address = models.GenericIPAddressField()
    success = models.BooleanField()
    timestamp = models.DateTimeField(default=timezone.now)
    user_agent = models.TextField(null=True, blank=True)
    location_data = models.JSONField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['user_id']),
            models.Index(fields=['ip_address']),
            models.Index(fields=['timestamp']),
        ] 