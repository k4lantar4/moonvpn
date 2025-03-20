from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.conf import settings
import secrets

# Create your models here.

class APIKey(models.Model):
    """Model for API keys used for external services"""
    name = models.CharField(max_length=100)
    key = models.CharField(max_length=255, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='api_keys', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.key:
            self.key = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)
    
    def is_valid(self):
        if not self.is_active:
            return False
        
        if self.expires_at and timezone.now() > self.expires_at:
            return False
        
        return True


class APIRequest(models.Model):
    """Model for tracking API requests"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='api_requests', null=True, blank=True)
    api_key = models.ForeignKey(APIKey, on_delete=models.SET_NULL, related_name='requests', null=True, blank=True)
    endpoint = models.CharField(max_length=255)
    method = models.CharField(max_length=10)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    response_code = models.PositiveIntegerField()
    response_time_ms = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        user_str = self.user.username if self.user else 'Anonymous'
        return f"{user_str} - {self.method} {self.endpoint} - {self.response_code}"


class APIRateLimit(models.Model):
    """Model for API rate limiting"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='rate_limits', null=True, blank=True)
    api_key = models.ForeignKey(APIKey, on_delete=models.CASCADE, related_name='rate_limits', null=True, blank=True)
    endpoint = models.CharField(max_length=255, blank=True)
    requests_count = models.PositiveIntegerField(default=0)
    last_request = models.DateTimeField(auto_now=True)
    reset_at = models.DateTimeField()
    
    def __str__(self):
        user_str = self.user.username if self.user else 'Anonymous'
        endpoint_str = self.endpoint or 'All endpoints'
        return f"{user_str} - {endpoint_str} - {self.requests_count}"
    
    def is_rate_limited(self, max_requests):
        """Check if the user/API key is rate limited"""
        if timezone.now() > self.reset_at:
            # Reset counter if the time window has passed
            self.requests_count = 0
            self.reset_at = timezone.now() + timezone.timedelta(hours=1)
            self.save()
            return False
        
        return self.requests_count >= max_requests
    
    def increment(self):
        """Increment the request counter"""
        self.requests_count += 1
        self.save()


class Webhook(models.Model):
    """Model for webhook configurations"""
    TYPE_CHOICES = (
        ('telegram', _('Telegram')),
        ('payment', _('Payment')),
        ('custom', _('Custom')),
    )
    
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    url = models.URLField()
    secret_key = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.type})"
    
    def save(self, *args, **kwargs):
        if not self.secret_key:
            self.secret_key = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)
