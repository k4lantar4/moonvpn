"""
Feature management models for MoonVPN.

This module defines models for managing system features and configurations.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

class FeatureFlag(models.Model):
    """Model to manage feature flags that can be enabled/disabled by admins."""
    
    name = models.CharField(
        max_length=50,
        unique=True,
        help_text=_("Internal feature name (lowercase, no spaces)")
    )
    
    display_name = models.CharField(
        max_length=100,
        help_text=_("Display name for this feature in the admin interface")
    )
    
    description = models.TextField(
        blank=True, 
        help_text=_("Description of what this feature does")
    )
    
    enabled = models.BooleanField(
        default=True,
        help_text=_("Whether this feature is currently enabled")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.display_name} ({'Enabled' if self.enabled else 'Disabled'})"
    
    class Meta:
        verbose_name = _("Feature Flag")
        verbose_name_plural = _("Feature Flags")


class SystemConfig(models.Model):
    """Model for system-wide configuration settings."""
    
    # General settings
    maintenance_mode = models.BooleanField(
        default=False,
        help_text=_("When enabled, only admins can access the bot")
    )
    
    default_language = models.CharField(
        max_length=2,
        default="fa",
        help_text=_("Default language for new users (e.g., 'fa', 'en')")
    )
    
    bot_name = models.CharField(
        max_length=50,
        default="MoonVPN",
        help_text=_("Name of the bot displayed to users")
    )
    
    support_contact = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text=_("Support contact information (e.g., Telegram username)")
    )
    
    # Payment settings
    card_payment_enabled = models.BooleanField(
        default=True,
        help_text=_("Enable card-to-card payment method")
    )
    
    card_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text=_("Card number for card-to-card payments")
    )
    
    card_holder = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text=_("Card holder name for card-to-card payments")
    )
    
    bank_name = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text=_("Bank name for card-to-card payments")
    )
    
    min_payment_amount = models.PositiveIntegerField(
        default=10000,
        help_text=_("Minimum amount for payments (in Toman)")
    )
    
    max_payment_amount = models.PositiveIntegerField(
        default=5000000,
        help_text=_("Maximum amount for payments (in Toman)")
    )
    
    zarinpal_enabled = models.BooleanField(
        default=False,
        help_text=_("Enable Zarinpal payment gateway")
    )
    
    zarinpal_merchant_id = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text=_("Zarinpal merchant ID")
    )
    
    zarinpal_callback_url = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text=_("Zarinpal callback URL")
    )
    
    # Bot behavior settings
    account_expiry_notification_days = models.PositiveSmallIntegerField(
        default=3,
        help_text=_("Days before account expiry to send notification")
    )
    
    traffic_threshold_notification = models.PositiveSmallIntegerField(
        default=80,
        help_text=_("Traffic threshold percentage to trigger notification")
    )
    
    def __str__(self):
        return "System Configuration"
    
    class Meta:
        verbose_name = _("System Configuration")
        verbose_name_plural = _("System Configurations")


class UserPreference(models.Model):
    """Model for user-specific preferences."""
    
    user = models.OneToOneField(
        'User',
        on_delete=models.CASCADE,
        related_name='preferences'
    )
    
    language = models.CharField(
        max_length=2,
        default="fa",
        help_text=_("User's preferred language (e.g., 'fa', 'en')")
    )
    
    theme = models.CharField(
        max_length=20,
        default="light",
        choices=[
            ("light", _("Light")),
            ("dark", _("Dark")),
            ("blue", _("Blue")),
            ("green", _("Green")),
        ],
        help_text=_("User's preferred theme")
    )
    
    notifications_enabled = models.BooleanField(
        default=True,
        help_text=_("Whether user wants to receive notifications")
    )
    
    expiry_notification_days = models.PositiveSmallIntegerField(
        default=3,
        help_text=_("Days before expiry to receive notification")
    )
    
    traffic_notification_threshold = models.PositiveSmallIntegerField(
        default=90,
        help_text=_("Traffic usage percentage threshold to receive notification")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Preferences for {self.user}"
    
    class Meta:
        verbose_name = _("User Preference")
        verbose_name_plural = _("User Preferences") 