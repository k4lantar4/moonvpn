"""
ChatMessage model for managing chat messages and their content.
"""

from typing import Optional, List
from sqlalchemy import String, Integer, Boolean, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
import enum

from ..base import BaseModel

class MessageType(str, enum.Enum):
    """Message type enumeration."""
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    SYSTEM = "system"
    CUSTOM = "custom"

class MessageStatus(str, enum.Enum):
    """Message status enumeration."""
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"

class ChatMessage(BaseModel):
    """
    ChatMessage model for managing chat messages.
    
    Attributes:
        session_id: Reference to chat session
        type: Message type
        status: Message status
        content: Message content
        sender_id: Reference to sender
        reply_to_id: Reference to replied message
        is_edited: Whether the message was edited
        edited_at: Message edit timestamp
        metadata: Additional message data
    """
    
    # Message identification
    session_id: Mapped[int] = mapped_column(ForeignKey("chat_session.id"), nullable=False)
    type: Mapped[MessageType] = mapped_column(Enum(MessageType), nullable=False)
    status: Mapped[MessageStatus] = mapped_column(Enum(MessageStatus), nullable=False)
    
    # Message content
    content: Mapped[str] = mapped_column(String(5000), nullable=False)
    sender_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    reply_to_id: Mapped[Optional[int]] = mapped_column(ForeignKey("chat_message.id"), nullable=True)
    
    # Message tracking
    is_edited: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    edited_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    
    # Additional data
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    # Relationships
    session: Mapped["ChatSession"] = relationship(back_populates="messages")
    sender: Mapped["User"] = relationship()
    reply_to: Mapped[Optional["ChatMessage"]] = relationship(remote_side=[id])
    
    def __repr__(self) -> str:
        """String representation of the chat message."""
        return f"<ChatMessage(type={self.type}, status={self.status})>" 