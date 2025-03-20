"""
Template models for system health monitoring.

This module defines the database models for recovery action templates
and template categories.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Enum, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.core.models.recovery import RecoveryStrategy

class TemplateCategory(Base):
    """Model for recovery action template categories."""
    __tablename__ = "template_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    templates = relationship("RecoveryTemplate", back_populates="category")

    def __repr__(self):
        return f"<TemplateCategory {self.name}>"

class ValidationRule(Base):
    """Model for template validation rules."""
    __tablename__ = "template_validation_rules"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("recovery_templates.id"), nullable=False)
    field = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False)
    value = Column(String(255), nullable=False)
    message = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    template = relationship("RecoveryTemplate", back_populates="validation_rules")

    def __repr__(self):
        return f"<ValidationRule {self.field} - {self.type}>"

    def to_dict(self):
        """Convert validation rule to dictionary."""
        return {
            "id": self.id,
            "template_id": self.template_id,
            "field": self.field,
            "type": self.type,
            "value": self.value,
            "message": self.message,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

class RecoveryTemplate(Base):
    """Model for recovery action templates."""
    __tablename__ = "recovery_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    category_id = Column(Integer, ForeignKey("template_categories.id"))
    strategy = Column(Enum(RecoveryStrategy), nullable=False)
    parameters = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    category = relationship("TemplateCategory", back_populates="templates")
    actions = relationship("RecoveryAction", back_populates="template")
    validation_rules = relationship("ValidationRule", back_populates="template", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<RecoveryTemplate {self.name}>"

    def to_dict(self):
        """Convert template to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category.name if self.category else None,
            "strategy": self.strategy.value,
            "parameters": self.parameters,
            "is_active": self.is_active,
            "validation_rules": [rule.to_dict() for rule in self.validation_rules],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        } 