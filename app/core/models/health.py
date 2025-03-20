"""
Health check models for system monitoring.
"""
from datetime import datetime
from enum import Enum
from typing import Dict, Optional
from sqlalchemy import Column, Integer, String, DateTime, JSON, Enum as SQLEnum
from sqlalchemy.sql import func

from app.core.database import Base

class HealthStatus(str, Enum):
    """Health status enumeration."""
    HEALTHY = "healthy"
    WARNING = "warning"
    ERROR = "error"
    UNKNOWN = "unknown"

class HealthCheck(Base):
    """Model for storing health check results."""
    __tablename__ = "health_checks"

    id = Column(Integer, primary_key=True, index=True)
    component = Column(String, index=True, nullable=False)
    status = Column(SQLEnum(HealthStatus), nullable=False)
    message = Column(String, nullable=False)
    metrics = Column(JSON, nullable=True)
    last_check = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    def __repr__(self):
        return f"<HealthCheck {self.component}: {self.status}>" 