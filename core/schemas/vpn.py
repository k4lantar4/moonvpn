"""
VPN schemas for request/response models.
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class ServerBase(BaseModel):
    """Base server schema."""
    name: str = Field(..., min_length=3, max_length=100)
    host: str
    port: int = Field(..., ge=1, le=65535)
    protocol: str = Field(..., pattern="^(tcp|udp|ws|tls)$")
    status: str = "active"
    is_active: bool = True
    location: str
    load: float = Field(0.0, ge=0.0, le=100.0)
    bandwidth_limit: Optional[int] = None
    current_connections: int = 0
    max_connections: int = 1000
    last_check: Optional[datetime] = None
    metadata: Optional[dict] = None

class ServerCreate(ServerBase):
    """Server creation schema."""
    pass

class ServerUpdate(BaseModel):
    """Server update schema."""
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    host: Optional[str] = None
    port: Optional[int] = Field(None, ge=1, le=65535)
    protocol: Optional[str] = Field(None, pattern="^(tcp|udp|ws|tls)$")
    status: Optional[str] = None
    is_active: Optional[bool] = None
    location: Optional[str] = None
    load: Optional[float] = Field(None, ge=0.0, le=100.0)
    bandwidth_limit: Optional[int] = None
    max_connections: Optional[int] = None
    metadata: Optional[dict] = None

class Server(ServerBase):
    """Server response schema."""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class VPNAccountBase(BaseModel):
    """Base VPN account schema."""
    user_id: int
    server_id: int
    status: str = "active"
    is_active: bool = True
    traffic_limit: int = 0
    traffic_used: int = 0
    expire_at: Optional[datetime] = None
    last_connect: Optional[datetime] = None
    last_disconnect: Optional[datetime] = None
    metadata: Optional[dict] = None

class VPNAccountCreate(VPNAccountBase):
    """VPN account creation schema."""
    pass

class VPNAccountUpdate(BaseModel):
    """VPN account update schema."""
    status: Optional[str] = None
    is_active: Optional[bool] = None
    traffic_limit: Optional[int] = None
    expire_at: Optional[datetime] = None
    metadata: Optional[dict] = None

class VPNAccount(VPNAccountBase):
    """VPN account response schema."""
    id: int
    created_at: datetime
    updated_at: datetime
    server: Server

    model_config = ConfigDict(from_attributes=True)

class VPNAccountList(BaseModel):
    """VPN account list response schema."""
    total: int
    accounts: List[VPNAccount]
    page: int
    size: int
    pages: int

class VPNAccountStats(BaseModel):
    """VPN account statistics schema."""
    account_id: int
    traffic_used: int
    traffic_limit: int
    connection_count: int
    last_24h_traffic: int
    last_7d_traffic: int
    last_30d_traffic: int
    uptime: Optional[float] = None
    last_connect: Optional[datetime] = None
    last_disconnect: Optional[datetime] = None
    current_ip: Optional[str] = None
    current_location: Optional[str] = None
    current_protocol: Optional[str] = None
    current_port: Optional[int] = None
    current_server: Optional[str] = None
    current_server_location: Optional[str] = None
    current_server_load: Optional[float] = None
    current_server_status: Optional[str] = None
    current_server_protocol: Optional[str] = None
    current_server_port: Optional[int] = None
    current_server_bandwidth_limit: Optional[int] = None
    current_server_current_connections: Optional[int] = None
    current_server_max_connections: Optional[int] = None
    current_server_last_check: Optional[datetime] = None
    current_server_metadata: Optional[dict] = None
    metadata: Optional[dict] = None 