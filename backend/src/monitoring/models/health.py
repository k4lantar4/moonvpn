from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class HealthStatus(Base):
    """Model for storing health status of system components"""
    __tablename__ = "health_status"

    id = Column(Integer, primary_key=True, index=True)
    component = Column(String, nullable=False)
    status = Column(String, nullable=False)  # healthy, unhealthy, degraded
    message = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    details = Column(JSON, nullable=True)
    check_id = Column(Integer, ForeignKey("health_checks.id"))

    # Relationships
    check = relationship("HealthCheck", back_populates="statuses")

class HealthCheck(Base):
    """Model for storing health check history"""
    __tablename__ = "health_checks"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    overall_status = Column(String, nullable=False)  # healthy, unhealthy, degraded
    duration_ms = Column(Integer, nullable=True)  # Duration of the health check in milliseconds
    error_count = Column(Integer, default=0)
    warning_count = Column(Integer, default=0)
    details = Column(JSON, nullable=True)

    # Relationships
    statuses = relationship("HealthStatus", back_populates="check")

class RecoveryAction(Base):
    """Model for storing recovery actions taken"""
    __tablename__ = "recovery_actions"

    id = Column(Integer, primary_key=True, index=True)
    component = Column(String, nullable=False)
    action_type = Column(String, nullable=False)  # reconnect, restart, clear_cache, etc.
    timestamp = Column(DateTime, default=datetime.utcnow)
    status = Column(String, nullable=False)  # success, failure, in_progress
    message = Column(String, nullable=True)
    details = Column(JSON, nullable=True)
    health_status_id = Column(Integer, ForeignKey("health_status.id"))

    # Relationships
    health_status = relationship("HealthStatus") 