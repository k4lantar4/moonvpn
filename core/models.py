from django.db import models
from django.core.cache import cache
from django.conf import settings

class SystemSettings(models.Model):
    """Model for storing system-wide settings"""
    
    site_name = models.CharField(max_length=100, default='V2Ray Management System')
    site_description = models.TextField(blank=True)
    maintenance_mode = models.BooleanField(default=False)
    session_timeout = models.IntegerField(default=30)  # minutes
    max_login_attempts = models.IntegerField(default=5)
    enable_2fa = models.BooleanField(default=False)
    enable_email_notifications = models.BooleanField(default=True)
    enable_telegram_notifications = models.BooleanField(default=True)
    telegram_bot_token = models.CharField(max_length=100, blank=True)
    zarinpal_merchant_id = models.CharField(max_length=100, blank=True)
    min_withdrawal_amount = models.DecimalField(max_digits=10, decimal_places=0, default=100000)
    enable_card_payment = models.BooleanField(default=False)
    default_language = models.CharField(max_length=2, choices=settings.LANGUAGES, default='fa')
    enable_rtl = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'System Settings'
        verbose_name_plural = 'System Settings'
    
    def __str__(self):
        return 'System Settings'
    
    def save(self, *args, **kwargs):
        # Only allow one instance
        if not self.pk and SystemSettings.objects.exists():
            return
        
        super().save(*args, **kwargs)
        # Clear cache after saving
        cache.delete('system_settings')
    
    @classmethod
    def get_settings(cls):
        """Get system settings from cache or database"""
        settings = cache.get('system_settings')
        if settings is None:
            settings = cls.objects.first()
            if settings:
                cache.set('system_settings', settings, timeout=3600)  # Cache for 1 hour
        return settings
    
    @classmethod
    def get_setting(cls, key, default=None):
        """Get a specific setting value"""
        settings = cls.get_settings()
        if settings:
            return getattr(settings, key, default) 