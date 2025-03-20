"""
Group model for managing user groups and permissions.
"""

from typing import Optional, List, Dict, Any
from sqlalchemy import String, Integer, Boolean, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
import enum

from ..base import BaseModel

class GroupType(str, enum.Enum):
    """Group type enumeration."""
    ADMIN = "admin"
    MODERATOR = "moderator"
    USER = "user"
    CUSTOM = "custom"

class Group(BaseModel):
    """
    Group model for managing user groups.
    
    Attributes:
        type: Group type
        name: Group name
        description: Group description
        is_active: Whether the group is active
        permissions: Group permissions
        metadata: Additional group data
    """
    
    # Group identification
    type: Mapped[GroupType] = mapped_column(Enum(GroupType), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Group details
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    permissions: Mapped[List[str]] = mapped_column(JSON, nullable=False)
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    # Relationships
    users: Mapped[List["User"]] = relationship(back_populates="group")
    configs: Mapped[List["SystemConfig"]] = relationship(back_populates="group")
    
    def __repr__(self) -> str:
        """String representation of the group."""
        return f"<Group(type={self.type}, name={self.name})>" 