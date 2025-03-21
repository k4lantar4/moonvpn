"""
User model for managing user accounts and authentication.
"""

from typing import Optional, List, Dict, Any
from sqlalchemy import String, Integer, Boolean, Enum, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
import enum

from ..base import BaseModel

class UserStatus(str, enum.Enum):
    """User status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    BANNED = "banned"

class User(BaseModel):
    """
    User model for managing user accounts.
    
    Attributes:
        username: User username
        email: User email
        password_hash: Hashed password
        status: User status
        is_active: Whether the user is active
        is_verified: Whether the user is verified
        last_login: Last login timestamp
        group_id: Reference to user group
        metadata: Additional user data
    """
    
    # User identification
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # User details
    status: Mapped[UserStatus] = mapped_column(Enum(UserStatus), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_login: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    
    # References
    group_id: Mapped[Optional[int]] = mapped_column(ForeignKey("group.id"), nullable=True)
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    # Relationships
    group: Mapped[Optional["Group"]] = relationship(back_populates="users")
    vpn_accounts: Mapped[List["VPNAccount"]] = relationship(back_populates="user")
    points: Mapped[Optional["UserPoints"]] = relationship(back_populates="user")
    transactions: Mapped[List["PointsTransaction"]] = relationship(back_populates="user")
    chat_sessions: Mapped[List["ChatSession"]] = relationship(back_populates="user")
    logs: Mapped[List["SystemLog"]] = relationship(back_populates="user")
    configs: Mapped[List["SystemConfig"]] = relationship(back_populates="user")
    
    def __repr__(self) -> str:
        """String representation of the user."""
        return f"<User(username={self.username}, email={self.email})>" 