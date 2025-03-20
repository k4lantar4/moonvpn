"""
Pydantic schemas for MoonVPN enhancement models.

This module contains Pydantic models for validating and serializing data
related to system health, backups, notifications, reporting, logging,
configuration, and metrics.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum

from core.database.models.enhancements.backup import BackupType, BackupStatus
from core.database.models.enhancements.backup_schedule import ScheduleType

# Enum types
class ReportType(str, Enum):
    DAILY = 'daily'
    WEEKLY = 'weekly'
    MONTHLY = 'monthly'
    QUARTERLY = 'quarterly'
    YEARLY = 'yearly'
    CUSTOM = 'custom'

class ReportStatus(str, Enum):
    PENDING = 'pending'
    GENERATING = 'generating'
    COMPLETED = 'completed'
    FAILED = 'failed'

class SystemHealthStatus(str, Enum):
    HEALTHY = 'healthy'
    WARNING = 'warning'
    CRITICAL = 'critical'
    MAINTENANCE = 'maintenance'

class NotificationChannel(str, Enum):
    EMAIL = 'email'
    SMS = 'sms'
    TELEGRAM = 'telegram'
    WEBHOOK = 'webhook'
    IN_APP = 'in_app'
    PUSH = 'push'

class NotificationTemplateType(str, Enum):
    WELCOME = 'welcome'
    PASSWORD_RESET = 'password_reset'
    SUBSCRIPTION = 'subscription'
    ALERT = 'alert'
    MAINTENANCE = 'maintenance'

# Base schemas
class SystemHealthBase(BaseModel):
    """Base schema for system health."""
    component: str = Field(..., min_length=1, max_length=100)
    status: SystemHealthStatus
    message: Optional[str] = None
    next_check: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None

class SystemHealthCreate(SystemHealthBase):
    """Schema for creating a system health record."""
    pass

class SystemHealthUpdate(SystemHealthBase):
    """Schema for updating a system health record."""
    component: Optional[str] = Field(None, min_length=1, max_length=100)
    status: Optional[SystemHealthStatus] = None

class SystemHealth(SystemHealthBase):
    """Schema for system health record."""
    id: int
    last_check: datetime
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None
    updated_by: Optional[int] = None

    class Config:
        orm_mode = True

class SystemBackupBase(BaseModel):
    """Base schema for system backup."""
    name: str = Field(..., description="Name of the backup")
    description: Optional[str] = Field(None, description="Description of the backup")
    backup_type: BackupType = Field(..., description="Type of backup")
    storage_path: str = Field(..., description="Path where backup is stored")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")

class SystemBackupCreate(SystemBackupBase):
    """Schema for creating a new backup."""
    pass

class SystemBackupUpdate(BaseModel):
    """Schema for updating an existing backup."""
    name: Optional[str] = None
    description: Optional[str] = None
    backup_type: Optional[BackupType] = None
    storage_path: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    status: Optional[BackupStatus] = None
    error_message: Optional[str] = None

class SystemBackupInDB(SystemBackupBase):
    """Schema for backup as stored in database."""
    id: int
    status: BackupStatus
    size_bytes: Optional[int] = None
    checksum: Optional[str] = None
    schedule_id: Optional[int] = None
    created_by: int
    updated_by: int
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    verified_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    error_message: Optional[str] = None

    class Config:
        orm_mode = True

class NotificationTemplateBase(BaseModel):
    """Base schema for notification template."""
    name: str = Field(..., min_length=1, max_length=100)
    type: NotificationTemplateType
    subject: Optional[str] = Field(None, max_length=255)
    content: str
    variables: Optional[Dict[str, Any]] = None
    channels: List[NotificationChannel]
    is_active: bool = True
    metadata: Optional[Dict[str, Any]] = None

class NotificationTemplateCreate(NotificationTemplateBase):
    """Schema for creating a notification template."""
    pass

class NotificationTemplateUpdate(NotificationTemplateBase):
    """Schema for updating a notification template."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    type: Optional[NotificationTemplateType] = None
    content: Optional[str] = None
    channels: Optional[List[NotificationChannel]] = None

class NotificationTemplate(NotificationTemplateBase):
    """Schema for notification template record."""
    id: int
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None
    updated_by: Optional[int] = None

    class Config:
        orm_mode = True

class ReportBase(BaseModel):
    """Base schema for report."""
    name: str = Field(..., min_length=1, max_length=100)
    type: ReportType
    parameters: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    next_generation: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None

class ReportCreate(ReportBase):
    """Schema for creating a report."""
    pass

class ReportUpdate(ReportBase):
    """Schema for updating a report."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    type: Optional[ReportType] = None

class Report(ReportBase):
    """Schema for report record."""
    id: int
    status: ReportStatus
    generated_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None
    updated_by: Optional[int] = None

    class Config:
        orm_mode = True

class ReportScheduleBase(BaseModel):
    """Base schema for report schedule."""
    report_id: int
    cron_expression: str = Field(..., min_length=1, max_length=100)
    is_active: bool = True
    recipients: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

class ReportScheduleCreate(ReportScheduleBase):
    """Schema for creating a report schedule."""
    pass

class ReportScheduleUpdate(ReportScheduleBase):
    """Schema for updating a report schedule."""
    report_id: Optional[int] = None
    cron_expression: Optional[str] = Field(None, min_length=1, max_length=100)

class ReportSchedule(ReportScheduleBase):
    """Schema for report schedule record."""
    id: int
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None
    updated_by: Optional[int] = None

    class Config:
        orm_mode = True

class SystemLogBase(BaseModel):
    """Base schema for system log."""
    level: str = Field(..., min_length=1, max_length=20)
    component: str = Field(..., min_length=1, max_length=100)
    message: str
    stack_trace: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

class SystemLogCreate(SystemLogBase):
    """Schema for creating a system log."""
    pass

class SystemLog(SystemLogBase):
    """Schema for system log record."""
    id: int
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None
    updated_by: Optional[int] = None

    class Config:
        orm_mode = True

class SystemConfigurationBase(BaseModel):
    """Base schema for system configuration."""
    key: str = Field(..., min_length=1, max_length=100)
    value: Dict[str, Any]
    description: Optional[str] = None
    is_encrypted: bool = False
    is_sensitive: bool = False
    validation_rules: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

class SystemConfigurationCreate(SystemConfigurationBase):
    """Schema for creating a system configuration."""
    pass

class SystemConfigurationUpdate(SystemConfigurationBase):
    """Schema for updating a system configuration."""
    key: Optional[str] = Field(None, min_length=1, max_length=100)
    value: Optional[Dict[str, Any]] = None

class SystemConfiguration(SystemConfigurationBase):
    """Schema for system configuration record."""
    id: int
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None
    updated_by: Optional[int] = None

    class Config:
        orm_mode = True

class SystemMetricBase(BaseModel):
    """Base schema for system metric."""
    metric_name: str = Field(..., min_length=1, max_length=100)
    value: float
    unit: Optional[str] = Field(None, max_length=20)
    metadata: Optional[Dict[str, Any]] = None

class SystemMetricCreate(SystemMetricBase):
    """Schema for creating a system metric."""
    pass

class SystemMetricUpdate(SystemMetricBase):
    """Schema for updating a system metric."""
    metric_name: Optional[str] = Field(None, min_length=1, max_length=100)
    value: Optional[float] = None

class SystemMetric(SystemMetricBase):
    """Schema for system metric record."""
    id: int
    timestamp: datetime
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None
    updated_by: Optional[int] = None

    class Config:
        orm_mode = True

class BackupScheduleBase(BaseModel):
    """Base schema for backup schedule."""
    name: str = Field(..., description="Name of the schedule")
    description: Optional[str] = Field(None, description="Description of the schedule")
    schedule_type: ScheduleType = Field(..., description="Type of schedule")
    cron_expression: str = Field(..., description="Cron expression for scheduling")
    is_active: bool = Field(True, description="Whether the schedule is active")
    retention_days: int = Field(..., description="Number of days to retain backups")
    max_backups: int = Field(..., description="Maximum number of backups to keep")
    backup_type: BackupType = Field(..., description="Type of backup to create")
    storage_path: str = Field(..., description="Path where backups will be stored")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")

class BackupScheduleCreate(BackupScheduleBase):
    """Schema for creating a new backup schedule."""
    pass

class BackupScheduleUpdate(BaseModel):
    """Schema for updating an existing backup schedule."""
    name: Optional[str] = None
    description: Optional[str] = None
    schedule_type: Optional[ScheduleType] = None
    cron_expression: Optional[str] = None
    is_active: Optional[bool] = None
    retention_days: Optional[int] = None
    max_backups: Optional[int] = None
    backup_type: Optional[BackupType] = None
    storage_path: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class BackupScheduleInDB(BackupScheduleBase):
    """Schema for backup schedule as stored in database."""
    id: int
    created_by: int
    updated_by: int
    created_at: datetime
    updated_at: datetime
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class BackupStatistics(BaseModel):
    """Schema for backup statistics."""
    total_backups: int
    completed_backups: int
    failed_backups: int
    success_rate: float
    total_size_bytes: int
    total_size_gb: float 