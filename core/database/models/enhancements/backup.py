"""
System backup model for MoonVPN.

This module contains the SQLAlchemy model for managing system backups,
including backup scheduling, status tracking, and storage management.
"""

from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Enum, JSON, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime

from core.database.base import Base
from core.database.models.user import User

class BackupType(str, Enum):
    """Types of system backups."""
    FULL = 'full'
    INCREMENTAL = 'incremental'
    DIFFERENTIAL = 'differential'

class BackupStatus(str, Enum):
    """Status of backup operations."""
    PENDING = 'pending'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'
    FAILED = 'failed'
    VERIFIED = 'verified'
    EXPIRED = 'expired'

class SystemBackup(Base):
    """Model for system backups."""
    
    __tablename__ = "system_backups"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    backup_type = Column(Enum(BackupType), nullable=False)
    status = Column(Enum(BackupStatus), default=BackupStatus.PENDING)
    storage_path = Column(String(512), nullable=False)
    size_bytes = Column(Numeric)
    checksum = Column(String(64))
    metadata = Column(JSONB)
    schedule_id = Column(Integer, ForeignKey("backup_schedules.id"))
    created_by = Column(Integer, ForeignKey("users.id"))
    updated_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    verified_at = Column(DateTime)
    expires_at = Column(DateTime)
    error_message = Column(Text)
    
    # Relationships
    schedule = relationship("BackupSchedule", back_populates="backups")
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "backup_type": self.backup_type,
            "status": self.status,
            "storage_path": self.storage_path,
            "size_bytes": float(self.size_bytes) if self.size_bytes else None,
            "checksum": self.checksum,
            "metadata": self.metadata,
            "schedule_id": self.schedule_id,
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "verified_at": self.verified_at.isoformat() if self.verified_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "error_message": self.error_message
        } 