from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Float, Text, DateTime, Enum, JSON
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
import uuid

from app.db.base import Base


class OrderStatus(enum.Enum):
    """Enumeration of possible order statuses"""
    PENDING = "pending"  # Order created, waiting for payment
    PAID = "paid"  # Payment received but not yet confirmed
    CONFIRMED = "confirmed"  # Payment confirmed, account created
    REJECTED = "rejected"  # Payment rejected by admin
    EXPIRED = "expired"  # Order expired (payment not received in time)
    CANCELED = "canceled"  # Order canceled by user or admin
    FAILED = "failed"  # Account creation failed
    VERIFICATION_PENDING = "verification_pending"  # Payment proof submitted, waiting for admin verification


class PaymentMethod(enum.Enum):
    """Enumeration of supported payment methods"""
    CARD_TO_CARD = "card_to_card"  # Manual card-to-card transfer
    WALLET = "wallet"  # Internal wallet
    ZARINPAL = "zarinpal"  # Zarinpal payment
    CRYPTO = "crypto"  # Cryptocurrency payment
    MANUAL = "manual"  # Manual payment (marked as paid by admin)


class Order(Base):
    """Order model for tracking user purchases and their status"""
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String(36), unique=True, index=True, nullable=False, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    plan_id = Column(Integer, ForeignKey("plans.id", ondelete="SET NULL"), nullable=True)
    panel_id = Column(Integer, ForeignKey("panels.id", ondelete="SET NULL"), nullable=True)
    inbound_id = Column(Integer, nullable=True)  # ID of the inbound on the panel

    # V2Ray configuration details (when confirmed)
    client_uuid = Column(String(36), nullable=True)  # UUID generated for client
    client_email = Column(String(100), nullable=True)  # Email/remark for client
    
    # Subscription reference
    # Uncomment the ForeignKey
    subscription_id = Column(Integer, ForeignKey("subscriptions.id", ondelete="SET NULL"), nullable=True) 
    
    # Basic order information
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING, nullable=False)
    payment_method = Column(Enum(PaymentMethod), nullable=True)
    payment_reference = Column(String(255), nullable=True)
    payment_authority = Column(String(50), nullable=True, index=True) # Zarinpal authority token
    payment_proof = Column(String(255), nullable=True) # Path or identifier for proof image
    
    # Enhanced payment proof fields
    payment_proof_img_url = Column(String(512), nullable=True) # Full URL to access the proof image
    payment_proof_submitted_at = Column(DateTime(timezone=True), nullable=True)
    payment_verified_at = Column(DateTime, nullable=True, index=True)  # When the proof was verified
    payment_verification_admin_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)  # Admin who verified the proof
    payment_rejection_reason = Column(Text, nullable=True)  # Reason for rejection if applicable
    payment_proof_telegram_msg_id = Column(String(50), nullable=True)  # Telegram message ID containing the proof
    
    # Financial information
    amount = Column(Float, nullable=False)  # Original price
    discount_amount = Column(Float, default=0.0, nullable=False)  # Discount amount
    final_amount = Column(Float, nullable=False)  # Final price after discount
    discount_code = Column(String(50), nullable=True)  # Discount code used
    
    # Configuration details
    config_protocol = Column(String(20), nullable=True)  # vless, vmess, trojan, etc.
    config_days = Column(Integer, nullable=True)  # Validity period in days
    config_traffic_gb = Column(Integer, nullable=True)  # Traffic limit in GB
    config_details = Column(JSON, nullable=True)  # JSON for additional config details
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    paid_at = Column(DateTime, nullable=True)
    confirmed_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)  # When the account will expire
    
    # Admin notes
    admin_note = Column(Text, nullable=True)
    admin_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)  # Admin who processed the order
    
    # Relationships
    user = relationship("User", back_populates="orders", foreign_keys=[user_id])
    plan = relationship("Plan", back_populates="orders")
    panel = relationship("Panel", back_populates="orders")
    subscription = relationship("Subscription", back_populates="orders")
    admin = relationship("User", foreign_keys=[admin_id])
    payment_verification_admin = relationship("User", foreign_keys=[payment_verification_admin_id])
    transactions = relationship("Transaction", back_populates="order")
    
    # Affiliate commissions relationship
    commissions = relationship("AffiliateCommission", back_populates="order")
    
    def __str__(self):
        return f"Order {self.order_id} - {self.status.value}"

    def __repr__(self):
        return f"<Order {self.order_id}>" 