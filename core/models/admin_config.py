"""
Admin configuration model for MoonVPN.

This module defines the database model for storing admin-related
configuration settings.
"""

from sqlalchemy import Column, Integer, String, Boolean, JSON, DateTime
from sqlalchemy.sql import func
from app.core.database.base import Base

class AdminConfig(Base):
    """Model for storing admin configuration settings."""
    
    __tablename__ = "admin_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(JSON, nullable=False)
    description = Column(String(255))
    is_encrypted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __str__(self):
        return f"<AdminConfig {self.key}>"
    
    @classmethod
    def get_setting(cls, db, key: str, default=None):
        """Get a configuration setting by key."""
        config = db.query(cls).filter(cls.key == key).first()
        return config.value if config else default
    
    @classmethod
    def set_setting(cls, db, key: str, value: any, description: str = None):
        """Set a configuration setting."""
        config = db.query(cls).filter(cls.key == key).first()
        if config:
            config.value = value
            if description:
                config.description = description
        else:
            config = cls(key=key, value=value, description=description)
            db.add(config)
        db.commit()
        return config 