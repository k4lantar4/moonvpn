"""
Models for subscription plans and user roles management.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model

User = get_user_model()


class SubscriptionPlan(models.Model):
    """Model for subscription plans."""
    
    name = models.CharField(_("Plan Name"), max_length=100)
    description = models.TextField(_("Description"))
    price = models.DecimalField(_("Price"), max_digits=10, decimal_places=2)
    duration_days = models.IntegerField(_("Duration (Days)"))
    traffic_limit_gb = models.IntegerField(
        _("Traffic Limit (GB)"),
        validators=[MinValueValidator(1)]
    )
    max_connections = models.IntegerField(
        _("Maximum Connections"),
        validators=[MinValueValidator(1)]
    )
    
    # Features
    is_active = models.BooleanField(_("Active"), default=True)
    has_priority_support = models.BooleanField(_("Priority Support"), default=False)
    has_dedicated_ip = models.BooleanField(_("Dedicated IP"), default=False)
    server_access_level = models.IntegerField(
        _("Server Access Level"),
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=1,
        help_text=_("1: Basic servers, 5: Premium servers")
    )
    
    # Points and rewards
    points_reward = models.IntegerField(
        _("Points Reward"),
        default=0,
        help_text=_("Points awarded when purchasing this plan")
    )
    referral_bonus_percent = models.IntegerField(
        _("Referral Bonus Percentage"),
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        default=0
    )
    
    # Discounts
    has_renewal_discount = models.BooleanField(_("Renewal Discount"), default=False)
    renewal_discount_percent = models.IntegerField(
        _("Renewal Discount Percentage"),
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        default=0
    )
    
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("Subscription Plan")
        verbose_name_plural = _("Subscription Plans")
        ordering = ["price", "duration_days"]
    
    def __str__(self):
        return f"{self.name} ({self.duration_days} days)"


class UserSubscription(models.Model):
    """Model for user subscriptions."""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="sub_subscriptions"
    )
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.PROTECT,
        related_name="sub_subscriptions"
    )
    
    # Status
    STATUS_CHOICES = [
        ("active", _("Active")),
        ("expired", _("Expired")),
        ("cancelled", _("Cancelled")),
        ("pending", _("Pending")),
    ]
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )
    
    # Dates
    start_date = models.DateTimeField(_("Start Date"), null=True, blank=True)
    end_date = models.DateTimeField(_("End Date"), null=True, blank=True)
    
    # Usage
    traffic_used_bytes = models.BigIntegerField(_("Traffic Used (Bytes)"), default=0)
    connections_count = models.IntegerField(_("Active Connections"), default=0)
    
    # Payment
    payment_id = models.CharField(_("Payment ID"), max_length=100, blank=True)
    amount_paid = models.DecimalField(
        _("Amount Paid"),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("User Subscription")
        verbose_name_plural = _("User Subscriptions")
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"{self.user.username} - {self.plan.name}"
    
    @property
    def traffic_remaining_gb(self):
        """Calculate remaining traffic in GB."""
        used_gb = self.traffic_used_bytes / (1024 * 1024 * 1024)
        return max(0, self.plan.traffic_limit_gb - used_gb)
    
    @property
    def is_expired(self):
        """Check if subscription is expired."""
        from django.utils import timezone
        return self.end_date and self.end_date < timezone.now()


class UserWallet(models.Model):
    """Model for user wallet management."""
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="sub_wallet"
    )
    balance = models.DecimalField(
        _("Balance"),
        max_digits=10,
        decimal_places=2,
        default=0
    )
    points = models.IntegerField(_("Points"), default=0)
    
    # Referral system
    referral_code = models.CharField(
        _("Referral Code"),
        max_length=20,
        unique=True,
        blank=True,
        null=True
    )
    referred_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sub_referrals"
    )
    total_referral_earnings = models.DecimalField(
        _("Total Referral Earnings"),
        max_digits=10,
        decimal_places=2,
        default=0
    )
    
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("User Wallet")
        verbose_name_plural = _("User Wallets")
    
    def __str__(self):
        return f"{self.user.username}'s Wallet"
    
    def save(self, *args, **kwargs):
        """Generate referral code if not set."""
        if not self.referral_code:
            import uuid
            self.referral_code = str(uuid.uuid4())[:8].upper()
        super().save(*args, **kwargs)


class UserRole(models.Model):
    """Model for user roles and permissions."""
    
    name = models.CharField(_("Role Name"), max_length=100)
    description = models.TextField(_("Description"))
    
    # Permissions
    can_manage_users = models.BooleanField(_("Can Manage Users"), default=False)
    can_manage_plans = models.BooleanField(_("Can Manage Plans"), default=False)
    can_manage_servers = models.BooleanField(_("Can Manage Servers"), default=False)
    can_access_admin = models.BooleanField(_("Can Access Admin"), default=False)
    can_manage_payments = models.BooleanField(_("Can Manage Payments"), default=False)
    can_view_stats = models.BooleanField(_("Can View Statistics"), default=False)
    
    # Limits
    max_referrals = models.IntegerField(
        _("Maximum Referrals"),
        validators=[MinValueValidator(0)],
        default=0
    )
    commission_rate = models.IntegerField(
        _("Commission Rate (%)"),
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        default=0
    )
    
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("User Role")
        verbose_name_plural = _("User Roles")
    
    def __str__(self):
        return self.name


class WalletTransaction(models.Model):
    """Model for wallet transactions."""
    
    wallet = models.ForeignKey(
        UserWallet,
        on_delete=models.CASCADE,
        related_name="sub_transactions"
    )
    
    # Transaction details
    TRANSACTION_TYPES = [
        ("deposit", _("Deposit")),
        ("withdrawal", _("Withdrawal")),
        ("subscription", _("Subscription Purchase")),
        ("referral", _("Referral Bonus")),
        ("refund", _("Refund")),
        ("adjustment", _("Manual Adjustment")),
    ]
    transaction_type = models.CharField(
        _("Transaction Type"),
        max_length=20,
        choices=TRANSACTION_TYPES
    )
    amount = models.DecimalField(_("Amount"), max_digits=10, decimal_places=2)
    points = models.IntegerField(_("Points"), default=0)
    
    # Status
    STATUS_CHOICES = [
        ("pending", _("Pending")),
        ("completed", _("Completed")),
        ("failed", _("Failed")),
        ("cancelled", _("Cancelled")),
    ]
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )
    
    description = models.TextField(_("Description"), blank=True)
    reference_id = models.CharField(
        _("Reference ID"),
        max_length=100,
        blank=True,
        help_text=_("Payment ID, subscription ID, etc.")
    )
    
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("Wallet Transaction")
        verbose_name_plural = _("Wallet Transactions")
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"{self.wallet.user.username} - {self.transaction_type} - {self.amount}" 