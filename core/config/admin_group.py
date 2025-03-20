from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from app.core.database.base import Base

class AdminGroup(Base):
    """Model for admin groups in the system."""
    __tablename__ = "admin_groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    chat_id = Column(Integer, unique=True, nullable=False)
    type = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(10), default="📊")
    notification_level = Column(String(20), default="normal")
    is_active = Column(Boolean, default=True)
    notification_types = Column(JSON, default=list)
    added_by = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    members = relationship("AdminGroupMember", back_populates="group", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<AdminGroup {self.name} ({self.type})>"

class AdminGroupMember(Base):
    """Model for admin group members."""
    __tablename__ = "admin_group_members"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("admin_groups.id", ondelete="CASCADE"))
    user_id = Column(Integer, nullable=False)
    role = Column(String(50), default="member")
    added_by = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    group = relationship("AdminGroup", back_populates="members")

    __table_args__ = (
        UniqueConstraint('group_id', 'user_id', name='uq_group_member'),
    )

    def __repr__(self):
        return f"<AdminGroupMember {self.user_id} ({self.role})>" 