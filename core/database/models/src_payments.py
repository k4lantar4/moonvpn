from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.conf import settings
import secrets
import uuid
import logging
from django.contrib.auth import get_user_model

User = get_user_model()
logger = logging.getLogger(__name__)

# Create your models here.

class CardOwner(models.Model):
    """Model for tracking card owners"""
    name = models.CharField(max_length=100, verbose_name=_('Owner Name'))
    card_number = models.CharField(max_length=20, unique=True, verbose_name=_('Card Number'))
    bank_name = models.CharField(max_length=50, verbose_name=_('Bank Name'))
    is_active = models.BooleanField(default=True, verbose_name=_('Is Active'))
    is_verified = models.BooleanField(default=False, verbose_name=_('Is Verified'))
    verification_date = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payment_verified_card_owners'
    )
    notes = models.TextField(blank=True, verbose_name=_('Notes'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = 'payments'
        verbose_name = _('Card Owner')
        verbose_name_plural = _('Card Owners')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.card_number}"
    
    def verify(self, admin_user):
        """Verify a card owner"""
        self.is_verified = True
        self.verification_date = timezone.now()
        self.verified_by = admin_user
        self.save()

class Transaction(models.Model):
    """Base model for all transactions"""
    STATUS_CHOICES = (
        ('pending', _('Pending')),
        ('completed', _('Completed')),
        ('failed', _('Failed')),
        ('expired', _('Expired')),
        ('refunded', _('Refunded')),
    )
    
    TYPE_CHOICES = (
        ('deposit', _('Deposit')),
        ('purchase', _('Purchase')),
        ('refund', _('Refund')),
        ('admin', _('Admin Adjustment')),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payment_transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    description = models.TextField(blank=True)
    reference_id = models.CharField(max_length=100, unique=True, default=uuid.uuid4)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = 'payments'
    
    def __str__(self):
        return f"{self.user.username} - {self.amount} - {self.type} - {self.status}"


class CardPayment(models.Model):
    """Model for card to card payments"""
    STATUS_CHOICES = (
        ('pending', _('Pending')),
        ('verified', _('Verified')),
        ('rejected', _('Rejected')),
        ('expired', _('Expired')),
        ('retry', _('Retry Required')),
    )
    
    VERIFICATION_METHOD_CHOICES = (
        ('manual', _('Manual Verification')),
        ('ocr', _('OCR Verification')),
        ('both', _('Both Manual & OCR')),
    )
    
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE, related_name='payment_card_payment_details')
    card_owner = models.ForeignKey(CardOwner, on_delete=models.PROTECT, related_name='payment_payments', null=True)
    card_number = models.CharField(max_length=20)
    reference_number = models.CharField(max_length=100)
    transfer_time = models.DateTimeField()
    verification_code = models.CharField(max_length=10, unique=True)
    expires_at = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    verification_method = models.CharField(
        max_length=10,
        choices=VERIFICATION_METHOD_CHOICES,
        default='manual'
    )
    receipt_image = models.ImageField(
        upload_to='receipts/%Y/%m/%d/',
        null=True,
        blank=True,
        verbose_name=_('Receipt Image')
    )
    ocr_verified = models.BooleanField(default=False, verbose_name=_('OCR Verified'))
    ocr_data = models.JSONField(null=True, blank=True, verbose_name=_('OCR Data'))
    admin_note = models.TextField(blank=True)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payment_verified_card_payments'
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    retry_count = models.PositiveSmallIntegerField(default=0, verbose_name=_('Retry Count'))
    max_retries = models.PositiveSmallIntegerField(default=3, verbose_name=_('Max Retries'))
    last_retry_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = 'payments'
        verbose_name = _('Card Payment')
        verbose_name_plural = _('Card Payments')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.transaction.user.username} - {self.verification_code}"
    
    def save(self, *args, **kwargs):
        if not self.verification_code:
            self.verification_code = secrets.token_hex(5)[:10]
        if not self.expires_at:
            # Set expiry time to 30 minutes from now
            timeout_minutes = getattr(settings, 'CARD_PAYMENT_VERIFICATION_TIMEOUT_MINUTES', 30)
            self.expires_at = timezone.now() + timezone.timedelta(minutes=timeout_minutes)
        super().save(*args, **kwargs)
    
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    def can_retry(self):
        """Check if payment can be retried"""
        return (
            self.status in ['rejected', 'expired', 'retry'] and
            self.retry_count < self.max_retries
        )
    
    def retry_payment(self):
        """Retry a failed payment"""
        if not self.can_retry():
            return False
        
        self.status = 'pending'
        self.retry_count += 1
        self.last_retry_at = timezone.now()
        # Reset expiry time
        timeout_minutes = getattr(settings, 'CARD_PAYMENT_VERIFICATION_TIMEOUT_MINUTES', 30)
        self.expires_at = timezone.now() + timezone.timedelta(minutes=timeout_minutes)
        self.save()
        return True
    
    def verify_with_ocr(self, ocr_data):
        """Verify payment using OCR data"""
        try:
            # Validate OCR data matches payment details
            if (
                str(self.amount) in str(ocr_data.get('amount')) and
                self.card_number[-4:] in str(ocr_data.get('card_number')) and
                self.reference_number in str(ocr_data.get('reference'))
            ):
                self.ocr_verified = True
                self.ocr_data = ocr_data
                self.save()
                return True
            return False
        except Exception as e:
            logger.error(f"OCR verification error: {str(e)}")
            return False


class ZarinpalPayment(models.Model):
    """Model for Zarinpal payments"""
    STATUS_CHOICES = (
        ('pending', _('Pending')),
        ('verified', _('Verified')),
        ('failed', _('Failed')),
    )
    
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE, related_name='payment_zarinpal_payment_details')
    authority = models.CharField(max_length=100, blank=True, null=True)
    ref_id = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_url = models.URLField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.transaction.user.username} - {self.authority}"


class PaymentMethod(models.Model):
    """Payment method configuration"""
    CARD = 'card'
    ZARINPAL = 'zarinpal'
    
    METHOD_CHOICES = [
        (CARD, _('Card to Card')),
        (ZARINPAL, _('ZarinPal')),
    ]
    
    name = models.CharField(_('Name'), max_length=50, choices=METHOD_CHOICES, unique=True)
    is_active = models.BooleanField(_('Is Active'), default=True)
    icon = models.ImageField(_('Icon'), upload_to='payment_icons/', null=True, blank=True)
    description = models.TextField(_('Description'), blank=True, null=True)
    
    # Card payment specific fields
    card_number = models.CharField(_('Card Number'), max_length=50, blank=True, null=True)
    card_holder = models.CharField(_('Card Holder'), max_length=100, blank=True, null=True)
    bank_name = models.CharField(_('Bank Name'), max_length=100, blank=True, null=True)
    
    # Zarinpal specific fields
    merchant_id = models.CharField(_('Merchant ID'), max_length=100, blank=True, null=True)
    callback_url = models.URLField(_('Callback URL'), blank=True, null=True)
    
    # Additional configurations
    min_amount = models.PositiveIntegerField(_('Minimum Amount'), default=50000)  # e.g., 50,000 Tomans
    max_amount = models.PositiveIntegerField(_('Maximum Amount'), default=10000000)  # e.g., 10M Tomans
    verification_timeout = models.PositiveIntegerField(
        _('Verification Timeout (minutes)'), 
        default=30, 
        help_text=_('How long to wait for payment verification')
    )
    
    created_at = models.DateTimeField(_('Created At'), default=timezone.now)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    
    class Meta:
        verbose_name = _('Payment Method')
        verbose_name_plural = _('Payment Methods')
    
    def __str__(self):
        return self.get_name_display()
    
    def save(self, *args, **kwargs):
        # Load defaults from environment variables if not set
        if self.name == self.CARD and not self.card_number:
            self.card_number = settings.CARD_PAYMENT_NUMBER
            self.card_holder = settings.CARD_PAYMENT_HOLDER
            self.bank_name = settings.CARD_PAYMENT_BANK
        elif self.name == self.ZARINPAL and not self.merchant_id:
            self.merchant_id = settings.ZARINPAL_MERCHANT_ID
            self.callback_url = settings.PAYMENT_CALLBACK_URL
        
        super().save(*args, **kwargs)


class PaymentPlan(models.Model):
    """Available payment plans/packages"""
    TRAFFIC_UNIT_CHOICES = [
        ('MB', _('Megabytes')),
        ('GB', _('Gigabytes')),
        ('TB', _('Terabytes')),
    ]
    
    name = models.CharField(_('Name'), max_length=100)
    description = models.TextField(_('Description'), blank=True, null=True)
    traffic_amount = models.PositiveIntegerField(_('Traffic Amount'))
    traffic_unit = models.CharField(_('Traffic Unit'), max_length=2, choices=TRAFFIC_UNIT_CHOICES, default='GB')
    duration_days = models.PositiveIntegerField(_('Duration (days)'))
    price = models.PositiveIntegerField(_('Price (IRR)'))
    discount_price = models.PositiveIntegerField(_('Discount Price (IRR)'), null=True, blank=True)
    is_active = models.BooleanField(_('Is Active'), default=True)
    is_featured = models.BooleanField(_('Is Featured'), default=False)
    server_id = models.PositiveIntegerField(_('Server ID'), null=True, blank=True)
    inbound_id = models.PositiveIntegerField(_('Inbound ID'), null=True, blank=True)
    order = models.PositiveIntegerField(_('Order'), default=0, help_text=_('Display order'))
    icon = models.CharField(_('Icon'), max_length=50, blank=True, null=True)
    badge_text = models.CharField(_('Badge Text'), max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    
    class Meta:
        verbose_name = _('Payment Plan')
        verbose_name_plural = _('Payment Plans')
        ordering = ['order', 'price']
    
    def __str__(self):
        return f"{self.name} ({self.traffic_amount} {self.traffic_unit}, {self.duration_days} days)"
    
    @property
    def traffic_bytes(self):
        """Convert traffic amount to bytes"""
        multiplier = 1024 * 1024  # default MB
        if self.traffic_unit == 'GB':
            multiplier = 1024 * 1024 * 1024
        elif self.traffic_unit == 'TB':
            multiplier = 1024 * 1024 * 1024 * 1024
        
        return self.traffic_amount * multiplier
    
    @property
    def display_price(self):
        """Return the effective price (discount price if available)"""
        return self.discount_price if self.discount_price else self.price
    
    @property
    def discount_percentage(self):
        """Calculate discount percentage if discount price is set"""
        if self.discount_price and self.price > 0:
            return int(((self.price - self.discount_price) / self.price) * 100)
        return 0


class DiscountCode(models.Model):
    """Discount codes for payments"""
    code = models.CharField(_('Code'), max_length=50, unique=True)
    description = models.TextField(_('Description'), blank=True, null=True)
    discount_percentage = models.PositiveIntegerField(_('Discount Percentage'), default=10)
    max_uses = models.PositiveIntegerField(_('Maximum Uses'), null=True, blank=True)
    used_count = models.PositiveIntegerField(_('Used Count'), default=0)
    is_active = models.BooleanField(_('Is Active'), default=True)
    valid_from = models.DateTimeField(_('Valid From'), default=timezone.now)
    valid_until = models.DateTimeField(_('Valid Until'), null=True, blank=True)
    plans = models.ManyToManyField(PaymentPlan, blank=True, related_name='discount_codes')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_discounts')
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    
    class Meta:
        verbose_name = _('Discount Code')
        verbose_name_plural = _('Discount Codes')
    
    def __str__(self):
        return f"{self.code} ({self.discount_percentage}%)"
    
    @property
    def is_valid(self):
        """Check if discount code is valid for use"""
        now = timezone.now()
        max_uses_valid = self.max_uses is None or self.used_count < self.max_uses
        date_valid = (self.valid_from <= now) and (self.valid_until is None or now <= self.valid_until)
        return self.is_active and max_uses_valid and date_valid

    def apply_discount(self, amount):
        """Apply the discount to the given amount"""
        if not self.is_valid:
            return amount
        
        discounted = amount - (amount * self.discount_percentage / 100)
        return int(discounted)


class Payment(models.Model):
    """Payment record for tracking transactions"""
    PENDING = 'pending'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'
    EXPIRED = 'expired'
    CANCELED = 'canceled'
    REFUNDED = 'refunded'
    
    STATUS_CHOICES = [
        (PENDING, _('Pending')),
        (PROCESSING, _('Processing')),
        (COMPLETED, _('Completed')),
        (FAILED, _('Failed')),
        (EXPIRED, _('Expired')),
        (CANCELED, _('Canceled')),
        (REFUNDED, _('Refunded')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    plan = models.ForeignKey(PaymentPlan, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL, null=True, related_name='payments')
    discount_code = models.ForeignKey(DiscountCode, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    
    amount = models.PositiveIntegerField(_('Amount (IRR)'))
    original_amount = models.PositiveIntegerField(_('Original Amount (IRR)'), null=True, blank=True)
    description = models.TextField(_('Description'), blank=True, null=True)
    status = models.CharField(_('Status'), max_length=15, choices=STATUS_CHOICES, default=PENDING)
    reference_code = models.CharField(_('Reference Code'), max_length=100, null=True, blank=True)
    tracking_code = models.CharField(_('Tracking Code'), max_length=100, null=True, blank=True)
    payment_date = models.DateTimeField(_('Payment Date'), null=True, blank=True)
    expires_at = models.DateTimeField(_('Expires At'), null=True, blank=True)
    
    # For card payments
    card_number = models.CharField(_('Card Number (last 4 digits)'), max_length=4, blank=True, null=True)
    payer_name = models.CharField(_('Payer Name'), max_length=150, blank=True, null=True)
    payer_bank = models.CharField(_('Payer Bank'), max_length=100, blank=True, null=True)
    payment_time = models.DateTimeField(_('Payment Time'), null=True, blank=True)
    
    # For online payments
    transaction_id = models.CharField(_('Transaction ID'), max_length=100, blank=True, null=True)
    verification_code = models.CharField(_('Verification Code'), max_length=100, blank=True, null=True)
    gateway_response = models.JSONField(_('Gateway Response'), null=True, blank=True)
    
    # Account data (what was purchased)
    traffic_amount = models.PositiveIntegerField(_('Traffic Amount (bytes)'), null=True, blank=True)
    duration_days = models.PositiveIntegerField(_('Duration (days)'), null=True, blank=True)
    server_id = models.PositiveIntegerField(_('Server ID'), null=True, blank=True)
    inbound_id = models.PositiveIntegerField(_('Inbound ID'), null=True, blank=True)
    
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    
    class Meta:
        verbose_name = _('Payment')
        verbose_name_plural = _('Payments')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.id} - {self.user.username} - {self.get_status_display()} - {self.amount} IRR"
    
    def save(self, *args, **kwargs):
        # Set original amount if not set and this is a new record
        if not self.original_amount and not self.pk:
            self.original_amount = self.amount
        
        # Set expiration time if not set
        if not self.expires_at and self.payment_method:
            timeout_minutes = self.payment_method.verification_timeout or 30
            self.expires_at = timezone.now() + timezone.timedelta(minutes=timeout_minutes)
        
        # Save plan details for historical records
        if self.plan and not self.traffic_amount:
            self.traffic_amount = self.plan.traffic_bytes
            self.duration_days = self.plan.duration_days
            self.server_id = self.plan.server_id
            self.inbound_id = self.plan.inbound_id
        
        super().save(*args, **kwargs)
    
    def mark_as_completed(self, reference_code=None, tracking_code=None):
        """Mark payment as completed"""
        self.status = self.COMPLETED
        self.payment_date = timezone.now()
        
        if reference_code:
            self.reference_code = reference_code
        
        if tracking_code:
            self.tracking_code = tracking_code
        
        # Apply discount code usage
        if self.discount_code and self.discount_code.is_valid:
            self.discount_code.used_count += 1
            self.discount_code.save()
        
        self.save()
        
        # Log success
        logger.info(f"Payment {self.id} marked as completed. Amount: {self.amount} IRR")
        
        return True
    
    def mark_as_failed(self, reason=None):
        """Mark payment as failed"""
        self.status = self.FAILED
        if reason:
            self.description = (self.description or '') + f"\nFailure reason: {reason}"
        self.save()
        
        # Log failure
        logger.warning(f"Payment {self.id} marked as failed. Reason: {reason}")
        
        return True
    
    def mark_as_expired(self):
        """Mark payment as expired"""
        if self.status == self.PENDING:
            self.status = self.EXPIRED
            self.save()
            
            # Log expiration
            logger.info(f"Payment {self.id} marked as expired.")
            
            return True
        return False
    
    def mark_as_canceled(self, reason=None):
        """Mark payment as canceled"""
        self.status = self.CANCELED
        if reason:
            self.description = (self.description or '') + f"\nCancellation reason: {reason}"
        self.save()
        
        # Log cancellation
        logger.info(f"Payment {self.id} canceled by user. Reason: {reason}")
        
        return True
    
    @property
    def is_paid(self):
        """Check if payment is completed"""
        return self.status == self.COMPLETED
    
    @property
    def is_pending(self):
        """Check if payment is still pending"""
        return self.status == self.PENDING
    
    @property
    def is_expired(self):
        """Check if payment is expired"""
        if self.status == self.EXPIRED:
            return True
        
        if self.status == self.PENDING and self.expires_at and timezone.now() > self.expires_at:
            self.mark_as_expired()
            return True
        
        return False
