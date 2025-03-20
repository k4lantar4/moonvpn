from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

class SystemBackupBase(BaseModel):
    type: str = Field(..., description="Type of backup (full, incremental, differential)")
    status: Optional[str] = Field(None, description="Status of backup (in_progress, completed, failed)")
    start_time: Optional[datetime] = Field(None, description="Start time of backup")
    end_time: Optional[datetime] = Field(None, description="End time of backup")
    size: Optional[int] = Field(None, description="Size of backup in bytes")
    path: Optional[str] = Field(None, description="Path to backup files")
    error_message: Optional[str] = Field(None, description="Error message if backup failed")

class SystemBackupCreate(SystemBackupBase):
    pass

class SystemBackupResponse(SystemBackupBase):
    id: int
    restore_status: Optional[str] = Field(None, description="Status of restore operation")
    restore_start_time: Optional[datetime] = Field(None, description="Start time of restore operation")
    restore_end_time: Optional[datetime] = Field(None, description="End time of restore operation")
    restore_error_message: Optional[str] = Field(None, description="Error message if restore failed")

    class Config:
        orm_mode = True

class BackupScheduleBase(BaseModel):
    backup_type: str = Field(..., description="Type of backup (full, incremental, differential)")
    schedule_type: str = Field(..., description="Type of schedule (daily, weekly, monthly)")
    is_active: bool = Field(True, description="Whether the schedule is active")
    retention_days: int = Field(30, description="Number of days to retain backups")
    last_run: Optional[datetime] = Field(None, description="Last time backup was run")
    next_run: Optional[datetime] = Field(None, description="Next scheduled backup time")
    settings: Optional[Dict[str, Any]] = Field(None, description="Additional schedule settings")

class BackupScheduleCreate(BackupScheduleBase):
    pass

class BackupScheduleResponse(BackupScheduleBase):
    id: int
    backup_id: Optional[int] = Field(None, description="ID of associated backup")

    class Config:
        orm_mode = True

class BackupRestoreRequest(BaseModel):
    force: bool = Field(False, description="Whether to force restore even if system is running")
    verify: bool = Field(True, description="Whether to verify backup integrity before restore")
    components: Optional[list[str]] = Field(None, description="List of components to restore")
    settings: Optional[Dict[str, Any]] = Field(None, description="Additional restore settings") 