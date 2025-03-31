from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, BigInteger, DECIMAL, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.session import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=False)
    telegram_username = Column(String(100), nullable=True)
    phone_number = Column(String(20), index=True, nullable=True)
    first_name = Column(String(100), nullable=True)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    wallet_balance = Column(DECIMAL(10, 2), nullable=False, default=0.00)
    is_iranian_verified = Column(Boolean, default=False)
    joined_channel = Column(Boolean, default=False)
    free_trial_used = Column(Boolean, default=False)
    is_blocked = Column(Boolean, default=False)
    referrer_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship (Many-to-One: User to Role)
    role = relationship("Role", back_populates="users")

    # Relationship (One-to-Many: User to Referrals)
    referrals = relationship("User", backref="referrer", remote_side=[id]) # Relationship to users referred by this user

    # Add relationships to other tables like Orders, Subscriptions, etc. later
    # orders = relationship("Order", back_populates="user")
    # subscriptions = relationship("Subscription", back_populates="user") 