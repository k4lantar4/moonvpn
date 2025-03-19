"""
Base model classes for MoonVPN database models.
Provides common functionality and fields for all models.
"""

from datetime import datetime
from typing import Any, Dict, Optional
from sqlalchemy import Column, DateTime, Integer, String, JSON
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass

class BaseModel(Base):
    """
    Base model class that provides common fields and functionality.
    All models should inherit from this class.
    """
    
    __abstract__ = True
    
    @declared_attr
    def __tablename__(cls) -> str:
        """Generate __tablename__ automatically."""
        return cls.__name__.lower()
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    metadata = Column(JSON, nullable=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model instance to dictionary."""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
    
    def update(self, **kwargs: Any) -> None:
        """Update model instance with given kwargs."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    @classmethod
    def get_by_id(cls, session, id: int) -> Optional['BaseModel']:
        """Get model instance by id."""
        return session.query(cls).filter(cls.id == id).first()
    
    def __repr__(self) -> str:
        """String representation of the model."""
        return f"<{self.__class__.__name__}(id={self.id})>" 