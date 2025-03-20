"""
Performance models for MoonVPN.
"""

from sqlalchemy import Column, String, JSON, DateTime, Float, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum

from ..database.base import Base

class TuningType(str, enum.Enum):
    """Types of performance tuning."""
    DATABASE = "database"
    CACHE = "cache"
    NETWORK = "network"
    APPLICATION = "application"

class TuningPhase(str, enum.Enum):
    """Phases of performance tuning."""
    ANALYSIS = "analysis"
    OPTIMIZATION = "optimization"
    TUNING = "tuning"

class PerformanceTuning(Base):
    """Model for performance tuning records."""
    __tablename__ = "performance_tuning"

    id = Column(String, primary_key=True)
    type = Column(Enum(TuningType), nullable=False)
    config = Column(JSON, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    duration = Column(Float)
    status = Column(String, nullable=False, default="running")
    
    # Relationships
    results = relationship("TuningResult", back_populates="tuning")

class TuningResult(Base):
    """Model for tuning results."""
    __tablename__ = "tuning_results"

    id = Column(String, primary_key=True)
    tuning_id = Column(String, ForeignKey("performance_tuning.id"), nullable=False)
    phase = Column(Enum(TuningPhase), nullable=False)
    metrics = Column(JSON, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    
    # Relationships
    tuning = relationship("PerformanceTuning", back_populates="results") 