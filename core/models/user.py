"""
User model for the MoonVPN application.

This module defines the User model and its relationships with other models.
"""

from decimal import Decimal
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, DECIMAL, BigInteger, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.database import Base
from core.config import settings

class RoleName(str, Enum):
    ADMIN = "ADMIN"
    SELLER = "SELLER"
    USER = "USER"

class User(Base):
    """
    User model representing a Telegram user in the system.
    
    Attributes:
        id (int): Primary key
        telegram_id (int): Telegram user ID
        username (str): Telegram username
        full_name (str): User's full name
        phone (str): User's phone number
        email (str): User's email address
        role_id (int): Foreign key to roles table
        balance (Decimal): User's account balance
        is_banned (bool): Whether the user is banned
        is_active (bool): Whether the user is active
        referral_code (str): User's unique referral code
        referred_by_id (int): ID of the user who referred this user
        lang (str): User's preferred language
        last_login (datetime): When the user last logged in
        login_ip (str): IP address of the user's last login
        created_at (datetime): When the user was created
        updated_at (datetime): When the user was last updated
    """
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=False)
    username = Column(String(255), unique=True)
    full_name = Column(String(255))
    phone = Column(String(20), unique=True)
    email = Column(String(255), unique=True)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    balance = Column(DECIMAL(10, 2), nullable=False)
    is_banned = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    referral_code = Column(String(20), unique=True)
    referred_by_id = Column(Integer, ForeignKey("users.id"))
    lang = Column(String(10), default=settings.DEFAULT_LANGUAGE)
    last_login = Column(DateTime)
    login_ip = Column(String(45))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    role = relationship("Role", back_populates="users")
    referred_by = relationship("User", remote_side=[id], backref="referrals")
    panels = relationship("Panel", back_populates="created_by_user")
    
    def __repr__(self) -> str:
        """String representation of the User model."""
        return f"<User {self.username or self.telegram_id}>" 