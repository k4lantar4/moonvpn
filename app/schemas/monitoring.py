from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime
from app.models.monitoring import (
    MetricType,
    AlertSeverity,
    AlertStatus,
    SystemHealth
)

class MetricBase(BaseModel):
    """Base schema for monitoring metrics."""
    name: str
    value: float
    unit: str = "count"
    tags: Optional[Dict[str, str]] = None
    type: Optional[MetricType] = MetricType.CUSTOM

class MetricCreate(MetricBase):
    """Schema for creating monitoring metrics."""
    pass

class MetricResponse(MetricBase):
    """Schema for monitoring metric responses."""
    id: int
    timestamp: float

    class Config:
        orm_mode = True

class AlertBase(BaseModel):
    """Base schema for system alerts."""
    name: str
    description: str
    severity: AlertSeverity = AlertSeverity.MEDIUM
    metadata: Optional[Dict[str, Any]] = None

class AlertCreate(AlertBase):
    """Schema for creating system alerts."""
    pass

class AlertResponse(AlertBase):
    """Schema for alert responses."""
    id: int
    status: AlertStatus
    created_at: float
    resolved_at: Optional[float] = None
    acknowledged_at: Optional[float] = None
    acknowledged_by: Optional[int] = None

    class Config:
        orm_mode = True

class SystemStatusResponse(BaseModel):
    """Schema for system status responses."""
    health: SystemHealth
    metrics: Dict[str, Any]
    alerts: List[Dict[str, Any]]
    components: List[Dict[str, Any]]
    last_check: float

class LogResponse(BaseModel):
    """Schema for log responses."""
    id: int
    level: str
    message: str
    source: str
    timestamp: float
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        orm_mode = True

class NotificationResponse(BaseModel):
    """Schema for notification responses."""
    id: int
    type: str
    channel: str
    content: Dict[str, Any]
    status: str
    timestamp: float
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        orm_mode = True

class ReportResponse(BaseModel):
    """Schema for report responses."""
    id: int
    type: str
    content: Dict[str, Any]
    status: str
    timestamp: float
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        orm_mode = True

class ReportScheduleCreate(BaseModel):
    """Schema for creating report schedules."""
    report_type: str
    recipients: List[str]
    metadata: Optional[Dict[str, Any]] = None

class ReportScheduleResponse(BaseModel):
    """Schema for report schedule responses."""
    id: int
    report_type: str
    recipients: List[str]
    next_run: float
    created_at: float
    last_run: Optional[float] = None
    status: str
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        orm_mode = True

class DashboardMetrics(BaseModel):
    """Schema for dashboard metrics."""
    system_health: SystemHealth
    performance: Dict[str, Any]
    alerts: List[Dict[str, Any]]

class MetricVisualization(BaseModel):
    """Schema for metric visualizations."""
    data: List[Dict[str, Any]]
    chart_type: str
    metric_name: str
    time_range: str

class MetricComparison(BaseModel):
    """Schema for metric comparisons."""
    time_range: str
    data: List[Dict[str, Any]]

class RecoveryResponse(BaseModel):
    """Schema for recovery responses."""
    status: str
    recovery_time: float
    timestamp: float 