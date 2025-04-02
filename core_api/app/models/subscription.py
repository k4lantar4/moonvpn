from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Text, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base_class import Base

class Subscription(Base):
    """
    Subscription model for tracking user subscriptions, including status settings.
    Links to a user and keeps track of their subscription preferences.
    """
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=False)
    
    # Order reference - the order that created this subscription
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    
    # Panel information
    panel_id = Column(Integer, ForeignKey("panels.id"), nullable=True)
    inbound_id = Column(Integer, nullable=True)
    client_uuid = Column(String(36), nullable=True)  # UUID used on the panel
    client_email = Column(String(100), nullable=True)  # Email/remark used on the panel
    
    # Service configuration
    config_traffic_gb = Column(Integer, nullable=True)  # Traffic limit in GB
    
    # Subscription status
    status = Column(String(20), default="active")  # active, expired, cancelled, frozen
    
    # Freeze functionality
    is_frozen = Column(Boolean, default=False)
    freeze_start_date = Column(DateTime, nullable=True)
    freeze_end_date = Column(DateTime, nullable=True)
    freeze_reason = Column(String(255), nullable=True)
    
    # Auto-renew functionality
    auto_renew = Column(Boolean, default=False)
    auto_renew_payment_method = Column(String(50), nullable=True)
    
    # User notes
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="subscriptions")
    plan = relationship("Plan", back_populates="subscriptions")
    client = relationship("Client", back_populates="subscription", uselist=False)
    panel = relationship("Panel", back_populates="subscriptions")
    order = relationship("Order", back_populates="subscription", foreign_keys=[order_id])
    
    def freeze(self, end_date=None, reason=None):
        """
        Freeze the subscription.
        
        Args:
            end_date: Date when the freeze should end (optional)
            reason: Reason for freezing (optional)
        """
        self.is_frozen = True
        self.freeze_start_date = datetime.utcnow()
        self.freeze_end_date = end_date
        self.freeze_reason = reason
        self.status = "frozen"
        
    def unfreeze(self):
        """
        Unfreeze the subscription.
        """
        self.is_frozen = False
        self.status = "active"
        
        # If there was time remaining when frozen, extend by the frozen duration
        if self.end_date and self.freeze_start_date:
            # Calculate frozen duration
            frozen_duration = datetime.utcnow() - self.freeze_start_date
            # Extend end date
            self.end_date = self.end_date + frozen_duration
        
        # Clear freeze-related fields
        self.freeze_start_date = None
        self.freeze_end_date = None
        self.freeze_reason = None
    
    def add_note(self, note_text):
        """
        Add a note to the subscription.
        
        Args:
            note_text: Text of the note to add
        """
        if not self.notes:
            self.notes = note_text
        else:
            # Add new note with timestamp
            timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            self.notes = f"{self.notes}\n\n--- {timestamp} ---\n{note_text}"
            
    def toggle_auto_renew(self, enabled, payment_method=None):
        """
        Toggle auto-renew setting.
        
        Args:
            enabled: Whether auto-renew should be enabled
            payment_method: Payment method to use for auto-renewal (optional)
        """
        self.auto_renew = enabled
        if enabled and payment_method:
            self.auto_renew_payment_method = payment_method 