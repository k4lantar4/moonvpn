"""Model for storing details about inbounds fetched from panels."""

from datetime import datetime
from typing import Optional, Dict, Any, List

from sqlalchemy import (
    String, Text, Boolean, Integer, DateTime, func, BigInteger,
    ForeignKey, Index, JSON, Column
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database.session import Base
# from typing import TYPE_CHECKING
# if TYPE_CHECKING:
#     from .panel import Panel
#     from .client_account import ClientAccount

class PanelInbound(Base):
    """Represents an inbound configuration synced from a VPN panel using Mapped syntax."""
    
    __tablename__ = "panel_inbounds"

    id = Column(Integer, primary_key=True, index=True)
    panel_id = Column(Integer, ForeignKey("panels.id", ondelete="CASCADE"), nullable=False, index=True)
    inbound_id_panel = Column(Integer, nullable=False, comment="ID of the inbound on the panel itself")
    tag = Column(String(255), nullable=False, comment="Inbound tag name on the panel")
    protocol = Column(String(50), nullable=False, comment="e.g., vmess, vless, trojan")
    port = Column(Integer, nullable=False)
    listen = Column(String(255), nullable=True, comment="Listen IP address")
    settings = Column(JSON, nullable=True, comment="Raw settings JSON from the panel API")
    stream_settings = Column(JSON, nullable=True, comment="Raw stream settings JSON from the panel API")
    total_gb = Column(BigInteger, nullable=True, default=0, comment="Total traffic limit in bytes (from panel, 0 means unlimited)")
    expiry_time = Column(BigInteger, nullable=True, default=0, comment="Expiry timestamp (milliseconds) (from panel, 0 means no limit)")
    status = Column(Boolean, nullable=False, default=True, comment="Whether this inbound is active/enabled on the panel")
    remark = Column(Text, nullable=True, comment="Panel's description/remark for the inbound") # Added based on common XUI fields

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    panel = relationship("Panel", back_populates="inbounds")
    # Relationship to ClientAccount
    client_accounts: Mapped[List["ClientAccount"]] = relationship(back_populates="inbound")

    def __repr__(self):
        return f"<PanelInbound(id={self.id}, panel_id={self.panel_id}, tag='{self.tag}')>"

    # Removed helper properties as SQLAlchemy handles JSON parsing
    # @property
    # def parsed_settings(self) -> Optional[Dict[str, Any]]: ...
    # @property
    # def parsed_stream_settings(self) -> Optional[Dict[str, Any]]: ... 