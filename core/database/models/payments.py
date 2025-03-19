from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Numeric, JSON, UniqueConstraint, Table
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timedelta
import uuid
import secrets
import logging
from core.database.base import BaseModel
from core.database.models.user import User

logger = logging.getLogger(__name__)

# Association table for PaymentPlan and DiscountCode many-to-many relationship
payment_plan_discount_codes = Table(
    'payment_plan_discount_codes',
    BaseModel.metadata,
    Column('payment_plan_id', Integer, ForeignKey('payment_plans.id'), primary_key=True),
    Column('discount_code_id', Integer, ForeignKey('discount_codes.id'), primary_key=True)
)

class CardOwner(BaseModel):
    """Model for tracking card owners"""
    __tablename__ = 'card_owners'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    card_number = Column(String(20), unique=True, nullable=False)
    bank_name = Column(String(50), nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    verification_date = Column(DateTime, nullable=True)
    verified_by_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    verified_by = relationship("User", foreign_keys=[verified_by_id])
    payments = relationship("CardPayment", back_populates="card_owner")
    
    def __str__(self):
        return f"{self.name} - {self.card_number}"
    
    def verify(self, admin_user):
        """Verify a card owner"""
        self.is_verified = True
        self.verification_date = datetime.utcnow()
        self.verified_by_id = admin_user.id

class Transaction(BaseModel):
    """Base model for all transactions"""
    __tablename__ = 'transactions'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    status = Column(String(20), nullable=False, default='pending')
    type = Column(String(20), nullable=False)
    description = Column(Text, nullable=True)
    reference_id = Column(String(100), unique=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="transactions")
    card_payment = relationship("CardPayment", back_populates="transaction", uselist=False)
    zarinpal_payment = relationship("ZarinpalPayment", back_populates="transaction", uselist=False)
    
    def __str__(self):
        return f"{self.user.username} - {self.amount} - {self.type} - {self.status}"

class CardPayment(BaseModel):
    """Model for card to card payments"""
    __tablename__ = 'card_payments'

    id = Column(Integer, primary_key=True)
    transaction_id = Column(Integer, ForeignKey('transactions.id'), nullable=False)
    card_owner_id = Column(Integer, ForeignKey('card_owners.id'), nullable=True)
    card_number = Column(String(20), nullable=False)
    reference_number = Column(String(100), nullable=False)
    transfer_time = Column(DateTime, nullable=False)
    verification_code = Column(String(10), unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    status = Column(String(20), nullable=False, default='pending')
    verification_method = Column(String(10), nullable=False, default='manual')
    receipt_image = Column(String(255), nullable=True)
    ocr_verified = Column(Boolean, default=False)
    ocr_data = Column(JSON, nullable=True)
    admin_note = Column(Text, nullable=True)
    verified_by_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    last_retry_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    transaction = relationship("Transaction", back_populates="card_payment")
    card_owner = relationship("CardOwner", back_populates="payments")
    verified_by = relationship("User", foreign_keys=[verified_by_id])

    def __str__(self):
        return f"{self.transaction.user.username} - {self.verification_code}"
    
    def save(self, db):
        """Save card payment with verification code generation"""
        if not self.verification_code:
            self.verification_code = secrets.token_hex(5)[:10]
        if not self.expires_at:
            self.expires_at = datetime.utcnow() + timedelta(minutes=30)
        return super().save(db)
    
    def is_expired(self):
        """Check if payment is expired"""
        return datetime.utcnow() > self.expires_at
    
    def can_retry(self):
        """Check if payment can be retried"""
        return (
            self.status in ['rejected', 'expired', 'retry'] and
            self.retry_count < self.max_retries
        )
    
    def retry_payment(self, db):
        """Retry a failed payment"""
        if not self.can_retry():
            return False
        
        self.status = 'pending'
        self.retry_count += 1
        self.last_retry_at = datetime.utcnow()
        # Reset expiry time
        self.expires_at = datetime.utcnow() + timedelta(minutes=30)
        return self.save(db)
    
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
                return True
            return False
        except Exception as e:
            logger.error(f"OCR verification error: {str(e)}")
            return False

class ZarinpalPayment(BaseModel):
    """Model for Zarinpal payments"""
    __tablename__ = 'zarinpal_payments'

    id = Column(Integer, primary_key=True)
    transaction_id = Column(Integer, ForeignKey('transactions.id'), nullable=False)
    authority = Column(String(100), nullable=True)
    ref_id = Column(String(100), nullable=True)
    status = Column(String(20), nullable=False, default='pending')
    payment_url = Column(String(255), nullable=True)
    
    transaction = relationship("Transaction", back_populates="zarinpal_payment")
    
    def __str__(self):
        return f"{self.transaction.user.username} - {self.authority}"

class PaymentMethod(BaseModel):
    """Payment method configuration"""
    __tablename__ = 'payment_methods'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    is_active = Column(Boolean, default=True)
    icon = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    
    # Card payment specific fields
    card_number = Column(String(50), nullable=True)
    card_holder = Column(String(100), nullable=True)
    bank_name = Column(String(100), nullable=True)
    
    # Zarinpal specific fields
    merchant_id = Column(String(100), nullable=True)
    callback_url = Column(String(255), nullable=True)
    
    # Additional configurations
    min_amount = Column(Integer, default=50000)  # e.g., 50,000 Tomans
    max_amount = Column(Integer, default=10000000)  # e.g., 10M Tomans
    verification_timeout = Column(Integer, default=30)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    payments = relationship("Payment", back_populates="payment_method")

    def __str__(self):
        return self.name

class PaymentPlan(BaseModel):
    """Available payment plans/packages"""
    __tablename__ = 'payment_plans'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    traffic_amount = Column(Integer, nullable=False)
    traffic_unit = Column(String(2), nullable=False, default='GB')
    duration_days = Column(Integer, nullable=False)
    price = Column(Integer, nullable=False)
    discount_price = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    server_id = Column(Integer, nullable=True)
    inbound_id = Column(Integer, nullable=True)
    order = Column(Integer, default=0)
    icon = Column(String(50), nullable=True)
    badge_text = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    payments = relationship("Payment", back_populates="plan")
    discount_codes = relationship("DiscountCode", secondary="payment_plan_discount_codes")

    def __str__(self):
        return self.name

    @property
    def traffic_bytes(self):
        """Convert traffic amount to bytes"""
        multiplier = {
            'MB': 1024 * 1024,
            'GB': 1024 * 1024 * 1024,
            'TB': 1024 * 1024 * 1024 * 1024
        }
        return self.traffic_amount * multiplier.get(self.traffic_unit, 1024 * 1024 * 1024)

    @property
    def display_price(self):
        """Get display price (with discount if available)"""
        return self.discount_price if self.discount_price else self.price

    @property
    def discount_percentage(self):
        """Calculate discount percentage"""
        if not self.discount_price:
            return 0
        return int(((self.price - self.discount_price) / self.price) * 100)

class DiscountCode(BaseModel):
    """Discount codes for payments"""
    __tablename__ = 'discount_codes'

    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    discount_percentage = Column(Integer, default=10)
    max_uses = Column(Integer, nullable=True)
    used_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    valid_from = Column(DateTime, default=datetime.utcnow)
    valid_until = Column(DateTime, nullable=True)
    created_by_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    created_by = relationship("User", foreign_keys=[created_by_id])
    payments = relationship("Payment", back_populates="discount_code")
    plans = relationship("PaymentPlan", secondary="payment_plan_discount_codes")

    def __str__(self):
        return self.code

    @property
    def is_valid(self):
        """Check if discount code is valid"""
        now = datetime.utcnow()
        return (
            self.is_active and
            self.valid_from <= now and
            (not self.valid_until or self.valid_until >= now) and
            (not self.max_uses or self.used_count < self.max_uses)
        )

    def apply_discount(self, amount):
        """Apply discount to amount"""
        if not self.is_valid:
            return amount
        return int(amount * (1 - self.discount_percentage / 100))

class Payment(BaseModel):
    """Payment record for tracking transactions"""
    __tablename__ = 'payments'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    plan_id = Column(Integer, ForeignKey('payment_plans.id'), nullable=True)
    payment_method_id = Column(Integer, ForeignKey('payment_methods.id'), nullable=True)
    discount_code_id = Column(Integer, ForeignKey('discount_codes.id'), nullable=True)
    
    amount = Column(Integer, nullable=False)
    original_amount = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)
    status = Column(String(15), nullable=False, default='pending')
    reference_code = Column(String(100), nullable=True)
    tracking_code = Column(String(100), nullable=True)
    payment_date = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    
    # For card payments
    card_number = Column(String(4), nullable=True)
    payer_name = Column(String(150), nullable=True)
    payer_bank = Column(String(100), nullable=True)
    payment_time = Column(DateTime, nullable=True)
    
    # For online payments
    transaction_id = Column(String(100), nullable=True)
    verification_code = Column(String(100), nullable=True)
    gateway_response = Column(JSON, nullable=True)
    
    # Account data (what was purchased)
    traffic_amount = Column(Integer, nullable=True)
    duration_days = Column(Integer, nullable=True)
    server_id = Column(Integer, nullable=True)
    inbound_id = Column(Integer, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="payments")
    plan = relationship("PaymentPlan", back_populates="payments")
    payment_method = relationship("PaymentMethod", back_populates="payments")
    discount_code = relationship("DiscountCode", back_populates="payments")

    def __str__(self):
        return f"{self.user.username} - {self.amount} - {self.status}"

    def save(self, db):
        """Save payment with original amount"""
        if not self.original_amount and not self.id:
            self.original_amount = self.amount
        return super().save(db)

    def mark_as_completed(self, db, reference_code=None, tracking_code=None):
        """Mark payment as completed"""
        self.status = 'completed'
        self.payment_date = datetime.utcnow()
        if reference_code:
            self.reference_code = reference_code
        if tracking_code:
            self.tracking_code = tracking_code
        return self.save(db)

    def mark_as_failed(self, db, reason=None):
        """Mark payment as failed"""
        self.status = 'failed'
        if reason:
            self.description = reason
        return self.save(db)

    def mark_as_expired(self, db):
        """Mark payment as expired"""
        self.status = 'expired'
        return self.save(db)

    def mark_as_canceled(self, db, reason=None):
        """Mark payment as canceled"""
        self.status = 'canceled'
        if reason:
            self.description = reason
        return self.save(db)

    @property
    def is_paid(self):
        """Check if payment is paid"""
        return self.status == 'completed'

    @property
    def is_pending(self):
        """Check if payment is pending"""
        return self.status == 'pending'

    @property
    def is_expired(self):
        """Check if payment is expired"""
        return self.status == 'expired' or (self.expires_at and datetime.utcnow() > self.expires_at)
