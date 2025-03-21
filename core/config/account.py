"""
VPNAccount model for managing VPN user accounts and connections.
"""

from typing import Optional, List
from sqlalchemy import String, Integer, Boolean, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
import enum

from ..base import BaseModel

class VPNStatus(str, enum.Enum):
    """VPN account status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"
    SUSPENDED = "suspended"

class VPNProtocol(str, enum.Enum):
    """VPN protocol enumeration."""
    OPENVPN = "openvpn"
    WIREGUARD = "wireguard"
    SHADOWSOCKS = "shadowsocks"
    CUSTOM = "custom"

class VPNAccount(BaseModel):
    """
    VPNAccount model for managing VPN user accounts.
    
    Attributes:
        user_id: Reference to user
        server_id: Reference to server
        protocol: VPN protocol
        username: VPN username
        password: VPN password
        status: Account status
        is_active: Whether the account is active
        expires_at: Account expiration timestamp
        last_connected: Last connection timestamp
        metadata: Additional account data
    """
    
    # Account identification
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    server_id: Mapped[int] = mapped_column(ForeignKey("server.id"), nullable=False)
    protocol: Mapped[VPNProtocol] = mapped_column(Enum(VPNProtocol), nullable=False)
    
    # Account details
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[VPNStatus] = mapped_column(Enum(VPNStatus), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    last_connected: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    
    # Additional data
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="vpn_accounts")
    server: Mapped["Server"] = relationship(back_populates="vpn_accounts")
    
    def __repr__(self) -> str:
        """String representation of the VPN account."""
        return f"<VPNAccount(username={self.username}, protocol={self.protocol})>" 