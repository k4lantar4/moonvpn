"""Live chat models for managing chat sessions and messages."""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, Enum, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from .base import Base

class ChatSessionStatus(str, enum.Enum):
    """Chat session status."""
    ACTIVE = "active"
    CLOSED = "closed"
    ARCHIVED = "archived"
    WAITING = "waiting"

class LiveChatSession(Base):
    """Live chat session model."""
    
    __tablename__ = "livechatsession"
    
    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Session information
    status: Mapped[ChatSessionStatus] = mapped_column(
        Enum(ChatSessionStatus),
        default=ChatSessionStatus.WAITING,
        nullable=False
    )
    subject: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    # User relationship
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    operator_id: Mapped[Optional[int]] = mapped_column(ForeignKey("user.id"), nullable=True)
    
    # Timestamps
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="chat_sessions")
    operator = relationship("User", foreign_keys=[operator_id], back_populates="operator_sessions")
    messages = relationship(
        "LiveChatMessage",
        back_populates="session",
        lazy="selectin"
    )
    rating = relationship(
        "LiveChatRating",
        back_populates="session",
        uselist=False
    )
    
    def __repr__(self) -> str:
        """String representation of the chat session."""
        return f"<LiveChatSession {self.id} {self.status}>"
    
    def close(self) -> None:
        """Close the chat session."""
        self.status = ChatSessionStatus.CLOSED
        self.ended_at = datetime.now(self.started_at.tzinfo)
    
    def archive(self) -> None:
        """Archive the chat session."""
        self.status = ChatSessionStatus.ARCHIVED
        self.ended_at = datetime.now(self.started_at.tzinfo)

class LiveChatMessage(Base):
    """Live chat message model."""
    
    __tablename__ = "livechatmessage"
    
    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Message information
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_from_user: Mapped[bool] = mapped_column(Boolean, nullable=False)
    
    # Session relationship
    session_id: Mapped[int] = mapped_column(ForeignKey("livechatsession.id"), nullable=False)
    sender_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    
    # Timestamps
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    # Relationships
    session = relationship("LiveChatSession", back_populates="messages")
    sender = relationship("User", back_populates="messages")
    
    def __repr__(self) -> str:
        """String representation of the chat message."""
        return f"<LiveChatMessage {self.id} {self.is_from_user}>"

class LiveChatOperator(Base):
    """Live chat operator model."""
    
    __tablename__ = "livechatoperator"
    
    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Operator information
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    max_sessions: Mapped[int] = mapped_column(Integer, default=5)
    current_sessions: Mapped[int] = mapped_column(Integer, default=0)
    
    # Relationships
    user = relationship("User", back_populates="operator_profile")
    
    def __repr__(self) -> str:
        """String representation of the operator."""
        return f"<LiveChatOperator {self.user.username}>"

class LiveChatRating(Base):
    """Live chat rating model."""
    
    __tablename__ = "livechatrating"
    
    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Rating information
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Session relationship
    session_id: Mapped[int] = mapped_column(ForeignKey("livechatsession.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    # Relationships
    session = relationship("LiveChatSession", back_populates="rating")
    user = relationship("User")
    
    def __repr__(self) -> str:
        """String representation of the rating."""
        return f"<LiveChatRating {self.rating}>" 