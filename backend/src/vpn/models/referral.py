import string
import random
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings

class ReferralCode(models.Model):
    """Model for storing referral codes"""
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='referral_code'
    )
    code = models.CharField(max_length=10, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    total_uses = models.IntegerField(default=0)
    total_earnings = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    
    class Meta:
        db_table = 'vpn_referral_codes'
        verbose_name = _('Referral Code')
        verbose_name_plural = _('Referral Codes')
    
    def __str__(self):
        return f"{self.code} ({self.user.username})"
    
    @staticmethod
    def generate_code(length=8):
        """Generate a unique referral code"""
        chars = string.ascii_uppercase + string.digits
        while True:
            code = ''.join(random.choices(chars, k=length))
            if not ReferralCode.objects.filter(code=code).exists():
                return code
    
    def record_usage(self, amount):
        """Record usage of referral code"""
        self.total_uses += 1
        self.total_earnings += amount
        self.save()

class ReferralUse(models.Model):
    """Model for tracking referral code usage"""
    
    referral_code = models.ForeignKey(
        ReferralCode,
        on_delete=models.CASCADE,
        related_name='uses'
    )
    referred_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='referral_signups'
    )
    transaction = models.ForeignKey(
        'Transaction',
        on_delete=models.SET_NULL,
        null=True,
        related_name='referral_uses'
    )
    commission_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'vpn_referral_uses'
        verbose_name = _('Referral Use')
        verbose_name_plural = _('Referral Uses')
        unique_together = [['referral_code', 'referred_user']]
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['referral_code', 'referred_user'])
        ]
    
    def __str__(self):
        return f"{self.referral_code.code} used by {self.referred_user.username}"
    
    def save(self, *args, **kwargs):
        # Update referral code stats
        if not self.pk:  # Only on creation
            self.referral_code.record_usage(self.commission_amount)
        super().save(*args, **kwargs)

class ReferralSettings(models.Model):
    """Model for storing referral system settings"""
    
    commission_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=10,
        help_text=_('Default commission rate in percentage')
    )
    min_commission = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=1000,
        help_text=_('Minimum commission amount')
    )
    max_commission = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=1000000,
        help_text=_('Maximum commission amount')
    )
    expiry_days = models.IntegerField(
        default=30,
        help_text=_('Number of days before referral code expires')
    )
    
    class Meta:
        db_table = 'vpn_referral_settings'
        verbose_name = _('Referral Settings')
        verbose_name_plural = _('Referral Settings')
    
    @classmethod
    def get_settings(cls):
        """Get or create referral settings"""
        settings, _ = cls.objects.get_or_create(pk=1)
        return settings
    
    def calculate_commission(self, amount):
        """Calculate commission amount for a given purchase amount"""
        commission = amount * (self.commission_rate / 100)
        return max(
            min(commission, self.max_commission),
            self.min_commission
        ) 