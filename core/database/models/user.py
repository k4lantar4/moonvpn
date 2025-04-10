from datetime import datetime
from typing import List, Optional
import enum

from sqlalchemy import (
    String, Text, Boolean, Integer, DateTime, func, BigInteger,
    ForeignKey, Numeric
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database.session import Base
# from typing import TYPE_CHECKING
# if TYPE_CHECKING:
#     from .role import Role
#     from .client import Client
#     from .order import Order
#     from .payment import Payment
#     from .transaction import Transaction

class User(Base):
    """Model for users (customers, admins, sellers)."""
    
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), unique=True, nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), nullable=False)
    lang: Mapped[Optional[str]] = mapped_column(String(10), default=None, nullable=True)
    is_banned: Mapped[Optional[bool]] = mapped_column(Boolean, default=None, nullable=True)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, default=None, nullable=True)
    referral_code: Mapped[Optional[str]] = mapped_column(String(20), unique=True, nullable=True)
    referred_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    login_ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, default=None, nullable=True
    )
    
    # Relationships (Forward references as strings)
    role: Mapped["Role"] = relationship("Role", back_populates="users")
    referred_by: Mapped[Optional["User"]] = relationship("User", remote_side=[id], back_populates="referrals")
    referrals: Mapped[List["User"]] = relationship("User", back_populates="referred_by")
    payments = relationship("Payment", foreign_keys="[Payment.user_id]", back_populates="user")
    approved_payments = relationship("Payment", foreign_keys="[Payment.admin_id]", back_populates="admin")
    client_accounts = relationship("ClientAccount", back_populates="user", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="user", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    # created_discount_codes = relationship("DiscountCode", foreign_keys="[DiscountCode.created_by]", back_populates="creator") # Commented out temporarily
    created_panels = relationship("Panel", foreign_keys="[Panel.created_by_id]", back_populates="creator")
    # Add relationship for discount codes created by this user later
    # created_discount_codes = relationship("DiscountCode", back_populates="creator") 

    def __repr__(self) -> str:
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, username='{self.username}')>" 