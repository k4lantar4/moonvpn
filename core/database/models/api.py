"""
API-related models for MoonVPN.
Defines API keys, requests, rate limits, and webhooks.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.conf import settings
import secrets
from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Enum, JSON, Text
from sqlalchemy.orm import relationship
import enum

# Create your models here.

class APIKeyStatus(enum.Enum):
    """API key status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    REVOKED = "revoked"

class APIRequestStatus(enum.Enum):
    """API request status."""
    SUCCESS = "success"
    FAILED = "failed"
    RATE_LIMITED = "rate_limited"
    UNAUTHORIZED = "unauthorized"

class APIKey(models.Model):
    """
    API key model.
    Manages API authentication and access control.
    """
    
    key = models.CharField(max_length=64, unique=True, null=False)
    name = models.CharField(max_length=100, null=False)
    description = models.CharField(max_length=500, null=True)
    status = models.CharField(max_length=20, choices=[(status.value, status.value) for status in APIKeyStatus], default=APIKeyStatus.ACTIVE.value, null=False)
    is_active = models.BooleanField(default=True)
    last_used = models.DateTimeField(null=True)
    expires_at = models.DateTimeField(null=True)
    permissions = models.JSONField(null=True)  # List of allowed endpoints
    metadata = models.JSONField(null=True)
    
    # Relationships
    requests = relationship("APIRequest", back_populates="api_key", cascade="all, delete-orphan")
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.key:
            self.key = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)
    
    def is_valid(self):
        if not self.is_active or self.status != APIKeyStatus.ACTIVE.value:
            return False
        
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False
        
        return True
    
    def revoke(self):
        """Revoke API key."""
        self.status = APIKeyStatus.REVOKED.value
        self.is_active = False
    
    def update_usage(self):
        """Update last used timestamp."""
        self.last_used = datetime.utcnow()

class APIRequest(models.Model):
    """
    API request model.
    Logs all API requests for monitoring and debugging.
    """
    
    method = models.CharField(max_length=10, null=False)
    endpoint = models.CharField(max_length=255, null=False)
    status = models.CharField(max_length=20, choices=[(status.value, status.value) for status in APIRequestStatus], null=False)
    status_code = models.PositiveIntegerField(null=False)
    response_time = models.PositiveIntegerField(null=True)  # in milliseconds
    ip_address = models.GenericIPAddressField(null=True)
    user_agent = models.TextField(blank=True)
    request_data = models.JSONField(null=True)
    response_data = models.JSONField(null=True)
    error_message = models.TextField(null=True)
    metadata = models.JSONField(null=True)
    
    # Relationships
    api_key_id = models.ForeignKey(APIKey, on_delete=models.CASCADE, related_name='requests', null=False)
    api_key = relationship("APIKey", back_populates="requests")
    
    def __str__(self):
        user_str = self.api_key.name if self.api_key else 'Anonymous'
        return f"{user_str} - {self.method} {self.endpoint} - {self.status}"
    
    def log_response(self, status_code: int, response_data: dict, error: Optional[str] = None):
        """Log response data."""
        self.status_code = status_code
        self.response_data = response_data
        if error:
            self.error_message = str(error)
            self.status = APIRequestStatus.FAILED.value
        else:
            self.status = APIRequestStatus.SUCCESS.value

class APIRateLimit(models.Model):
    """
    API rate limit model.
    Manages rate limiting for API endpoints.
    """
    
    endpoint = models.CharField(max_length=255, null=False)
    method = models.CharField(max_length=10, null=False)
    requests_per_minute = models.PositiveIntegerField(null=False)
    requests_per_hour = models.PositiveIntegerField(null=False)
    requests_per_day = models.PositiveIntegerField(null=False)
    is_active = models.BooleanField(default=True)
    metadata = models.JSONField(null=True)
    
    def __str__(self):
        return f"{self.endpoint} - {self.method}"
    
    def get_limit(self, period: str) -> int:
        """Get rate limit for specified period."""
        limits = {
            "minute": self.requests_per_minute,
            "hour": self.requests_per_hour,
            "day": self.requests_per_day
        }
        return limits.get(period, 0)

class Webhook(models.Model):
    """
    Webhook model.
    Manages webhook endpoints for event notifications.
    """
    
    url = models.URLField(null=False)
    name = models.CharField(max_length=100, null=False)
    description = models.CharField(max_length=500, null=True)
    is_active = models.BooleanField(default=True)
    secret = models.CharField(max_length=64, null=True)
    events = models.JSONField(null=True)  # List of subscribed events
    last_triggered = models.DateTimeField(null=True)
    failure_count = models.PositiveIntegerField(default=0)
    metadata = models.JSONField(null=True)
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.secret:
            self.secret = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)
    
    def trigger(self, event: str, data: dict):
        """Trigger webhook with event data."""
        if not self.is_active or event not in (self.events or []):
            return
        
        self.last_triggered = datetime.utcnow()
        # Webhook triggering logic would be implemented in a service layer
    
    def increment_failures(self):
        """Increment failure count."""
        self.failure_count += 1
        if self.failure_count >= 5:
            self.is_active = False
    
    def reset_failures(self):
        """Reset failure count."""
        self.failure_count = 0
