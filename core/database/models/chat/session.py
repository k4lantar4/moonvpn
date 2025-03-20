"""
ChatSession model for managing chat sessions and conversations.
"""

from typing import Optional, List
from sqlalchemy import String, Integer, Boolean, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
import enum

from ..base import BaseModel

class SessionStatus(str, enum.Enum):
    """Session status enumeration."""
    ACTIVE = "active"
    CLOSED = "closed"
    ARCHIVED = "archived"

class SessionType(str, enum.Enum):
    """Session type enumeration."""
    SUPPORT = "support"
    SALES = "sales"
    GENERAL = "general"
    CUSTOM = "custom"

class ChatSession(BaseModel):
    """
    ChatSession model for managing chat sessions.
    
    Attributes:
        user_id: Reference to user
        type: Session type
        status: Session status
        title: Session title
        description: Session description
        is_active: Whether the session is active
        started_at: Session start timestamp
        ended_at: Session end timestamp
        metadata: Additional session data
    """
    
    # Session identification
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    type: Mapped[SessionType] = mapped_column(Enum(SessionType), nullable=False)
    status: Mapped[SessionStatus] = mapped_column(Enum(SessionStatus), nullable=False)
    
    # Session details
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Session timing
    started_at: Mapped[datetime] = mapped_column(nullable=False)
    ended_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    
    # Additional data
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="chat_sessions")
    messages: Mapped[List["ChatMessage"]] = relationship(back_populates="session")
    
    def __repr__(self) -> str:
        """String representation of the chat session."""
        return f"<ChatSession(type={self.type}, title={self.title})>" 