from sqlalchemy import (Column, Integer, String, Boolean, DateTime, ForeignKey, Text)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from api.models.base import Base

class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    flag = Column(String(10), nullable=True) # Emoji flag e.g. 🇩🇪
    country_code = Column(String(2), nullable=True) # ISO 3166-1 alpha-2
    is_active = Column(Boolean, default=True)
    description = Column(Text, nullable=True)
    
    # Fields for inbound management
    default_inbound_id = Column(Integer, nullable=True)
    protocols_supported = Column(String(100), nullable=True)  # comma-separated list
    inbound_tag_pattern = Column(String(100), nullable=True)
    default_remark_prefix = Column(String(50), nullable=True)
    
    # Fields for remark & migration
    remark_pattern = Column(String(100), nullable=True)  # Pattern for new client remarks
    migration_remark_pattern = Column(String(100), nullable=True)  # Pattern for migrated clients
    max_migrations_per_day = Column(Integer, default=3) # Maximum allowed migrations per day

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    panels = relationship("Panel", back_populates="location")
    client_id_sequences = relationship("ClientIdSequence", back_populates="location")
    clients = relationship("Client", back_populates="location")

    def __repr__(self):
        return f"<Location(id={self.id}, name={self.name})>"

class ClientIdSequence(Base):
    __tablename__ = "client_id_sequences"
    
    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    last_id = Column(Integer, default=0)
    prefix = Column(String(20), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    location = relationship("Location", back_populates="client_id_sequences")
    
    def __repr__(self):
        return f"<ClientIdSequence(id={self.id}, location_id={self.location_id}, last_id={self.last_id})>" 