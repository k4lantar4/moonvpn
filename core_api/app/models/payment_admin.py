from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime, Float, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import Base


class PaymentAdminAssignment(Base):
    """
    Model for assigning payment admins to bank cards and Telegram groups.
    
    This model tracks which admin users are responsible for verifying payments
    made to which bank cards, and in which Telegram groups they should receive
    notifications for verification.
    """
    __tablename__ = "payment_admin_assignments"

    id = Column(Integer, primary_key=True, index=True)
    
    # User (admin) who is assigned to verify payments
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Bank card that this admin is responsible for (optional - can be responsible for multiple)
    bank_card_id = Column(Integer, ForeignKey("bank_cards.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Telegram group ID where payment notifications should be sent
    telegram_group_id = Column(String(100), nullable=True)
    
    # Status and limits
    is_active = Column(Boolean, default=True, nullable=False)
    daily_limit = Column(Integer, nullable=True)  # Maximum payments to process per day
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_assignment_date = Column(DateTime, nullable=True)  # When was the admin last assigned to verify a payment
    
    # Relationships
    user = relationship("User", back_populates="payment_admin_assignments")
    bank_card = relationship("BankCard")
    
    def __str__(self):
        card_info = f" - Card: {self.bank_card.card_number[-4:]}" if self.bank_card else ""
        group_info = f" - Group: {self.telegram_group_id}" if self.telegram_group_id else ""
        status = "Active" if self.is_active else "Inactive"
        return f"Admin: {self.user.username}{card_info}{group_info} ({status})"


class PaymentAdminMetrics(Base):
    """
    Model for tracking payment admin performance metrics.
    
    This model stores metrics about payment admin performance, such as response time,
    approval rate, and total processed payments, to help evaluate admin effectiveness.
    """
    __tablename__ = "payment_admin_metrics"

    id = Column(Integer, primary_key=True)
    
    # User (admin) whose metrics are being tracked
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, unique=True)
    
    # Performance metrics
    total_processed = Column(Integer, default=0, nullable=False)
    total_approved = Column(Integer, default=0, nullable=False)
    total_rejected = Column(Integer, default=0, nullable=False)
    avg_response_time_seconds = Column(Float, nullable=True)
    
    # Timestamps
    last_processed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="payment_admin_metrics")
    
    def __str__(self):
        approval_rate = (self.total_approved / self.total_processed * 100) if self.total_processed > 0 else 0
        return f"Admin: {self.user.username} - Processed: {self.total_processed} - Approval Rate: {approval_rate:.1f}%"
