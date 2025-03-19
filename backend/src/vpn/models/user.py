from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    """Extended user model with additional fields"""
    
    class Role(models.TextChoices):
        ADMIN = 'admin', _('Admin')
        RESELLER = 'reseller', _('Reseller')
        USER = 'user', _('User')
    
    # Basic Info
    phone = models.CharField(max_length=15, blank=True)
    telegram_id = models.CharField(max_length=50, blank=True)
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.USER
    )
    
    # Wallet
    wallet_balance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    
    # Reseller Info
    parent_reseller = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sub_resellers'
    )
    commission_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text='Commission rate in percentage'
    )
    
    # Stats & Metrics
    total_spent = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    total_traffic_used = models.BigIntegerField(default=0)
    joined_at = models.DateTimeField(auto_now_add=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    
    # Settings & Preferences
    language = models.CharField(max_length=10, default='fa')
    notifications_enabled = models.BooleanField(default=True)
    auto_renew_enabled = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'vpn_users'
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        indexes = [
            models.Index(fields=['telegram_id']),
            models.Index(fields=['role']),
            models.Index(fields=['parent_reseller'])
        ]
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN
    
    @property
    def is_reseller(self):
        return self.role == self.Role.RESELLER
    
    def get_active_subscriptions(self):
        """Get user's active subscriptions"""
        return self.subscriptions.filter(status='active')
    
    def get_total_traffic_limit(self):
        """Get total traffic limit from all active subscriptions"""
        active_subs = self.get_active_subscriptions()
        return sum(sub.plan.traffic_limit for sub in active_subs)
    
    def get_remaining_traffic(self):
        """Get remaining traffic across all subscriptions"""
        total_limit = self.get_total_traffic_limit()
        return max(0, total_limit - self.total_traffic_used)
    
    def add_to_wallet(self, amount):
        """Add amount to user's wallet"""
        self.wallet_balance += amount
        self.save(update_fields=['wallet_balance'])
    
    def deduct_from_wallet(self, amount):
        """Deduct amount from user's wallet"""
        if self.wallet_balance >= amount:
            self.wallet_balance -= amount
            self.save(update_fields=['wallet_balance'])
            return True
        return False
    
    def record_traffic_usage(self, bytes_used):
        """Record traffic usage"""
        self.total_traffic_used += bytes_used
        self.save(update_fields=['total_traffic_used'])
    
    def can_purchase_plan(self, plan):
        """Check if user can purchase a plan"""
        # Check if user has reached max active subscriptions
        active_subs_count = self.get_active_subscriptions().count()
        if active_subs_count >= 3:  # Max 3 active subscriptions
            return False, "Maximum active subscriptions reached"
            
        # Check if plan is available
        if not plan.is_available():
            return False, "Plan is not available"
            
        return True, None
    
    def calculate_price_with_discount(self, plan):
        """Calculate final price after applying reseller discounts"""
        price = plan.price
        
        if self.is_reseller:
            # Apply reseller's own commission
            price = price * (1 - self.commission_rate / 100)
        elif self.parent_reseller:
            # Apply parent reseller's commission
            price = price * (1 - self.parent_reseller.commission_rate / 100)
            
        return price
    
    def get_referral_code(self):
        """Get or create referral code for reseller"""
        if not self.is_reseller:
            return None
            
        from .referral import ReferralCode
        referral_code, created = ReferralCode.objects.get_or_create(
            user=self,
            defaults={'code': ReferralCode.generate_code()}
        )
        return referral_code.code 