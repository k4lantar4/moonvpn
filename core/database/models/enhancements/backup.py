"""
SystemBackup model for managing system backups and restores.
"""

from typing import Optional, List
from sqlalchemy import String, Integer, Float, Boolean, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
import enum

from ..base import BaseModel

class BackupStatus(str, enum.Enum):
    """Backup status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    RESTORED = "restored"

class BackupType(str, enum.Enum):
    """Backup type enumeration."""
    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"

class SystemBackup(BaseModel):
    """
    SystemBackup model for managing system backups.
    
    Attributes:
        type: Backup type
        status: Backup status
        size: Backup size in bytes
        path: Backup file path
        started_at: Backup start timestamp
        completed_at: Backup completion timestamp
        error_message: Error message if failed
        metadata: Additional backup data
    """
    
    # Backup identification
    type: Mapped[BackupType] = mapped_column(Enum(BackupType), default=BackupType.FULL, nullable=False)
    status: Mapped[BackupStatus] = mapped_column(Enum(BackupStatus), default=BackupStatus.PENDING, nullable=False)
    
    # Backup details
    size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    path: Mapped[str] = mapped_column(String(255), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    def __repr__(self) -> str:
        """String representation of the system backup."""
        return f"<SystemBackup(type={self.type}, status={self.status})>" 