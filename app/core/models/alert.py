"""
Alert models for system monitoring and notifications.
"""
from datetime import datetime
from enum import Enum
from typing import Dict, Optional
from sqlalchemy import Column, Integer, String, DateTime, JSON, Enum as SQLEnum, Boolean
from sqlalchemy.sql import func

from app.core.database import Base

class AlertSeverity(str, Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class AlertStatus(str, Enum):
    """Alert status."""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    IGNORED = "ignored"

class Alert(Base):
    """Model for storing system alerts."""
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    component = Column(String, index=True, nullable=False)
    severity = Column(SQLEnum(AlertSeverity), nullable=False)
    status = Column(SQLEnum(AlertStatus), nullable=False, default=AlertStatus.ACTIVE)
    title = Column(String, nullable=False)
    message = Column(String, nullable=False)
    metrics = Column(JSON, nullable=True)
    acknowledged_by = Column(String, nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    def __repr__(self):
        return f"<Alert {self.component}: {self.severity}>"

class AlertRule(Base):
    """Model for storing alert rules."""
    __tablename__ = "alert_rules"

    id = Column(Integer, primary_key=True, index=True)
    component = Column(String, index=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    severity = Column(SQLEnum(AlertSeverity), nullable=False)
    condition = Column(JSON, nullable=False)  # Stores the alert condition logic
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    def __repr__(self):
        return f"<AlertRule {self.name}: {self.component}>" 