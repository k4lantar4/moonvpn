"""
Wallet and Transaction models for MoonVPN.

This module defines the Wallet and Transaction models for managing user payments.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import uuid

class Wallet(models.Model):
    """Model for user wallets."""
    
    user = models.OneToOneField(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='wallet',
        help_text=_("User who owns this wallet")
    )
    
    balance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text=_("Current wallet balance")
    )
    
    total_deposit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text=_("Total amount deposited")
    )
    
    total_spent = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text=_("Total amount spent")
    )
    
    last_transaction = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("Last transaction time")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def deposit(self, amount, description=None, reference_id=None):
        """
        Add funds to this wallet.
        
        Args:
            amount: Amount to add
            description: Optional description
            reference_id: Optional reference ID
            
        Returns:
            Transaction object
        """
        if amount <= 0:
            raise ValueError("Deposit amount must be positive")
            
        self.balance += amount
        self.total_deposit += amount
        self.last_transaction = timezone.now()
        self.save(update_fields=['balance', 'total_deposit', 'last_transaction', 'updated_at'])
        
        transaction = Transaction.objects.create(
            wallet=self,
            amount=amount,
            type='deposit',
            description=description,
            reference_id=reference_id
        )
        
        return transaction
    
    def withdraw(self, amount, description=None, reference_id=None):
        """
        Withdraw funds from this wallet.
        
        Args:
            amount: Amount to withdraw
            description: Optional description
            reference_id: Optional reference ID
            
        Returns:
            Transaction object or None if insufficient funds
        """
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive")
            
        if self.balance < amount:
            return None
            
        self.balance -= amount
        self.total_spent += amount
        self.last_transaction = timezone.now()
        self.save(update_fields=['balance', 'total_spent', 'last_transaction', 'updated_at'])
        
        transaction = Transaction.objects.create(
            wallet=self,
            amount=-amount,
            type='withdraw',
            description=description,
            reference_id=reference_id
        )
        
        return transaction
    
    def can_afford(self, amount):
        """Check if the wallet can afford a certain amount."""
        return self.balance >= amount
    
    def __str__(self):
        return f"Wallet for {self.user.username}"
    
    class Meta:
        verbose_name = _("Wallet")
        verbose_name_plural = _("Wallets")


class Transaction(models.Model):
    """Model for wallet transactions."""
    
    TYPE_CHOICES = [
        ('deposit', _('Deposit')),
        ('withdraw', _('Withdraw')),
        ('refund', _('Refund')),
        ('bonus', _('Bonus')),
        ('commission', _('Commission')),
    ]
    
    STATUS_CHOICES = [
        ('completed', _('Completed')),
        ('pending', _('Pending')),
        ('failed', _('Failed')),
        ('cancelled', _('Cancelled')),
    ]
    
    wallet = models.ForeignKey(
        'Wallet',
        on_delete=models.CASCADE,
        related_name='transactions',
        help_text=_("Wallet this transaction belongs to")
    )
    
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text=_("Transaction amount (positive for deposit, negative for withdraw)")
    )
    
    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        help_text=_("Transaction type")
    )
    
    description = models.TextField(
        null=True,
        blank=True,
        help_text=_("Transaction description")
    )
    
    reference_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text=_("External reference ID")
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='completed',
        help_text=_("Transaction status")
    )
    
    admin_note = models.TextField(
        null=True,
        blank=True,
        help_text=_("Admin notes about this transaction")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.get_type_display()} of {abs(self.amount)} ({self.wallet.user.username})"
    
    class Meta:
        verbose_name = _("Transaction")
        verbose_name_plural = _("Transactions")
        ordering = ['-created_at']


class Order(models.Model):
    """Model for orders."""
    
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('processing', _('Processing')),
        ('completed', _('Completed')),
        ('cancelled', _('Cancelled')),
        ('failed', _('Failed')),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('wallet', _('Wallet')),
        ('card', _('Card to Card')),
        ('zarinpal', _('ZarinPal')),
    ]
    
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='orders',
        help_text=_("User who placed this order")
    )
    
    subscription_plan = models.ForeignKey(
        'vpn.SubscriptionPlan',
        on_delete=models.CASCADE,
        help_text=_("Subscription plan ordered")
    )
    
    location = models.ForeignKey(
        'vpn.Location',
        on_delete=models.CASCADE,
        help_text=_("Selected location")
    )
    
    server = models.ForeignKey(
        'vpn.Server',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text=_("Selected server (can be auto-assigned)")
    )
    
    quantity = models.IntegerField(
        default=1,
        help_text=_("Number of accounts ordered")
    )
    
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text=_("Total price before discount")
    )
    
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text=_("Discount amount")
    )
    
    final_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text=_("Final price after discount")
    )
    
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        help_text=_("Payment method used")
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text=_("Order status")
    )
    
    voucher = models.ForeignKey(
        'payment.Voucher',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text=_("Voucher applied to this order")
    )
    
    transaction = models.ForeignKey(
        'Transaction',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text=_("Transaction associated with this order")
    )
    
    admin_note = models.TextField(
        null=True,
        blank=True,
        help_text=_("Admin notes about this order")
    )
    
    receipt_image = models.ImageField(
        upload_to='receipts/',
        null=True,
        blank=True,
        help_text=_("Receipt image for card payments")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def apply_voucher(self, voucher):
        """Apply a voucher to this order."""
        if self.voucher:
            return False
            
        if not voucher.is_valid():
            return False
            
        # Calculate discount
        discount = self.total_price * (voucher.discount_percent / 100)
        
        # Apply max discount limit if set
        if voucher.max_discount and discount > voucher.max_discount:
            discount = voucher.max_discount
            
        self.voucher = voucher
        self.discount_amount = discount
        self.final_price = self.total_price - discount
        self.save(update_fields=['voucher', 'discount_amount', 'final_price', 'updated_at'])
        
        # Update voucher usage
        voucher.current_uses += 1
        voucher.save(update_fields=['current_uses'])
        
        return True
    
    def complete_order(self):
        """Complete this order by creating VPN accounts."""
        if self.status != 'processing':
            return False
            
        from backend.models.vpn.account import VPNAccount
        
        # Select server if not specified
        if not self.server:
            self.server = self.location.get_best_server()
            if not self.server:
                self.status = 'failed'
                self.admin_note = "No available server in selected location"
                self.save(update_fields=['server', 'status', 'admin_note', 'updated_at'])
                return False
                
        # Create VPN accounts
        accounts = []
        for i in range(self.quantity):
            email = f"{self.user.username}_{uuid.uuid4().hex[:8]}@moonvpn.ir"
            account = VPNAccount.objects.create(
                user=self.user,
                server=self.server,
                email=email,
                expires_at=timezone.now() + timezone.timedelta(days=self.subscription_plan.duration_days),
                total_traffic_gb=self.subscription_plan.traffic_limit_gb,
                max_connections=self.subscription_plan.max_connections,
                remark=f"MoonVPN-{self.user.username}-{i+1}"
            )
            accounts.append(account)
            
        # Update order status
        self.status = 'completed'
        self.save(update_fields=['status', 'updated_at'])
        
        # Update server statistics
        self.server.current_clients += self.quantity
        self.server.update_load_factor()
        
        return accounts
    
    def __str__(self):
        return f"Order {self.id} by {self.user.username} ({self.get_status_display()})"
    
    class Meta:
        verbose_name = _("Order")
        verbose_name_plural = _("Orders")
        ordering = ['-created_at']


class Voucher(models.Model):
    """Model for discount vouchers."""
    
    code = models.CharField(
        max_length=20,
        unique=True,
        help_text=_("Voucher code")
    )
    
    discount_percent = models.IntegerField(
        help_text=_("Discount percentage")
    )
    
    max_discount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Maximum discount amount (optional)")
    )
    
    valid_from = models.DateTimeField(
        help_text=_("When this voucher becomes valid")
    )
    
    valid_until = models.DateTimeField(
        help_text=_("When this voucher expires")
    )
    
    max_uses = models.IntegerField(
        help_text=_("Maximum number of uses (0 for unlimited)")
    )
    
    current_uses = models.IntegerField(
        default=0,
        help_text=_("Current number of uses")
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text=_("Whether this voucher is active")
    )
    
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text=_("User who created this voucher")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def is_valid(self):
        """Check if this voucher is valid."""
        now = timezone.now()
        
        if not self.is_active:
            return False
            
        if now < self.valid_from or now > self.valid_until:
            return False
            
        if self.max_uses > 0 and self.current_uses >= self.max_uses:
            return False
            
        return True
    
    def __str__(self):
        return f"{self.code} ({self.discount_percent}% off)"
    
    class Meta:
        verbose_name = _("Voucher")
        verbose_name_plural = _("Vouchers")
        ordering = ['-created_at'] 