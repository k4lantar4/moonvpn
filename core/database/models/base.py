"""
Base model with common functionality for all models.
"""

from typing import Optional, Dict, Any
from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime
import uuid

class Base(DeclarativeBase):
    """Base class for all models."""
    pass

class BaseModel(Base):
    """
    Base model with common fields and functionality.
    
    Attributes:
        id: Primary key
        uuid: Unique identifier
        created_at: Creation timestamp
        updated_at: Last update timestamp
        deleted_at: Deletion timestamp
        created_by: Creator reference
        updated_by: Last updater reference
        deleted_by: Deleter reference
        metadata: Additional model data
    """
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Unique identifier
    uuid: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # References
    created_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    updated_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    deleted_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Additional data
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(nullable=True)
    
    def __repr__(self) -> str:
        """String representation of the model."""
        return f"<{self.__class__.__name__}(id={self.id}, uuid={self.uuid})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "uuid": self.uuid,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "deleted_by": self.deleted_by,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BaseModel":
        """Create model from dictionary."""
        return cls(**data) 