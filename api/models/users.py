import enum
from datetime import datetime
from sqlalchemy import (Column, Integer, String, Boolean, DateTime, ForeignKey,
                        DECIMAL, BigInteger, Text, Enum)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from api.models.base import Base

class RoleName(enum.Enum):
    ADMIN = "admin"
    SELLER = "seller"
    USER = "user"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=False)
    username = Column(String(255), unique=True, nullable=True)
    full_name = Column(String(255), nullable=True) # Made nullable initially
    phone = Column(String(20), unique=True, nullable=True) # Phone verification later
    email = Column(String(255), unique=True, nullable=True)

    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    balance = Column(DECIMAL(10, 2), nullable=False, default=0.00)
    is_banned = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True) # Added for soft delete/activation

    referral_code = Column(String(20), unique=True, nullable=True)
    referred_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    lang = Column(String(10), default='fa')
    last_login = Column(DateTime, nullable=True)
    login_ip = Column(String(45), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    role = relationship("Role", back_populates="users")
    referred_by = relationship("User", remote_side=[id], backref="referrals")
    panels_created = relationship("Panel", back_populates="created_by_user") # If tracking creator
    clients = relationship("Client", back_populates="user")
    orders = relationship("Order", back_populates="user")
    transactions = relationship("Transaction", back_populates="user")
    payments = relationship("Payment", back_populates="user")
    payments_verified = relationship("Payment", foreign_keys="[Payment.admin_id]", back_populates="admin")

    def __repr__(self):
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, role={self.role.name if self.role else None})>"

class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(Enum(RoleName), unique=True, nullable=False)
    description = Column(Text, nullable=True)

    # Permissions - Add more granular permissions as needed
    can_manage_panels = Column(Boolean, default=False)
    can_manage_users = Column(Boolean, default=False)
    can_manage_plans = Column(Boolean, default=False)
    can_approve_payments = Column(Boolean, default=False)
    can_broadcast = Column(Boolean, default=False)
    
    # Additional fields for role types
    is_admin = Column(Boolean, default=False)
    is_seller = Column(Boolean, default=False)

    discount_percent = Column(Integer, default=0) # For sellers
    commission_percent = Column(Integer, default=0) # For sellers

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    users = relationship("User", back_populates="role")

    def __repr__(self):
        return f"<Role(id={self.id}, name={self.name})>" 