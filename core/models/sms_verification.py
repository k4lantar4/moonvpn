"""
SMS verification model for MoonVPN.

This module defines the database model for storing SMS verification
codes and tracking verification attempts.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database.base import Base

class SMSVerification(Base):
    """Model for storing SMS verification codes."""
    
    __tablename__ = "sms_verifications"
    
    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String(20), nullable=False, index=True)
    code = Column(String(10), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    attempts = Column(Integer, default=0)
    is_used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    verified_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="sms_verifications")
    
    def __str__(self):
        return f"<SMSVerification {self.phone}>"
    
    def is_expired(self) -> bool:
        """Check if verification code has expired."""
        return datetime.utcnow() > self.expires_at
    
    def is_valid(self) -> bool:
        """Check if verification code is still valid."""
        return not self.is_used and not self.is_expired() and self.attempts < 3
    
    def increment_attempts(self) -> None:
        """Increment verification attempts."""
        self.attempts += 1
    
    def mark_as_used(self) -> None:
        """Mark verification code as used."""
        self.is_used = True
        self.verified_at = datetime.utcnow() 