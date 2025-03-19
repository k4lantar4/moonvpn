"""
Subscription Model

This module defines the Subscription model and related functionality.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from django.utils import timezone
import uuid

class Plan(models.Model):
    """Subscription plan model."""
    
    name = models.CharField(
        _('name'),
        max_length=100,
        help_text=_('Plan name')
    )
    
    description = models.TextField(
        _('description'),
        blank=True,
        help_text=_('Plan description')
    )
    
    duration_days = models.PositiveIntegerField(
        _('duration in days'),
        validators=[MinValueValidator(1)],
        help_text=_('Plan duration in days')
    )
    
    traffic_limit = models.BigIntegerField(
        _('traffic limit'),
        validators=[MinValueValidator(1)],
        help_text=_('Traffic limit in bytes')
    )
    
    price = models.DecimalField(
        _('price'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text=_('Plan price')
    )
    
    is_active = models.BooleanField(
        _('active status'),
        default=True,
        help_text=_('Whether this plan is currently active')
    )
    
    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True
    )
    
    updated_at = models.DateTimeField(
        _('updated at'),
        auto_now=True
    )
    
    class Meta:
        verbose_name = _('plan')
        verbose_name_plural = _('plans')
        ordering = ['price', 'duration_days']
    
    def __str__(self):
        return f'{self.name} ({self.duration_days} days)'

class Subscription(models.Model):
    """User subscription model."""
    
    STATUS_CHOICES = [
        ('active', _('Active')),
        ('expired', _('Expired')),
        ('cancelled', _('Cancelled')),
        ('suspended', _('Suspended')),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text=_('Unique subscription identifier')
    )
    
    user = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='subscriptions',
        help_text=_('User who owns this subscription')
    )
    
    plan = models.ForeignKey(
        Plan,
        on_delete=models.PROTECT,
        help_text=_('Subscription plan')
    )
    
    server = models.ForeignKey(
        'Server',
        on_delete=models.PROTECT,
        help_text=_('VPN server')
    )
    
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        help_text=_('Current subscription status')
    )
    
    start_date = models.DateTimeField(
        _('start date'),
        default=timezone.now,
        help_text=_('Subscription start date')
    )
    
    end_date = models.DateTimeField(
        _('end date'),
        help_text=_('Subscription end date')
    )
    
    traffic_used = models.BigIntegerField(
        _('traffic used'),
        default=0,
        help_text=_('Traffic used in bytes')
    )
    
    traffic_limit = models.BigIntegerField(
        _('traffic limit'),
        help_text=_('Traffic limit in bytes')
    )
    
    config = models.JSONField(
        _('configuration'),
        default=dict,
        help_text=_('VPN configuration data')
    )
    
    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True
    )
    
    updated_at = models.DateTimeField(
        _('updated at'),
        auto_now=True
    )
    
    class Meta:
        verbose_name = _('subscription')
        verbose_name_plural = _('subscriptions')
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.user.username} - {self.plan.name}'
    
    def save(self, *args, **kwargs):
        """Override save to set end_date and traffic_limit from plan."""
        if not self.end_date:
            self.end_date = self.start_date + timezone.timedelta(days=self.plan.duration_days)
        if not self.traffic_limit:
            self.traffic_limit = self.plan.traffic_limit
        super().save(*args, **kwargs)
    
    def is_expired(self):
        """Check if subscription is expired."""
        return timezone.now() >= self.end_date
    
    def is_traffic_exceeded(self):
        """Check if traffic limit is exceeded."""
        return self.traffic_used >= self.traffic_limit
    
    def get_remaining_traffic(self):
        """Get remaining traffic in bytes."""
        return max(0, self.traffic_limit - self.traffic_used)
    
    def get_remaining_days(self):
        """Get remaining days until expiration."""
        if self.is_expired():
            return 0
        return (self.end_date - timezone.now()).days
    
    def update_traffic(self, bytes_used):
        """Update traffic usage."""
        self.traffic_used += bytes_used
        if self.traffic_used >= self.traffic_limit:
            self.status = 'suspended'
        self.save()
    
    def renew(self, plan=None):
        """Renew subscription with same or new plan."""
        plan = plan or self.plan
        self.start_date = timezone.now()
        self.end_date = self.start_date + timezone.timedelta(days=plan.duration_days)
        self.traffic_used = 0
        self.traffic_limit = plan.traffic_limit
        self.status = 'active'
        self.save()
    
    def cancel(self):
        """Cancel subscription."""
        self.status = 'cancelled'
        self.save()
    
    def suspend(self):
        """Suspend subscription."""
        self.status = 'suspended'
        self.save()
    
    def activate(self):
        """Activate subscription."""
        self.status = 'active'
        self.save() 