"""
Chat-related models for MoonVPN.
Defines live chat sessions, messages, operators, and ratings.
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Enum, JSON, Text
from sqlalchemy.orm import relationship
import enum

from .base import BaseModel

class ChatStatus(enum.Enum):
    """Chat session status."""
    ACTIVE = "active"
    CLOSED = "closed"
    ARCHIVED = "archived"

class MessageType(enum.Enum):
    """Chat message types."""
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    SYSTEM = "system"

class LiveChatSession(BaseModel):
    """
    Live chat session model.
    Represents a chat session between a user and an operator.
    """
    
    status = Column(Enum(ChatStatus), default=ChatStatus.ACTIVE, nullable=False)
    is_active = Column(Boolean, default=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    subject = Column(String(200), nullable=True)
    priority = Column(Integer, default=0)
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    user = relationship("User", back_populates="chat_sessions")
    operator_id = Column(Integer, ForeignKey("livechatoperator.id"), nullable=True)
    operator = relationship("LiveChatOperator", back_populates="sessions")
    messages = relationship("LiveChatMessage", back_populates="session", cascade="all, delete-orphan")
    rating = relationship("LiveChatRating", back_populates="session", uselist=False, cascade="all, delete-orphan")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.start_time:
            self.start_time = datetime.utcnow()
    
    def close(self) -> None:
        """Close chat session."""
        self.status = ChatStatus.CLOSED
        self.is_active = False
        self.end_time = datetime.utcnow()
    
    def archive(self) -> None:
        """Archive chat session."""
        self.status = ChatStatus.ARCHIVED
        self.is_active = False
        if not self.end_time:
            self.end_time = datetime.utcnow()
    
    def get_duration(self) -> int:
        """Get chat duration in seconds."""
        end = self.end_time or datetime.utcnow()
        return int((end - self.start_time).total_seconds())
    
    def get_message_count(self) -> int:
        """Get total number of messages in session."""
        return len(self.messages)

class LiveChatMessage(BaseModel):
    """
    Live chat message model.
    Represents a message in a chat session.
    """
    
    content = Column(Text, nullable=False)
    type = Column(Enum(MessageType), default=MessageType.TEXT, nullable=False)
    is_read = Column(Boolean, default=False)
    read_time = Column(DateTime, nullable=True)
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    session_id = Column(Integer, ForeignKey("livechatsession.id"), nullable=False)
    session = relationship("LiveChatSession", back_populates="messages")
    sender_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    sender = relationship("User")
    
    def mark_as_read(self) -> None:
        """Mark message as read."""
        self.is_read = True
        self.read_time = datetime.utcnow()
    
    def __repr__(self) -> str:
        return f"<LiveChatMessage(type='{self.type.value}', content='{self.content[:50]}...')>"

class LiveChatOperator(BaseModel):
    """
    Live chat operator model.
    Represents a customer support operator.
    """
    
    is_active = Column(Boolean, default=True)
    max_sessions = Column(Integer, default=5)
    current_sessions = Column(Integer, default=0)
    average_rating = Column(Integer, default=0)
    total_sessions = Column(Integer, default=0)
    last_active = Column(DateTime, nullable=True)
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    user = relationship("User")
    sessions = relationship("LiveChatSession", back_populates="operator")
    
    def can_accept_new_session(self) -> bool:
        """Check if operator can accept new sessions."""
        return self.is_active and self.current_sessions < self.max_sessions
    
    def update_rating(self, rating: int) -> None:
        """Update operator's average rating."""
        self.total_sessions += 1
        self.average_rating = ((self.average_rating * (self.total_sessions - 1)) + rating) / self.total_sessions
    
    def update_activity(self) -> None:
        """Update operator's last active time."""
        self.last_active = datetime.utcnow()

class LiveChatRating(BaseModel):
    """
    Live chat rating model.
    Represents a user's rating of a chat session.
    """
    
    rating = Column(Integer, nullable=False)  # 1-5
    comment = Column(Text, nullable=True)
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    session_id = Column(Integer, ForeignKey("livechatsession.id"), nullable=False)
    session = relationship("LiveChatSession", back_populates="rating")
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    user = relationship("User")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.rating < 1:
            self.rating = 1
        elif self.rating > 5:
            self.rating = 5
    
    def __repr__(self) -> str:
        return f"<LiveChatRating(rating={self.rating})>" 