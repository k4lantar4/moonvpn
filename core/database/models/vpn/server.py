"""
Server model for managing VPN servers and their configurations.
"""

from typing import Optional, List, Dict, Any
from sqlalchemy import String, Integer, Boolean, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
import enum

from ..base import BaseModel

class ServerStatus(str, enum.Enum):
    """Server status enumeration."""
    ONLINE = "online"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"
    ERROR = "error"

class ServerType(str, enum.Enum):
    """Server type enumeration."""
    VPN = "vpn"
    PROXY = "proxy"
    CUSTOM = "custom"

class Server(BaseModel):
    """
    Server model for managing VPN servers.
    
    Attributes:
        name: Server name
        type: Server type
        status: Server status
        hostname: Server hostname
        ip_address: Server IP address
        port: Server port
        is_active: Whether the server is active
        location: Server location
        bandwidth: Server bandwidth
        max_connections: Maximum number of connections
        current_connections: Current number of connections
        last_check: Last health check timestamp
        metadata: Additional server data
    """
    
    # Server identification
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[ServerType] = mapped_column(Enum(ServerType), nullable=False)
    status: Mapped[ServerStatus] = mapped_column(Enum(ServerStatus), nullable=False)
    
    # Server details
    hostname: Mapped[str] = mapped_column(String(255), nullable=False)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False)
    port: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Server specifications
    location: Mapped[str] = mapped_column(String(100), nullable=False)
    bandwidth: Mapped[int] = mapped_column(Integer, nullable=False)
    max_connections: Mapped[int] = mapped_column(Integer, nullable=False)
    current_connections: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Monitoring
    last_check: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    # Relationships
    vpn_accounts: Mapped[List["VPNAccount"]] = relationship(back_populates="server")
    metrics: Mapped[List["SystemMetric"]] = relationship(back_populates="server")
    configs: Mapped[List["SystemConfig"]] = relationship(back_populates="server")
    
    def __repr__(self) -> str:
        """String representation of the server."""
        return f"<Server(name={self.name}, type={self.type})>" 