from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import Base


class BankCard(Base):
    """Bank card model for managing payment card information"""
    __tablename__ = "bank_cards"

    id = Column(Integer, primary_key=True, index=True)
    
    # Bank information
    bank_name = Column(String(100), nullable=False, index=True)
    card_number = Column(String(20), nullable=False, index=True)
    card_holder_name = Column(String(100), nullable=False)
    account_number = Column(String(50), nullable=True)  # Optional account number
    sheba_number = Column(String(50), nullable=True)  # Optional SHEBA number
    
    # Status and metadata
    is_active = Column(Boolean, default=True, nullable=False)
    priority = Column(Integer, default=0, nullable=False)  # Higher means higher priority
    description = Column(Text, nullable=True)
    
    # Owner information
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="bank_cards")
    creator = relationship("User", foreign_keys=[created_by])
    
    def __str__(self):
        return f"{self.bank_name} - {self.card_number[-4:]} - {self.card_holder_name}" 