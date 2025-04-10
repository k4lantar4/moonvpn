from datetime import datetime
from typing import List, Optional
import enum

from sqlalchemy import (
    String, Text, Boolean, Integer, DateTime, func, BigInteger,
    ForeignKey, Enum as SQLAlchemyEnum
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database.session import Base
# Import related models for type hinting if needed (using string forward references otherwise)
# from .user import User
# from .plan import Plan
# from .order import Order
# from .panel import Panel
# from .panel_inbound import PanelInbound
# from .location import Location
# from .client_migration import ClientMigration

class ClientStatus(enum.Enum):
    ACTIVE = 'ACTIVE'
    EXPIRED = 'EXPIRED'
    DISABLED = 'DISABLED'
    FROZEN = 'FROZEN'

class ClientProtocol(enum.Enum):
    VMESS = 'VMESS'
    VLESS = 'VLESS'
    TROJAN = 'TROJAN'
    SHADOWSOCKS = 'SHADOWSOCKS'

class ClientAccount(Base):
    """Model for user VPN client accounts/subscriptions using Mapped syntax."""
    
    __tablename__ = "clients"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    plan_id: Mapped[int] = mapped_column(ForeignKey("plans.id"), nullable=False)
    order_id: Mapped[Optional[int]] = mapped_column(ForeignKey("orders.id"), nullable=True)
    panel_id: Mapped[int] = mapped_column(ForeignKey("panels.id"), nullable=False)
    inbound_id: Mapped[int] = mapped_column(ForeignKey("panel_inbounds.id"), nullable=False, index=True)
    panel_native_identifier: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True, comment="Identifier used by the panel API (e.g., email, uuid, password, internal ID)")
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"), nullable=False)
    client_uuid: Mapped[str] = mapped_column(String(36), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    remark: Mapped[str] = mapped_column(String(255), nullable=False)
    expire_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    traffic: Mapped[int] = mapped_column(BigInteger, nullable=False)
    used_traffic: Mapped[Optional[int]] = mapped_column(BigInteger, default=None, nullable=True)
    subscription_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    qrcode_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[Optional[ClientStatus]] = mapped_column(SQLAlchemyEnum(ClientStatus, name='client_status_enum'), default=None, nullable=True)
    protocol: Mapped[ClientProtocol] = mapped_column(SQLAlchemyEnum(ClientProtocol, name='client_protocol_enum'), nullable=False)
    network: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    port: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tls: Mapped[Optional[bool]] = mapped_column(Boolean, default=None, nullable=True)
    security: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    config_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    freeze_start: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    freeze_end: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_trial: Mapped[Optional[bool]] = mapped_column(Boolean, default=None, nullable=True)
    auto_renew: Mapped[Optional[bool]] = mapped_column(Boolean, default=None, nullable=True)
    last_online: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_notified: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    original_client_uuid: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    original_remark: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    custom_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    migration_count: Mapped[Optional[int]] = mapped_column(Integer, default=None, nullable=True)
    previous_panel_id: Mapped[Optional[int]] = mapped_column(ForeignKey("panels.id"), nullable=True)
    migration_history: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=None, nullable=True)
    
    # Relationships (Forward references as strings)
    user: Mapped["User"] = relationship(back_populates="client_accounts")
    plan: Mapped["Plan"] = relationship(back_populates="client_accounts")
    order: Mapped[Optional["Order"]] = relationship(back_populates="client_accounts")
    panel: Mapped["Panel"] = relationship(foreign_keys=[panel_id], back_populates="client_accounts")
    previous_panel: Mapped[Optional["Panel"]] = relationship(foreign_keys=[previous_panel_id]) # Consider adding back_populates if needed in Panel
    inbound: Mapped["PanelInbound"] = relationship(foreign_keys=[inbound_id], back_populates="client_accounts")
    location: Mapped["Location"] = relationship(back_populates="client_accounts")
    # Corrected back_populates assuming ClientMigration model has a 'client' relationship
    migrations: Mapped[List["ClientMigration"]] = relationship(back_populates="client") 

    def __repr__(self) -> str:
        return f"<ClientAccount(id={self.id}, user_id={self.user_id}, remark='{self.remark}')>" 