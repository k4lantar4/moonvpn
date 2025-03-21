"""
User model for MoonVPN.

This module defines the database model for storing user information
and managing user-related operations.
"""

from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property

from app.core.database.base import Base
from app.core.schemas.user import UserStatus

class User(Base):
    """Model for storing user information."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, nullable=True)
    phone = Column(String(20), unique=True, nullable=True)
    password_hash = Column(String(128))
    first_name = Column(String(50), nullable=True)
    last_name = Column(String(50), nullable=True)
    language = Column(String(5), default="en")
    timezone = Column(String(50), default="UTC")
    status = Column(SQLEnum(UserStatus), default=UserStatus.ACTIVE)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_phone_verified = Column(Boolean, default=False)
    is_email_verified = Column(Boolean, default=False)
    verification_code = Column(String(10), nullable=True)
    verification_code_expires = Column(DateTime, nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    subscriptions = relationship("Subscription", back_populates="user")
    vpn_accounts = relationship("VPNAccount", back_populates="user")
    transactions = relationship("Transaction", back_populates="user")
    sms_verifications = relationship("SMSVerification", back_populates="user")
    
    @hybrid_property
    def full_name(self) -> str:
        """Get user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.last_name or self.username
    
    def __init__(self, **kwargs):
        """Initialize user model."""
        super().__init__(**kwargs)
        if not self.language:
            self.language = "en"
    
    def verify_phone(self, code: str) -> bool:
        """Verify user's phone number with given code."""
        if not self.verification_code or not self.verification_code_expires:
            return False
        
        if datetime.utcnow() > self.verification_code_expires:
            return False
        
        if self.verification_code != code:
            return False
        
        self.is_phone_verified = True
        self.verification_code = None
        self.verification_code_expires = None
        return True
    
    def generate_verification_code(self) -> str:
        """Generate a new verification code."""
        import random
        self.verification_code = str(random.randint(100000, 999999))
        self.verification_code_expires = datetime.utcnow() + timedelta(minutes=10)
        return self.verification_code
    
    def update_login_attempt(self, success: bool) -> None:
        """Update login attempt counter."""
        if success:
            self.failed_login_attempts = 0
            self.last_login = datetime.utcnow()
        else:
            self.failed_login_attempts += 1
            if self.failed_login_attempts >= 5:
                self.status = UserStatus.SUSPENDED
    
    def has_active_subscription(self) -> bool:
        """Check if user has any active subscription."""
        return any(sub.is_active for sub in self.subscriptions)
    
    def get_active_vpn_account(self) -> Optional["VPNAccount"]:
        """Get user's active VPN account if any."""
        for account in self.vpn_accounts:
            if account.is_active:
                return account
        return None
    
    def __str__(self):
        """String representation of user."""
        return self.username 