"""
Recovery models for system health monitoring.

This module defines the database models for tracking automated recovery actions
and their status in the system.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, Any
from sqlalchemy import Column, Integer, String, JSON, DateTime, Enum as SQLEnum
from app.core.database import Base

class RecoveryStatus(str, Enum):
    """Enumeration of possible recovery action statuses."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class RecoveryAction(Base):
    """Model for tracking system recovery actions."""

    __tablename__ = "recovery_actions"

    id = Column(Integer, primary_key=True, index=True)
    component = Column(String, nullable=False, index=True)
    failure_type = Column(String, nullable=False)
    strategy = Column(String, nullable=False)
    parameters = Column(JSON, nullable=True)
    status = Column(SQLEnum(RecoveryStatus), nullable=False, default=RecoveryStatus.PENDING)
    result = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(String, nullable=True)

    def __repr__(self) -> str:
        """String representation of the recovery action."""
        return f"<RecoveryAction {self.id}: {self.component} - {self.status}>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert the recovery action to a dictionary."""
        return {
            "id": self.id,
            "component": self.component,
            "failure_type": self.failure_type,
            "strategy": self.strategy,
            "parameters": self.parameters,
            "status": self.status,
            "result": self.result,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message
        } 