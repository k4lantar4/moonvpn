"""
Template test result model for system health monitoring.

This module defines the database model for storing template test results.
"""

from datetime import datetime
from typing import Dict, Any
from sqlalchemy import Column, Integer, String, Float, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class TemplateTestResult(Base):
    """Model for storing template test results."""

    __tablename__ = "template_test_results"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("recovery_templates.id"), nullable=False)
    status = Column(String, nullable=False)  # success, failure, error
    message = Column(String, nullable=False)
    execution_time = Column(Float, nullable=False)  # in seconds
    parameters = Column(JSON, nullable=False)
    errors = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    template = relationship("RecoveryTemplate", back_populates="test_results") 