"""
SystemMetric model for managing system metrics and monitoring.
"""

from typing import Optional, List
from sqlalchemy import String, Integer, Float, Boolean, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
import enum

from ..base import BaseModel

class MetricType(str, enum.Enum):
    """Metric type enumeration."""
    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    CONNECTIONS = "connections"
    LATENCY = "latency"
    CUSTOM = "custom"

class MetricUnit(str, enum.Enum):
    """Metric unit enumeration."""
    PERCENT = "percent"
    BYTES = "bytes"
    COUNT = "count"
    SECONDS = "seconds"
    CUSTOM = "custom"

class SystemMetric(BaseModel):
    """
    SystemMetric model for managing system metrics.
    
    Attributes:
        type: Metric type
        name: Metric name
        value: Metric value
        unit: Metric unit
        server_id: Reference to server if applicable
        timestamp: When the metric was recorded
        metadata: Additional metric data
    """
    
    # Metric identification
    type: Mapped[MetricType] = mapped_column(Enum(MetricType), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[MetricUnit] = mapped_column(Enum(MetricUnit), nullable=False)
    
    # Metric details
    server_id: Mapped[Optional[int]] = mapped_column(ForeignKey("server.id"), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(nullable=False)
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    # Relationships
    server: Mapped[Optional["Server"]] = relationship()
    
    def __repr__(self) -> str:
        """String representation of the system metric."""
        return f"<SystemMetric(type={self.type}, name={self.name})>" 