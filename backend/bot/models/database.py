"""
Database models for the V2Ray management system.
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.dialects.postgresql import UUID
import uuid

Base = declarative_base()

class Server(Base):
    """Server model for V2Ray servers."""
    __tablename__ = 'servers'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    host = Column(String, nullable=False)
    port = Column(Integer, nullable=False)
    panel_url = Column(String, nullable=False)
    panel_username = Column(String, nullable=False)
    panel_password = Column(String, nullable=False)
    status = Column(String, nullable=False)
    last_sync = Column(DateTime, nullable=False)
    traffic_used = Column(Integer, default=0)
    traffic_total = Column(Integer, default=0)
    uptime = Column(Float, default=0.0)
    load = Column(Float, default=0.0)
    memory_used = Column(Float, default=0.0)
    memory_total = Column(Float, default=0.0)
    disk_used = Column(Float, default=0.0)
    disk_total = Column(Float, default=0.0)
    tags = Column(JSON, default=list)
    location = Column(String, nullable=False)
    bandwidth_limit = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Card(Base):
    """Card model for payment tracking."""
    __tablename__ = 'cards'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_name = Column(String, nullable=False)
    card_number = Column(String, nullable=False)
    bank_name = Column(String, nullable=False)
    is_verified = Column(Boolean, default=False)
    last_used = Column(DateTime, nullable=False)
    total_transactions = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    payments_from = relationship("Payment", foreign_keys="Payment.from_card_id", back_populates="from_card")
    payments_to = relationship("Payment", foreign_keys="Payment.to_card_id", back_populates="to_card")

class Payment(Base):
    """Payment model for transaction tracking."""
    __tablename__ = 'payments'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    amount = Column(Float, nullable=False)
    currency = Column(String, nullable=False)
    status = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    from_card_id = Column(UUID(as_uuid=True), ForeignKey('cards.id'), nullable=False)
    to_card_id = Column(UUID(as_uuid=True), ForeignKey('cards.id'), nullable=False)
    description = Column(String)
    receipt_image = Column(String)
    verified_by = Column(String)
    verified_at = Column(DateTime)
    rejection_reason = Column(String)
    points_earned = Column(Integer, default=0)
    is_points_payment = Column(Boolean, default=False)
    
    from_card = relationship("Card", foreign_keys=[from_card_id], back_populates="payments_from")
    to_card = relationship("Card", foreign_keys=[to_card_id], back_populates="payments_to")

class UserPoints(Base):
    """User points model for rewards system."""
    __tablename__ = 'user_points'
    
    user_id = Column(String, primary_key=True)
    total_points = Column(Integer, default=0)
    available_points = Column(Integer, default=0)
    vip_level = Column(String, nullable=False)
    last_activity = Column(DateTime, nullable=False)
    referral_code = Column(String, unique=True)
    referred_by = Column(String)
    referral_count = Column(Integer, default=0)
    total_earned = Column(Integer, default=0)
    total_spent = Column(Integer, default=0)
    total_expired = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    transactions = relationship("PointsTransaction", back_populates="user")

class PointsTransaction(Base):
    """Points transaction model."""
    __tablename__ = 'points_transactions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, ForeignKey('user_points.user_id'), nullable=False)
    amount = Column(Integer, nullable=False)
    type = Column(String, nullable=False)
    source = Column(String, nullable=False)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    
    user = relationship("UserPoints", back_populates="transactions")

class ChatSession(Base):
    """Chat session model for live support."""
    __tablename__ = 'chat_sessions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, nullable=False)
    agent_id = Column(String)
    status = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_message_at = Column(DateTime, nullable=False)
    tags = Column(JSON, default=list)
    priority = Column(Integer, default=1)
    category = Column(String, nullable=False)
    notes = Column(JSON, default=list)
    rating = Column(Integer)
    feedback = Column(String)
    resolution_time = Column(Float)
    transfer_count = Column(Integer, default=0)
    
    messages = relationship("ChatMessage", back_populates="chat")

class ChatMessage(Base):
    """Chat message model."""
    __tablename__ = 'chat_messages'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chat_id = Column(UUID(as_uuid=True), ForeignKey('chat_sessions.id'), nullable=False)
    user_id = Column(String, nullable=False)
    role = Column(String, nullable=False)
    content = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_read = Column(Boolean, default=False)
    attachments = Column(JSON, default=list)
    metadata = Column(JSON, default=dict)
    
    chat = relationship("ChatSession", back_populates="messages")

class AgentInfo(Base):
    """Support agent information model."""
    __tablename__ = 'agents'
    
    user_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    is_available = Column(Boolean, default=True)
    active_chats = Column(JSON, default=list)
    total_chats = Column(Integer, default=0)
    avg_rating = Column(Float, default=0.0)
    response_time = Column(Float, default=0.0)
    resolution_rate = Column(Float, default=0.0)
    specialties = Column(JSON, default=list)
    working_hours = Column(JSON, default=dict)
    last_active = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow) 