import enum
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Column, Integer, String, Boolean, Text, DateTime, func, BigInteger,
    ForeignKey, Enum as SQLAlchemyEnum
)
from sqlalchemy.orm import relationship, Mapped, mapped_column

from core.database.session import Base

class PanelType(enum.Enum):
    XUI = "XUI" # Corrected value to match SQL
    MARZBAN = "MARZBAN"
    SANAEI = "SANAEI"
    ALIREZA = "ALIREZA"
    VAXILU = "VAXILU"
    XRAY = "XRAY" # Maybe just XRAY?

class Panel(Base):
    """Model for VPN panels (3x-ui)."""
    
    __tablename__ = "panels"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    url: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    api_path: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    login_path: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    username: Mapped[str] = mapped_column(String(100), nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    panel_type: Mapped[Optional[PanelType]] = mapped_column(SQLAlchemyEnum(PanelType), nullable=True)
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"), nullable=False)
    server_ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    server_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, default=None, nullable=True)
    is_healthy: Mapped[Optional[bool]] = mapped_column(Boolean, default=None, nullable=True)
    last_check: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    status_message: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    max_clients: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    current_clients: Mapped[Optional[int]] = mapped_column(Integer, default=None, nullable=True)
    traffic_limit: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    traffic_used: Mapped[Optional[int]] = mapped_column(BigInteger, default=None, nullable=True)
    api_token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    api_token_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    priority: Mapped[Optional[int]] = mapped_column(Integer, default=None, nullable=True)
    created_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), name="created_by", nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, default=None, nullable=True
    )
    geo_location: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    provider: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    datacenter: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    alternate_domain: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_premium: Mapped[Optional[bool]] = mapped_column(Boolean, default=None, nullable=True)
    network_speed: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    server_specs: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships (Forward references as strings)
    location = relationship("Location", back_populates="panels")
    creator = relationship("User", foreign_keys=[created_by_id], back_populates="created_panels")
    client_accounts = relationship("ClientAccount", foreign_keys="[ClientAccount.panel_id]", back_populates="panel")
    # Relationship to synced inbounds from this panel
    inbounds = relationship("PanelInbound", back_populates="panel", cascade="all, delete-orphan")
    health_checks = relationship("PanelHealthCheck", back_populates="panel", cascade="all, delete-orphan")
    # Relationship for previous_panel in ClientAccount is handled there
    
    # Removed commented out relationships as they are now defined above
    # inbounds = relationship("PanelInbound", back_populates="panel", cascade="all, delete-orphan")
    # health_checks = relationship("PanelHealthCheck", back_populates="panel", cascade="all, delete-orphan") 

    def __repr__(self) -> str:
        return f"<Panel(id={self.id}, name='{self.name}', url='{self.url}')>" 