"""
SystemHealth model for monitoring system health and performance.
"""

from typing import Optional, List
from sqlalchemy import String, Integer, Float, Boolean, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
import enum

from ..base import BaseModel

class HealthStatus(str, enum.Enum):
    """Health status enumeration."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

class SystemHealth(BaseModel):
    """
    SystemHealth model for monitoring system health.
    
    Attributes:
        component: System component name
        status: Health status
        is_active: Whether the component is active
        last_check: Last health check timestamp
        response_time: Component response time
        error_count: Number of errors
        warning_count: Number of warnings
        details: Additional health details
    """
    
    # Health identification
    component: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[HealthStatus] = mapped_column(Enum(HealthStatus), default=HealthStatus.UNKNOWN, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Health metrics
    last_check: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    response_time: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    error_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    warning_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    def __repr__(self) -> str:
        """String representation of the system health."""
        return f"<SystemHealth(component={self.component}, status={self.status})>" 