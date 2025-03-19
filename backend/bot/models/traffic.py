"""
Traffic monitoring database models.
"""

from django.db import models
from django.utils import timezone

class TrafficStats(models.Model):
    """Traffic statistics for subscriptions"""
    subscription_id = models.CharField(max_length=255)
    user_id = models.BigIntegerField()
    total_usage = models.BigIntegerField(default=0)  # In bytes
    upload = models.BigIntegerField(default=0)  # In bytes
    download = models.BigIntegerField(default=0)  # In bytes
    last_updated = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=['subscription_id']),
            models.Index(fields=['user_id']),
            models.Index(fields=['last_updated']),
        ]

class TrafficEvent(models.Model):
    """Traffic-related events"""
    EVENT_TYPES = [
        ('traffic_warning', 'Traffic Warning'),
        ('traffic_exceeded', 'Traffic Exceeded'),
        ('traffic_reset', 'Traffic Reset'),
        ('traffic_added', 'Traffic Added'),
    ]

    subscription_id = models.CharField(max_length=255)
    user_id = models.BigIntegerField()
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    data = models.JSONField()
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=['subscription_id']),
            models.Index(fields=['user_id']),
            models.Index(fields=['event_type']),
            models.Index(fields=['timestamp']),
        ]

class DailyTrafficLog(models.Model):
    """Daily traffic usage log"""
    subscription_id = models.CharField(max_length=255)
    user_id = models.BigIntegerField()
    date = models.DateField()
    usage = models.BigIntegerField(default=0)  # In bytes
    peak_usage = models.BigIntegerField(default=0)  # Maximum usage in any hour
    peak_hour = models.IntegerField(null=True)  # Hour with maximum usage (0-23)

    class Meta:
        indexes = [
            models.Index(fields=['subscription_id']),
            models.Index(fields=['user_id']),
            models.Index(fields=['date']),
        ]
        unique_together = ['subscription_id', 'date']

class TrafficUsagePattern(models.Model):
    """User traffic usage patterns"""
    user_id = models.BigIntegerField()
    average_daily_usage = models.BigIntegerField(default=0)  # In bytes
    peak_usage_time = models.IntegerField()  # Hour of day (0-23)
    usage_pattern = models.JSONField()  # Hourly usage distribution
    last_updated = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=['user_id']),
            models.Index(fields=['last_updated']),
        ]

class BandwidthAlert(models.Model):
    """Bandwidth alerts for servers"""
    ALERT_TYPES = [
        ('high_usage', 'High Usage'),
        ('approaching_limit', 'Approaching Limit'),
        ('exceeded', 'Exceeded'),
    ]

    server_id = models.CharField(max_length=255)
    alert_type = models.CharField(max_length=50, choices=ALERT_TYPES)
    current_usage = models.BigIntegerField()  # In bytes
    threshold = models.BigIntegerField()  # In bytes
    timestamp = models.DateTimeField(default=timezone.now)
    resolved = models.BooleanField(default=False)
    resolution_time = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['server_id']),
            models.Index(fields=['alert_type']),
            models.Index(fields=['timestamp']),
        ] 