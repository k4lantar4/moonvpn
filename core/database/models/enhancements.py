"""
Enhancement models for MoonVPN system management and monitoring.

This module contains SQLAlchemy models for system health monitoring, backups,
notifications, reporting, logging, configuration, and metrics tracking.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Enum, JSON, Numeric, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB

from core.database.base import Base
from core.database.models.user import User

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

class BackupType(str, Enum):
    FULL = 'full'
    INCREMENTAL = 'incremental'
    DIFFERENTIAL = 'differential'

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

class SystemHealth(Base):
    """Model for tracking system component health status."""
    
    __tablename__ = 'system_health'

    id = Column(Integer, primary_key=True)
    component = Column(String(100), nullable=False)
    status = Column(Enum(SystemHealthStatus), nullable=False)
    message = Column(Text)
    last_check = Column(DateTime(timezone=True), default=datetime.utcnow)
    next_check = Column(DateTime(timezone=True))
    metadata = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))
    updated_by = Column(Integer, ForeignKey('users.id'))

    creator = relationship('User', foreign_keys=[created_by], backref='created_health_checks')
    updater = relationship('User', foreign_keys=[updated_by], backref='updated_health_checks')

class SystemBackup(Base):
    """Model for managing system backups."""
    
    __tablename__ = 'system_backups'

    id = Column(Integer, primary_key=True)
    type = Column(Enum(BackupType), nullable=False)
    status = Column(Enum(ReportStatus), default=ReportStatus.PENDING)
    size = Column(Integer)
    path = Column(String(255))
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    retention_days = Column(Integer, default=30)
    is_encrypted = Column(Boolean, default=True)
    encryption_key = Column(String(255))
    error_message = Column(Text)
    metadata = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))
    updated_by = Column(Integer, ForeignKey('users.id'))

    creator = relationship('User', foreign_keys=[created_by], backref='created_backups')
    updater = relationship('User', foreign_keys=[updated_by], backref='updated_backups')

class NotificationTemplate(Base):
    """Model for managing notification templates."""
    
    __tablename__ = 'notification_templates'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    type = Column(Enum(NotificationTemplateType), nullable=False)
    subject = Column(String(255))
    content = Column(Text, nullable=False)
    variables = Column(JSONB)
    channels = Column(ARRAY(Enum(NotificationChannel)))
    is_active = Column(Boolean, default=True)
    metadata = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))
    updated_by = Column(Integer, ForeignKey('users.id'))

    creator = relationship('User', foreign_keys=[created_by], backref='created_templates')
    updater = relationship('User', foreign_keys=[updated_by], backref='updated_templates')

class Report(Base):
    """Model for managing system reports."""
    
    __tablename__ = 'reports'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    type = Column(Enum(ReportType), nullable=False)
    status = Column(Enum(ReportStatus), default=ReportStatus.PENDING)
    parameters = Column(JSONB)
    result = Column(JSONB)
    error_message = Column(Text)
    generated_at = Column(DateTime(timezone=True))
    next_generation = Column(DateTime(timezone=True))
    metadata = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))
    updated_by = Column(Integer, ForeignKey('users.id'))

    creator = relationship('User', foreign_keys=[created_by], backref='created_reports')
    updater = relationship('User', foreign_keys=[updated_by], backref='updated_reports')
    schedules = relationship('ReportSchedule', back_populates='report')

class ReportSchedule(Base):
    """Model for managing report generation schedules."""
    
    __tablename__ = 'report_schedules'

    id = Column(Integer, primary_key=True)
    report_id = Column(Integer, ForeignKey('reports.id'), nullable=False)
    cron_expression = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    last_run = Column(DateTime(timezone=True))
    next_run = Column(DateTime(timezone=True))
    recipients = Column(JSONB)
    metadata = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))
    updated_by = Column(Integer, ForeignKey('users.id'))

    report = relationship('Report', back_populates='schedules')
    creator = relationship('User', foreign_keys=[created_by], backref='created_schedules')
    updater = relationship('User', foreign_keys=[updated_by], backref='updated_schedules')

class SystemLog(Base):
    """Model for system logging."""
    
    __tablename__ = 'system_logs'

    id = Column(Integer, primary_key=True)
    level = Column(String(20), nullable=False)
    component = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)
    stack_trace = Column(Text)
    context = Column(JSONB)
    metadata = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))
    updated_by = Column(Integer, ForeignKey('users.id'))

    creator = relationship('User', foreign_keys=[created_by], backref='created_logs')
    updater = relationship('User', foreign_keys=[updated_by], backref='updated_logs')

class SystemConfiguration(Base):
    """Model for system configuration management."""
    
    __tablename__ = 'system_configurations'

    id = Column(Integer, primary_key=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(JSONB, nullable=False)
    description = Column(Text)
    is_encrypted = Column(Boolean, default=False)
    is_sensitive = Column(Boolean, default=False)
    validation_rules = Column(JSONB)
    metadata = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))
    updated_by = Column(Integer, ForeignKey('users.id'))

    creator = relationship('User', foreign_keys=[created_by], backref='created_configs')
    updater = relationship('User', foreign_keys=[updated_by], backref='updated_configs')

class SystemMetric(Base):
    """Model for tracking system metrics."""
    
    __tablename__ = 'system_metrics'

    id = Column(Integer, primary_key=True)
    metric_name = Column(String(100), nullable=False)
    value = Column(Numeric(10, 2), nullable=False)
    unit = Column(String(20))
    timestamp = Column(DateTime(timezone=True), default=datetime.utcnow)
    metadata = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))
    updated_by = Column(Integer, ForeignKey('users.id'))

    creator = relationship('User', foreign_keys=[created_by], backref='created_metrics')
    updater = relationship('User', foreign_keys=[updated_by], backref='updated_metrics') 