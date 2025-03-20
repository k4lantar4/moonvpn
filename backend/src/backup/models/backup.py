from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class SystemBackup(Base):
    __tablename__ = "system_backups"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, nullable=False)  # full, incremental, differential
    status = Column(String, nullable=False)  # in_progress, completed, failed
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    size = Column(Integer)  # in bytes
    path = Column(String)
    error_message = Column(String)
    
    # Restore related fields
    restore_status = Column(String)  # in_progress, completed, failed
    restore_start_time = Column(DateTime)
    restore_end_time = Column(DateTime)
    restore_error_message = Column(String)
    
    # Relationships
    schedules = relationship("BackupSchedule", back_populates="backup")

class BackupSchedule(Base):
    __tablename__ = "backup_schedules"

    id = Column(Integer, primary_key=True, index=True)
    backup_type = Column(String, nullable=False)  # full, incremental, differential
    schedule_type = Column(String, nullable=False)  # daily, weekly, monthly
    is_active = Column(Boolean, default=True)
    retention_days = Column(Integer, default=30)
    last_run = Column(DateTime)
    next_run = Column(DateTime)
    settings = Column(JSON)  # Additional schedule settings
    
    # Foreign key
    backup_id = Column(Integer, ForeignKey("system_backups.id"))
    
    # Relationships
    backup = relationship("SystemBackup", back_populates="schedules") 