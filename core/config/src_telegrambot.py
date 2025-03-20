from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.conf import settings

# Create your models here.

class TelegramMessage(models.Model):
    """Model for storing Telegram message templates"""
    name = models.CharField(max_length=100)
    content = models.TextField()
    language_code = models.CharField(max_length=10, default='fa')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.language_code})"


class TelegramState(models.Model):
    """Model for storing Telegram conversation states"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='telegram_states')
    state = models.CharField(max_length=100)
    data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.state}"


class TelegramNotification(models.Model):
    """Model for storing Telegram notifications"""
    TYPE_CHOICES = (
        ('user', _('User Notification')),
        ('admin', _('Admin Notification')),
        ('system', _('System Notification')),
    )
    
    STATUS_CHOICES = (
        ('pending', _('Pending')),
        ('sent', _('Sent')),
        ('failed', _('Failed')),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='telegram_notifications')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.type} - {self.status}"


class TelegramCallback(models.Model):
    """Model for storing Telegram callback data"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='telegram_callbacks')
    callback_data = models.CharField(max_length=255)
    data = models.JSONField(default=dict, blank=True)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.callback_data}"
    
    def is_expired(self):
        return timezone.now() > self.expires_at


class TelegramLog(models.Model):
    """Model for logging Telegram bot activity"""
    LEVEL_CHOICES = (
        ('info', _('Info')),
        ('warning', _('Warning')),
        ('error', _('Error')),
        ('debug', _('Debug')),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='telegram_logs', null=True, blank=True)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='info')
    message = models.TextField()
    details = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        user_str = self.user.username if self.user else 'System'
        return f"{user_str} - {self.level} - {self.created_at}"


class BotCommand(models.Model):
    """Model for storing custom bot commands"""
    command = models.CharField(max_length=100)
    description = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_admin_only = models.BooleanField(default=False)
    handler_function = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.command


class BotSetting(models.Model):
    """Model for storing bot settings"""
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True)
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.key


class FAQ(models.Model):
    """Model for storing Frequently Asked Questions"""
    question = models.CharField(max_length=255)
    answer = models.TextField()
    language_code = models.CharField(max_length=10, default='fa')
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', 'created_at']
        
    def __str__(self):
        return f"{self.question[:30]} ({self.language_code})"


class Tutorial(models.Model):
    """Model for storing step-by-step tutorials for setup"""
    CATEGORY_CHOICES = (
        ('v2ray', _('V2Ray')),
        ('vmess', _('VMess')),
        ('vless', _('VLess')),
        ('trojan', _('Trojan')),
        ('shadowsocks', _('ShadowSocks')),
        ('general', _('General')),
    )
    
    PLATFORM_CHOICES = (
        ('android', _('Android')),
        ('ios', _('iOS')),
        ('windows', _('Windows')),
        ('macos', _('macOS')),
        ('linux', _('Linux')),
        ('all', _('All Platforms')),
    )
    
    title = models.CharField(max_length=255)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    language_code = models.CharField(max_length=10, default='fa')
    content = models.TextField()
    image_url = models.URLField(blank=True, null=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['category', 'platform', 'order', 'title']
        
    def __str__(self):
        return f"{self.title} - {self.get_platform_display()} ({self.language_code})"


class UserPreference(models.Model):
    """Model for storing user preferences for notifications and settings"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='telegram_preferences')
    notify_expiration = models.BooleanField(default=True, help_text=_("Notify before subscription expires"))
    expiration_days_threshold = models.PositiveIntegerField(default=3, help_text=_("Days before expiration to notify"))
    notify_data_usage = models.BooleanField(default=True, help_text=_("Notify when data usage threshold is reached"))
    data_usage_threshold = models.PositiveIntegerField(default=80, help_text=_("Percentage of data usage to trigger notification"))
    auto_renewal = models.BooleanField(default=False, help_text=_("Automatically renew subscription when expired"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Preferences for {self.user.username}"


class ReferralCode(models.Model):
    """Model for tracking referral codes"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='telegram_referral_code')
    code = models.CharField(max_length=20, unique=True)
    bonus_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Referral code for {self.user.username}: {self.code}"


class ReferralUsage(models.Model):
    """Model for tracking referral code usage"""
    referral_code = models.ForeignKey(ReferralCode, on_delete=models.CASCADE, related_name='telegram_usages')
    referred_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='telegram_referred_by')
    bonus_applied = models.BooleanField(default=False)
    bonus_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.referred_user.username} used {self.referral_code.code}"


class ServerStatus(models.Model):
    """Model for tracking server status and health"""
    server = models.ForeignKey('main.Server', on_delete=models.CASCADE, related_name='telegram_status_logs')
    is_online = models.BooleanField(default=True)
    ping_ms = models.IntegerField(null=True, blank=True)
    cpu_usage = models.FloatField(null=True, blank=True)
    memory_usage = models.FloatField(null=True, blank=True)
    disk_usage = models.FloatField(null=True, blank=True)
    checked_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        status = "Online" if self.is_online else "Offline"
        return f"{self.server.name} - {status} - {self.checked_at}"
    
    class Meta:
        ordering = ['-checked_at']
        get_latest_by = 'checked_at'
