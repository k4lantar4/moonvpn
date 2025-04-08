from sqlalchemy import (Column, Integer, String, DateTime, ForeignKey, DECIMAL, Text)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from api.models.base import Base

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=False)
    payment_method = Column(String(50), nullable=False)
    amount = Column(DECIMAL(10, 2), nullable=False)
    discount_amount = Column(DECIMAL(10, 2), default=0)
    final_amount = Column(DECIMAL(10, 2), nullable=False)
    status = Column(String(20), nullable=False)  # pending, completed, failed, cancelled
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    user = relationship("User", back_populates="orders")
    plan = relationship("Plan", back_populates="orders")
    payments = relationship("Payment", back_populates="order")
    clients = relationship("Client", back_populates="order")
    
    def __repr__(self):
        return f"<Order(id={self.id}, user_id={self.user_id}, amount={self.final_amount}, status={self.status})>"

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(DECIMAL(10, 2), nullable=False)
    type = Column(String(20), nullable=False)  # deposit, withdraw, purchase, refund, commission
    reference_id = Column(Integer, nullable=True)  # Reference to payment_id or order_id
    description = Column(Text, nullable=True)
    balance_after = Column(DECIMAL(10, 2), nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="transactions")
    
    def __repr__(self):
        return f"<Transaction(id={self.id}, user_id={self.user_id}, amount={self.amount}, type={self.type})>"

class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    amount = Column(DECIMAL(10, 2), nullable=False)
    payment_method = Column(String(50), nullable=False)
    payment_gateway_id = Column(String(100), nullable=True)
    card_number = Column(String(20), nullable=True)
    tracking_code = Column(String(100), nullable=True)
    receipt_image = Column(String(255), nullable=True)
    status = Column(String(20), nullable=False)  # pending, verified, rejected
    admin_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    verification_notes = Column(Text, nullable=True)
    verified_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    user = relationship("User", foreign_keys=[user_id], back_populates="user_payments")
    admin = relationship("User", foreign_keys=[admin_id], back_populates="admin_verified_payments")
    order = relationship("Order", back_populates="payments")
    
    def __repr__(self):
        return f"<Payment(id={self.id}, user_id={self.user_id}, amount={self.amount}, status={self.status})>"

class BankCard(Base):
    __tablename__ = "bank_cards"
    
    id = Column(Integer, primary_key=True, index=True)
    bank_name = Column(String(100), nullable=False)
    card_number = Column(String(20), nullable=False)
    account_number = Column(String(30), nullable=True)
    owner_name = Column(String(100), nullable=False)
    is_active = Column(Integer, default=1)
    rotation_priority = Column(Integer, default=0)
    last_used = Column(DateTime, nullable=True)
    daily_limit = Column(DECIMAL(15, 2), nullable=True)
    monthly_limit = Column(DECIMAL(15, 2), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<BankCard(id={self.id}, bank_name={self.bank_name}, card_number={self.card_number})>" 