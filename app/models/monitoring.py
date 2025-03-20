from sqlalchemy import Column, Integer, String, Float, JSON, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.db.base_class import Base
import enum

class MetricType(str, enum.Enum):
    SYSTEM = "system"
    APPLICATION = "application"
    CUSTOM = "custom"

class AlertSeverity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AlertStatus(str, enum.Enum):
    ACTIVE = "active"
    RESOLVED = "resolved"
    ACKNOWLEDGED = "acknowledged"

class SystemHealth(str, enum.Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

class MonitoringMetric(Base):
    """Model for storing monitoring metrics."""
    __tablename__ = "monitoring_metrics"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    value = Column(Float)
    unit = Column(String)
    timestamp = Column(Float, index=True)
    tags = Column(JSON)
    type = Column(Enum(MetricType), default=MetricType.CUSTOM)

    def __repr__(self):
        return f"<MonitoringMetric {self.name}={self.value} {self.unit}>"

class Alert(Base):
    """Model for storing system alerts."""
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    severity = Column(Enum(AlertSeverity), default=AlertSeverity.MEDIUM)
    status = Column(Enum(AlertStatus), default=AlertStatus.ACTIVE)
    created_at = Column(Float, index=True)
    resolved_at = Column(Float, nullable=True)
    acknowledged_at = Column(Float, nullable=True)
    acknowledged_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    metadata = Column(JSON, nullable=True)

    # Relationships
    acknowledger = relationship("User", back_populates="acknowledged_alerts")

    def __repr__(self):
        return f"<Alert {self.name} ({self.severity})>"

class SystemStatus(Base):
    """Model for storing system status snapshots."""
    __tablename__ = "system_status"

    id = Column(Integer, primary_key=True, index=True)
    health = Column(Enum(SystemHealth), default=SystemHealth.UNKNOWN)
    metrics = Column(JSON)
    alerts = Column(JSON)
    components = Column(JSON)
    timestamp = Column(Float, index=True)

    def __repr__(self):
        return f"<SystemStatus {self.health} at {self.timestamp}>"

class Log(Base):
    """Model for storing system logs."""
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True)
    level = Column(String, index=True)
    message = Column(String)
    source = Column(String)
    timestamp = Column(Float, index=True)
    metadata = Column(JSON, nullable=True)

    def __repr__(self):
        return f"<Log {self.level}: {self.message}>"

class Notification(Base):
    """Model for storing notifications."""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, index=True)
    channel = Column(String)
    content = Column(JSON)
    status = Column(String)
    timestamp = Column(Float, index=True)
    metadata = Column(JSON, nullable=True)

    def __repr__(self):
        return f"<Notification {self.type} via {self.channel}>"

class Report(Base):
    """Model for storing monitoring reports."""
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, index=True)
    content = Column(JSON)
    status = Column(String)
    timestamp = Column(Float, index=True)
    metadata = Column(JSON, nullable=True)

    def __repr__(self):
        return f"<Report {self.type} at {self.timestamp}>"

class ReportSchedule(Base):
    """Model for storing report schedules."""
    __tablename__ = "report_schedules"

    id = Column(Integer, primary_key=True, index=True)
    report_type = Column(String, index=True)
    recipients = Column(JSON)
    next_run = Column(Float, index=True)
    created_at = Column(Float, index=True)
    last_run = Column(Float, nullable=True)
    status = Column(String, default="active")
    metadata = Column(JSON, nullable=True)

    def __repr__(self):
        return f"<ReportSchedule {self.report_type} next run at {self.next_run}>" 