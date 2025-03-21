from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

class Service(models.Model):
    """
    Service model for managing different types of services.
    """
    name = models.CharField(_('Name'), max_length=100)
    description = models.TextField(_('Description'), blank=True)
    icon = models.ImageField(upload_to='services/icons/', null=True, blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_services'
    )
    is_active = models.BooleanField(_('Is Active'), default=True)
    features = models.JSONField(default=list)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Service')
        verbose_name_plural = _('Services')
        ordering = ['-created_at']

    def check_health(self):
        """
        Check if the service is healthy
        Override this method in subclasses to implement service-specific health checks
        """
        return True

class Plan(models.Model):
    """
    Plan model for managing service plans.
    """
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='plans')
    name = models.CharField(_('Name'), max_length=100)
    description = models.TextField(_('Description'), blank=True)
    price = models.DecimalField(_('Price'), max_digits=10, decimal_places=2)
    duration = models.IntegerField(_('Duration (days)'))
    features = models.JSONField(_('Features'), default=list)
    is_active = models.BooleanField(_('Is Active'), default=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    def __str__(self):
        return f"{self.service.name} - {self.name}"

    class Meta:
        verbose_name = _('Plan')
        verbose_name_plural = _('Plans')
        ordering = ['price']

class Subscription(models.Model):
    """
    Subscription model for managing user subscriptions.
    """
    STATUS_CHOICES = [
        ('active', _('Active')),
        ('expired', _('Expired')),
        ('cancelled', _('Cancelled')),
        ('pending', _('Pending')),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name='subscriptions')
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    start_date = models.DateTimeField(_('Start Date'))
    end_date = models.DateTimeField(_('End Date'))
    auto_renew = models.BooleanField(_('Auto Renew'), default=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    def __str__(self):
        return f"{self.user.email} - {self.plan.name}"

    class Meta:
        verbose_name = _('Subscription')
        verbose_name_plural = _('Subscriptions')
        ordering = ['-created_at']

    def is_active(self):
        return self.status == 'active' and self.end_date > timezone.now()

    def is_expired(self):
        return self.status == 'expired' or self.end_date <= timezone.now()

    def is_cancelled(self):
        return self.status == 'cancelled'

    def is_pending(self):
        return self.status == 'pending'

    def renew(self):
        if self.status != 'active':
            self.status = 'active'
            self.start_date = timezone.now()
            self.end_date = timezone.now() + timezone.timedelta(days=self.plan.duration)
            self.save()

    def cancel(self):
        if self.status == 'active':
            self.status = 'cancelled'
            self.auto_renew = False
            self.save()

class Config(models.Model):
    """
    Configuration model for managing service configurations.
    """
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='configs')
    key = models.CharField(_('Key'), max_length=100)
    value = models.JSONField(_('Value'))
    description = models.TextField(blank=True)
    is_active = models.BooleanField(_('Is Active'), default=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    def __str__(self):
        return f"{self.service.name} - {self.key}"

    class Meta:
        verbose_name = _('Config')
        verbose_name_plural = _('Configs')
        unique_together = ['service', 'key']
        ordering = ['key']

class Usage(models.Model):
    """
    Usage model for tracking service usage.
    """
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='usage_records')
    date = models.DateField(_('Date'))
    amount = models.DecimalField(_('Amount'), max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    def __str__(self):
        return f"{self.subscription.user.email} - {self.date}"

    class Meta:
        verbose_name = _('Usage')
        verbose_name_plural = _('Usage Records')
        ordering = ['-date']
        unique_together = ['subscription', 'date']

class ServiceLog(models.Model):
    """
    Service log model for tracking service events.
    """
    LEVEL_CHOICES = [
        ('info', _('Info')),
        ('warning', _('Warning')),
        ('error', _('Error')),
        ('debug', _('Debug')),
    ]

    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='logs')
    level = models.CharField(
        _('Level'),
        max_length=20,
        choices=LEVEL_CHOICES,
        default='info'
    )
    message = models.TextField(_('Message'))
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    def __str__(self):
        return f"{self.service.name} - {self.level}"

    class Meta:
        verbose_name = _('Service Log')
        verbose_name_plural = _('Service Logs')
        ordering = ['-created_at']

class ServiceMetric(models.Model):
    """
    Service metric model for tracking service performance metrics.
    """
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='metrics')
    name = models.CharField(_('Name'), max_length=100)
    value = models.JSONField(_('Value'))
    timestamp = models.DateTimeField(_('Timestamp'))
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    def __str__(self):
        return f"{self.service.name} - {self.name}"

    class Meta:
        verbose_name = _('Service Metric')
        verbose_name_plural = _('Service Metrics')
        ordering = ['-timestamp']

class ServiceAlert(models.Model):
    """
    Service alert model for managing service alerts.
    """
    LEVEL_CHOICES = [
        ('info', _('Info')),
        ('warning', _('Warning')),
        ('error', _('Error')),
        ('critical', _('Critical')),
    ]

    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='alerts')
    level = models.CharField(
        _('Level'),
        max_length=20,
        choices=LEVEL_CHOICES,
        default='info'
    )
    message = models.TextField(_('Message'))
    is_resolved = models.BooleanField(_('Is Resolved'), default=False)
    resolved_at = models.DateTimeField(_('Resolved At'), null=True, blank=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    def __str__(self):
        return f"{self.service.name} - {self.level}"

    class Meta:
        verbose_name = _('Service Alert')
        verbose_name_plural = _('Service Alerts')
        ordering = ['-created_at']

    def resolve(self):
        if not self.is_resolved:
            self.is_resolved = True
            self.resolved_at = timezone.now()
            self.save() 