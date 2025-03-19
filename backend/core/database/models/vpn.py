"""VPN account models for managing VPN services."""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Integer, Float, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from .base import Base

class AccountStatus(str, enum.Enum):
    """VPN account status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"

class VPNAccount(Base):
    """VPN account model for managing VPN services."""
    
    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Account information
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(128), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(254), nullable=True)
    
    # Account status
    status: Mapped[AccountStatus] = mapped_column(
        Enum(AccountStatus),
        default=AccountStatus.INACTIVE,
        nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Traffic limits
    traffic_limit: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # in bytes
    traffic_used: Mapped[int] = mapped_column(Integer, default=0)  # in bytes
    
    # Connection limits
    max_connections: Mapped[int] = mapped_column(Integer, default=1)
    current_connections: Mapped[int] = mapped_column(Integer, default=0)
    
    # Server information
    server_id: Mapped[Optional[int]] = mapped_column(ForeignKey("server.id"), nullable=True)
    
    # User relationship
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    
    # Timestamps
    last_connection: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    expiry_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="vpn_accounts")
    server: Mapped[Optional["Server"]] = relationship("Server", back_populates="accounts")
    traffic_logs: Mapped[List["TrafficLog"]] = relationship(
        "TrafficLog",
        back_populates="account",
        lazy="selectin"
    )
    
    # Methods
    def __repr__(self) -> str:
        """String representation of the VPN account."""
        return f"<VPNAccount {self.username}>"
    
    @property
    def traffic_remaining(self) -> Optional[int]:
        """Get remaining traffic in bytes."""
        if self.traffic_limit is None:
            return None
        return max(0, self.traffic_limit - self.traffic_used)
    
    @property
    def is_expired(self) -> bool:
        """Check if account is expired."""
        if self.expiry_date is None:
            return False
        return datetime.now(self.expiry_date.tzinfo) > self.expiry_date
    
    def can_connect(self) -> bool:
        """Check if account can connect."""
        return (
            self.is_active
            and not self.is_expired
            and self.status == AccountStatus.ACTIVE
            and self.current_connections < self.max_connections
            and (self.traffic_remaining is None or self.traffic_remaining > 0)
        )

class Server(Base):
    """VPN server model."""
    
    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Server information
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    host: Mapped[str] = mapped_column(String(255), nullable=False)
    port: Mapped[int] = mapped_column(Integer, nullable=False)
    protocol: Mapped[str] = mapped_column(String(20), nullable=False)
    
    # Server status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_maintenance: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Server metrics
    load: Mapped[float] = mapped_column(Float, default=0.0)
    uptime: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Relationships
    accounts: Mapped[List["VPNAccount"]] = relationship(
        "VPNAccount",
        back_populates="server",
        lazy="selectin"
    )
    
    # Methods
    def __repr__(self) -> str:
        """String representation of the server."""
        return f"<Server {self.name}>"

class TrafficLog(Base):
    """Traffic usage log model."""
    
    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Traffic information
    bytes_sent: Mapped[int] = mapped_column(Integer, default=0)
    bytes_received: Mapped[int] = mapped_column(Integer, default=0)
    
    # Timestamps
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # Relationships
    account_id: Mapped[int] = mapped_column(ForeignKey("vpnaccount.id"), nullable=False)
    account: Mapped["VPNAccount"] = relationship("VPNAccount", back_populates="traffic_logs")
    
    # Methods
    def __repr__(self) -> str:
        """String representation of the traffic log."""
        return f"<TrafficLog {self.account.username} {self.timestamp}>" 