"""
Backup schedule model for MoonVPN.

This module contains the SQLAlchemy model for managing backup schedules,
including scheduling configuration and retention policies.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Enum, JSON, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB

from core.database.base import Base
from core.database.models.user import User

class ScheduleType(str, Enum):
    """Types of backup schedules."""
    DAILY = 'daily'
    WEEKLY = 'weekly'
    MONTHLY = 'monthly'
    CUSTOM = 'custom'

class BackupSchedule(Base):
    """Model for backup schedules."""
    
    __tablename__ = "backup_schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    schedule_type = Column(Enum(ScheduleType), nullable=False)
    cron_expression = Column(String(100))
    is_active = Column(Boolean, default=True)
    retention_days = Column(Integer, default=30)
    max_backups = Column(Integer, default=10)
    backup_type = Column(String(50), nullable=False)
    storage_path = Column(String(512), nullable=False)
    metadata = Column(JSONB)
    created_by = Column(Integer, ForeignKey("users.id"))
    updated_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_run_at = Column(DateTime)
    next_run_at = Column(DateTime)
    
    # Relationships
    backups = relationship("SystemBackup", back_populates="schedule")
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "schedule_type": self.schedule_type,
            "cron_expression": self.cron_expression,
            "is_active": self.is_active,
            "retention_days": self.retention_days,
            "max_backups": self.max_backups,
            "backup_type": self.backup_type,
            "storage_path": self.storage_path,
            "metadata": self.metadata,
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_run_at": self.last_run_at.isoformat() if self.last_run_at else None,
            "next_run_at": self.next_run_at.isoformat() if self.next_run_at else None
        } 