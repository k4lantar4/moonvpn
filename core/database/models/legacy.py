"""
Database models for legacy code management.
"""

from datetime import datetime
from typing import Dict, List, Any
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from core.database.base import Base

class LegacyCode(Base):
    """Model for archived legacy code."""
    
    __tablename__ = "legacy_codes"
    
    id = Column(Integer, primary_key=True)
    original_path = Column(String, nullable=False)
    archive_path = Column(String, nullable=False)
    description = Column(String, nullable=False)
    archived_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    migrations = relationship("LegacyMigration", back_populates="legacy_code")
    
    def __repr__(self) -> str:
        return f"<LegacyCode(id={self.id}, path={self.original_path})>"

class LegacyMigration(Base):
    """Model for legacy code migration plans and execution."""
    
    __tablename__ = "legacy_migrations"
    
    id = Column(Integer, primary_key=True)
    legacy_code_id = Column(Integer, ForeignKey("legacy_codes.id"), nullable=False)
    new_implementation = Column(String, nullable=False)
    steps = Column(JSON, nullable=False)
    status = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    rollback_at = Column(DateTime)
    error_message = Column(String)
    results = Column(JSON)
    rollback_results = Column(JSON)
    
    # Relationships
    legacy_code = relationship("LegacyCode", back_populates="migrations")
    
    def __repr__(self) -> str:
        return f"<LegacyMigration(id={self.id}, status={self.status})>" 