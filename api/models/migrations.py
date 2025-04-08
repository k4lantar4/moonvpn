from sqlalchemy import (Column, Integer, String, DateTime, ForeignKey, Text, UniqueConstraint)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from api.models.base import Base

class ClientMigrationSettings(Base):
    __tablename__ = "client_migration_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False, unique=True)
    max_migrations_per_day = Column(Integer, default=3)
    allow_custom_remarks = Column(Integer, default=1)
    remark_pattern = Column(String(100), nullable=True)
    migration_remark_pattern = Column(String(100), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    location = relationship("Location")
    
    def __repr__(self):
        return f"<ClientMigrationSettings(id={self.id}, location_id={self.location_id})>"

class PanelMigrationMap(Base):
    __tablename__ = "panel_migration_map"
    
    id = Column(Integer, primary_key=True, index=True)
    source_panel_id = Column(Integer, ForeignKey("panels.id"), nullable=False)
    target_panel_id = Column(Integer, ForeignKey("panels.id"), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Integer, default=1)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    source_panel = relationship("Panel", foreign_keys=[source_panel_id])
    target_panel = relationship("Panel", foreign_keys=[target_panel_id])
    
    __table_args__ = (
        # Unique constraint for source_panel_id and target_panel_id
        UniqueConstraint('source_panel_id', 'target_panel_id'),
    )
    
    def __repr__(self):
        return f"<PanelMigrationMap(id={self.id}, source={self.source_panel_id}, target={self.target_panel_id})>" 