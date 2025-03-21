"""
Backup models for MoonVPN.

This module contains the SQLAlchemy models for managing system backups,
including backup records, schedules, and storage management.
"""

from enum import Enum as PyEnum
from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database.base import Base

class BackupType(str, PyEnum):
    """Types of system backups."""
    FULL = 'full'
    INCREMENTAL = 'incremental'
    DIFFERENTIAL = 'differential'

class BackupStatus(str, PyEnum):
    """Status of system backups."""
    PENDING = 'pending'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'
    FAILED = 'failed'
    VERIFIED = 'verified'
    DELETED = 'deleted'

class StorageProvider(str, PyEnum):
    """Available storage providers."""
    LOCAL = 'local'
    S3 = 's3'
    AZURE = 'azure'
    GCS = 'gcs'

class SystemBackup(Base):
    """Model for storing system backup records."""
    
    __tablename__ = "system_backups"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    backup_type = Column(Enum(BackupType), nullable=False)
    status = Column(Enum(BackupStatus), nullable=False, default=BackupStatus.PENDING)
    storage_provider = Column(Enum(StorageProvider), nullable=False, default=StorageProvider.LOCAL)
    storage_path = Column(String(1024), nullable=False)
    file_size = Column(Integer)  # Size in bytes
    checksum = Column(String(64))  # SHA-256 hash
    error_message = Column(Text)
    metadata = Column(JSON)  # Additional backup metadata
    
    # Backup schedule reference
    schedule_id = Column(Integer, ForeignKey('backup_schedules.id'), nullable=True)
    schedule = relationship("BackupSchedule", back_populates="backups")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    verified_at = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True))
    
    # User references
    created_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    updated_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    verified_by = Column(Integer, ForeignKey('users.id'))
    
    def __str__(self):
        return f"<SystemBackup {self.name} ({self.backup_type})>"

class BackupSchedule(Base):
    """Model for managing backup schedules."""
    
    __tablename__ = "backup_schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    backup_type = Column(Enum(BackupType), nullable=False)
    storage_provider = Column(Enum(StorageProvider), nullable=False, default=StorageProvider.LOCAL)
    storage_path = Column(String(1024), nullable=False)
    cron_expression = Column(String(100), nullable=False)  # Cron schedule expression
    retention_days = Column(Integer, nullable=False, default=30)
    max_backups = Column(Integer, nullable=False, default=10)
    is_active = Column(Boolean, default=True)
    
    # Schedule metadata
    last_run_at = Column(DateTime(timezone=True))
    next_run_at = Column(DateTime(timezone=True))
    error_count = Column(Integer, default=0)
    last_error = Column(Text)
    metadata = Column(JSON)  # Additional schedule metadata
    
    # Relationships
    backups = relationship("SystemBackup", back_populates="schedule")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # User references
    created_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    updated_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    def __str__(self):
        return f"<BackupSchedule {self.name} ({self.backup_type})>" 