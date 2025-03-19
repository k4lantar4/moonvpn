"""SQLAlchemy base model."""
from datetime import datetime
from typing import Any

from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy import Column, DateTime
from sqlalchemy.sql import func

@as_declarative()
class Base:
    """Base class for all database models."""

    id: Any
    __name__: str

    # Generate __tablename__ automatically
    @declared_attr
    def __tablename__(cls) -> str:
        """Generate table name from class name."""
        return cls.__name__.lower()
    
    # Add created_at and updated_at columns to all models
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    ) 