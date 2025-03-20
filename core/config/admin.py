"""
Admin group models for MoonVPN.

This module provides SQLAlchemy models for admin groups and their members in the database.
"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum, ARRAY, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database.base import Base

class AdminGroupType(str, Enum):
    """Enum for admin group types."""
    MANAGE = "manage"  # Full management access
    REPORTS = "reports"  # Access to reports and analytics
    LOGS = "logs"  # Access to system logs
    TRANSACTIONS = "transactions"  # Access to transaction management
    OUTAGES = "outages"  # Access to outage management
    SELLERS = "sellers"  # Access to seller management
    BACKUPS = "backups"  # Access to backup management

class NotificationLevel(str, Enum):
    """Enum for notification levels."""
    CRITICAL = "critical"  # Critical system issues
    ERROR = "error"  # Error notifications
    WARNING = "warning"  # Warning notifications
    INFO = "info"  # General information
    DEBUG = "debug"  # Debug information

class AdminGroup(Base):
    """Model for admin groups."""
    
    __tablename__ = "admin_groups"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    type = Column(Enum(AdminGroupType), nullable=False)
    chat_id = Column(Integer, nullable=True, unique=True)
    icon = Column(String(10), nullable=True)
    notification_level = Column(
        Enum(NotificationLevel),
        nullable=False,
        default=NotificationLevel.INFO
    )
    notification_types = Column(ARRAY(String), nullable=False, default=list)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
    
    # Relationships
    members = relationship(
        "AdminGroupMember",
        back_populates="group",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        """String representation of the admin group."""
        return f"<AdminGroup {self.name} ({self.type})>"

class AdminGroupMember(Base):
    """Model for admin group members."""
    
    __tablename__ = "admin_group_members"
    
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("admin_groups.id", ondelete="CASCADE"))
    user_id = Column(Integer, nullable=False)
    role = Column(String(50), nullable=False, default="member")
    is_active = Column(Boolean, nullable=False, default=True)
    added_by = Column(Integer, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
    
    # Relationships
    group = relationship("AdminGroup", back_populates="members")
    
    # Indexes
    __table_args__ = (
        Index('idx_group_user', 'group_id', 'user_id', unique=True),
    )
    
    def __repr__(self) -> str:
        """String representation of the group member."""
        return f"<AdminGroupMember {self.user_id} in group {self.group_id}>" 