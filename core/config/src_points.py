from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone

class PointsTransaction(models.Model):
    """Model for tracking points transactions."""
    
    class TransactionType(models.TextChoices):
        EARN = 'earn', _('Earn')
        SPEND = 'spend', _('Spend')
        EXPIRE = 'expire', _('Expire')
        ADJUST = 'adjust', _('Adjust')
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='points_transactions'
    )
    type = models.CharField(
        max_length=10,
        choices=TransactionType.choices,
        default=TransactionType.EARN
    )
    points = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text=_('Number of points (positive for earn, negative for spend)')
    )
    description = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'type']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.type} {abs(self.points)} points"
    
    def clean(self):
        if self.type in [self.TransactionType.SPEND, self.TransactionType.EXPIRE]:
            if self.points > 0:
                raise ValidationError(_('Points must be negative for spend/expire transactions'))
        elif self.type in [self.TransactionType.EARN, self.TransactionType.ADJUST]:
            if self.points < 0:
                raise ValidationError(_('Points must be positive for earn/adjust transactions'))

class PointsRedemptionRule(models.Model):
    """Model for defining points redemption rules."""
    
    class RewardType(models.TextChoices):
        DISCOUNT = 'discount', _('Discount')
        VIP = 'vip', _('VIP Status')
        TRAFFIC = 'traffic', _('Extra Traffic')
        CUSTOM = 'custom', _('Custom Reward')
    
    name = models.CharField(max_length=100)
    description = models.TextField()
    points_required = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text=_('Points required to redeem this reward')
    )
    reward_type = models.CharField(
        max_length=20,
        choices=RewardType.choices,
        default=RewardType.DISCOUNT
    )
    reward_value = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text=_('Value of the reward (e.g., discount percentage, VIP days)')
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['points_required']
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['reward_type']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.points_required} points)"
    
    def clean(self):
        if self.reward_type == self.RewardType.DISCOUNT:
            if self.reward_value > 100:
                raise ValidationError(_('Discount percentage cannot exceed 100%'))

class PointsRedemption(models.Model):
    """Model for tracking points redemptions."""
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='points_redemptions'
    )
    rule = models.ForeignKey(
        PointsRedemptionRule,
        on_delete=models.PROTECT,
        related_name='redemptions'
    )
    points_spent = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text=_('Points spent on this redemption')
    )
    reward_value = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text=_('Value of the reward received')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['rule']),
        ]
    
    def __str__(self):
        return f"{self.user.username} redeemed {self.rule.name}"
    
    def clean(self):
        if self.points_spent != self.rule.points_required:
            raise ValidationError(_('Points spent must match rule requirements'))
        if self.reward_value != self.rule.reward_value:
            raise ValidationError(_('Reward value must match rule value')) 