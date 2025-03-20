from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel

class HealthStatusBase(BaseModel):
    component: str
    status: str
    message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class HealthStatusCreate(HealthStatusBase):
    pass

class HealthStatusResponse(HealthStatusBase):
    id: int
    timestamp: datetime
    check_id: int

    class Config:
        orm_mode = True

class HealthCheckBase(BaseModel):
    overall_status: str
    duration_ms: Optional[int] = None
    error_count: int = 0
    warning_count: int = 0
    details: Optional[Dict[str, Any]] = None

class HealthCheckCreate(HealthCheckBase):
    pass

class HealthCheckResponse(HealthCheckBase):
    id: int
    timestamp: datetime
    statuses: list[HealthStatusResponse] = []

    class Config:
        orm_mode = True

class RecoveryActionBase(BaseModel):
    component: str
    action_type: str
    status: str
    message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    health_status_id: int

class RecoveryActionCreate(RecoveryActionBase):
    pass

class RecoveryActionResponse(RecoveryActionBase):
    id: int
    timestamp: datetime

    class Config:
        orm_mode = True

class HealthMetrics(BaseModel):
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_usage: float
    timestamp: datetime

class ComponentHealth(BaseModel):
    status: str
    message: str
    metrics: Optional[HealthMetrics] = None
    last_check: datetime
    recovery_attempts: int = 0
    last_recovery: Optional[datetime] = None 