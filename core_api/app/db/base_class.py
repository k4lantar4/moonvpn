# core_api/app/db/base_class.py
from typing import Any
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    """
    Base class for all database models.
    
    This class provides common functionality and settings for all models.
    It's designed to be inherited by all model classes in the application.
    """
    # Allow unmapped type annotations in model classes
    __allow_unmapped__ = True

    # Use class name as table name by default (converted to lowercase)
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()

    # Generic method for string representation
    def __repr__(self) -> str:
        attrs = []
        for col in self.__table__.columns:
            if hasattr(self, col.name):
                value = getattr(self, col.name)
                # Truncate long string values for better readability
                if isinstance(value, str) and len(value) > 30:
                    value = f"{value[:27]}..."
                attrs.append(f"{col.name}={value!r}")
        return f"<{self.__class__.__name__}({', '.join(attrs)})>" 