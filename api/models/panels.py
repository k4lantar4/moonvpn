from sqlalchemy import (Column, Integer, String, Boolean, DateTime, ForeignKey, Text, UniqueConstraint)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from api.models.base import Base

class Panel(Base):
    __tablename__ = "panels"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    url = Column(String(255), unique=True, nullable=False) # Panel API base URL
    login_path = Column(String(50), default="/login") # Default login path for 3x-ui
    username = Column(String(100), nullable=False)
    password = Column(String(255), nullable=False) # Store securely (e.g., encrypted)

    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    panel_type = Column(String(50), default='3x-ui') # Could support other types later

    is_active = Column(Boolean, default=True) # Admin can disable
    is_healthy = Column(Boolean, default=False) # Updated by health checks
    last_check = Column(DateTime, nullable=True)
    status_message = Column(String(255), nullable=True) # Store last health check result/error
    priority = Column(Integer, default=0) # For load balancing/selection

    created_by = Column(Integer, ForeignKey("users.id"), nullable=True) # Optional: track who added it
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    location = relationship("Location", back_populates="panels")
    created_by_user = relationship("User", back_populates="panels_created")
    clients = relationship("Client", foreign_keys="[Client.panel_id]", back_populates="panel")
    previous_clients = relationship("Client", foreign_keys="[Client.previous_panel_id]", back_populates="previous_panel")
    health_checks = relationship("PanelHealthCheck", back_populates="panel")

    # Additional fields for panel management
    api_path = Column(String(100), nullable=True)
    server_ip = Column(String(45), nullable=True)
    server_type = Column(String(50), nullable=True)
    api_token = Column(String(255), nullable=True)
    api_token_expires_at = Column(DateTime, nullable=True)
    
    # Enhanced panel info fields
    geo_location = Column(String(100), nullable=True)
    provider = Column(String(100), nullable=True)
    datacenter = Column(String(100), nullable=True)
    alternate_domain = Column(String(255), nullable=True)
    is_premium = Column(Boolean, default=False)
    network_speed = Column(String(50), nullable=True)
    server_specs = Column(Text, nullable=True)
    
    # Fields for panel migration
    previous_server_ip = Column(String(45), nullable=True)
    previous_url = Column(String(255), nullable=True)
    migration_date = Column(DateTime, nullable=True)
    migration_notes = Column(Text, nullable=True)
    is_migrated = Column(Boolean, default=False)

    # Relationships with other panel-related tables
    inbounds = relationship('PanelInbound', back_populates='panel')
    domains = relationship('PanelDomain', back_populates='panel')
    migrations = relationship('PanelServerMigration', back_populates='panel')

    def __repr__(self):
        return f"<Panel(id={self.id}, name={self.name}, url={self.url})>"

class PanelInbound(Base):
    __tablename__ = "panel_inbounds"
    
    id = Column(Integer, primary_key=True, index=True)
    panel_id = Column(Integer, ForeignKey("panels.id"), nullable=False)
    inbound_id = Column(Integer, nullable=False)
    tag = Column(String(100), nullable=False)
    protocol = Column(String(20), nullable=False)  # vmess, vless, trojan, etc.
    port = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)
    settings = Column(Text, nullable=True)  # JSON settings
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    panel = relationship("Panel", back_populates="inbounds")
    
    def __repr__(self):
        return f"<PanelInbound(id={self.id}, panel_id={self.panel_id}, inbound_id={self.inbound_id}, tag={self.tag})>"

class PanelDomain(Base):
    __tablename__ = "panel_domains"
    
    id = Column(Integer, primary_key=True, index=True)
    panel_id = Column(Integer, ForeignKey("panels.id"), nullable=False)
    domain = Column(String(255), nullable=False)
    is_primary = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    panel = relationship("Panel", back_populates="domains")
    
    __table_args__ = (
        # Unique constraint for panel_id and domain
        UniqueConstraint('panel_id', 'domain'),
    )
    
    def __repr__(self):
        return f"<PanelDomain(id={self.id}, panel_id={self.panel_id}, domain={self.domain})>"

class PanelHealthCheck(Base):
    __tablename__ = "panel_health_checks"
    
    id = Column(Integer, primary_key=True, index=True)
    panel_id = Column(Integer, ForeignKey("panels.id"), nullable=False)
    check_time = Column(DateTime(timezone=True), server_default=func.now())
    is_healthy = Column(Boolean, nullable=False)
    status_code = Column(Integer, nullable=True)
    response_time_ms = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    cpu_usage = Column(String(20), nullable=True)
    memory_usage = Column(String(20), nullable=True)
    disk_usage = Column(String(20), nullable=True)
    
    panel = relationship("Panel", back_populates="health_checks")
    
    def __repr__(self):
        return f"<PanelHealthCheck(id={self.id}, panel_id={self.panel_id}, is_healthy={self.is_healthy})>"

class PanelServerMigration(Base):
    __tablename__ = "panel_server_migrations"
    
    id = Column(Integer, primary_key=True, index=True)
    panel_id = Column(Integer, ForeignKey("panels.id"), nullable=False)
    old_server_ip = Column(String(45), nullable=False)
    old_url = Column(String(255), nullable=False)
    new_server_ip = Column(String(45), nullable=False)
    new_url = Column(String(255), nullable=False)
    migration_date = Column(DateTime(timezone=True), server_default=func.now())
    performed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(String(20), nullable=False)  # started, completed, failed
    notes = Column(Text, nullable=True)
    
    panel = relationship("Panel", back_populates="migrations")
    performed_by_user = relationship("User")
    
    def __repr__(self):
        return f"<PanelServerMigration(id={self.id}, panel_id={self.panel_id}, status={self.status})>" 