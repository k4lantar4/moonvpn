import enum
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, Enum as SQLAlchemyEnum, func
from sqlalchemy.orm import relationship, Mapped, mapped_column

from core.database.session import Base

class RoleName(enum.Enum):
    ADMIN = "ADMIN"
    SELLER = "SELLER"
    USER = "USER"

class Role(Base):
    """Model for user roles and permissions."""
    
    __tablename__ = "roles"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[RoleName] = mapped_column(SQLAlchemyEnum(RoleName), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Permissions - using Boolean for simplicity, could use a separate permission model later
    can_manage_panels: Mapped[Optional[bool]] = mapped_column(Boolean, default=None, nullable=True)
    can_manage_users: Mapped[Optional[bool]] = mapped_column(Boolean, default=None, nullable=True)
    can_manage_plans: Mapped[Optional[bool]] = mapped_column(Boolean, default=None, nullable=True)
    can_approve_payments: Mapped[Optional[bool]] = mapped_column(Boolean, default=None, nullable=True)
    can_broadcast: Mapped[Optional[bool]] = mapped_column(Boolean, default=None, nullable=True)
    is_admin: Mapped[Optional[bool]] = mapped_column(Boolean, default=None, nullable=True) # Shortcut flag
    is_seller: Mapped[Optional[bool]] = mapped_column(Boolean, default=None, nullable=True) # Shortcut flag
    discount_percent: Mapped[Optional[int]] = mapped_column(Integer, default=None, nullable=True)
    commission_percent: Mapped[Optional[int]] = mapped_column(Integer, default=None, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, default=None, nullable=True
    )
    
    # Relationships
    users: Mapped[List["User"]] = relationship("User", back_populates="role")

    def __repr__(self) -> str:
        return f"<Role(id={self.id}, name='{self.name.value}')>"

    # users = relationship("User", back_populates="role") # Add this later when User model is updated 