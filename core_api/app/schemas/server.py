from typing import Optional, List, Dict, Any
from pydantic import BaseModel, validator, Field, IPvAnyAddress
from datetime import datetime

# --- Server Schemas ---

# Base properties shared by other schemas
class ServerBase(BaseModel):
    """Base schema for server data."""
    name: str = Field(..., min_length=1, max_length=100, description="Server name")
    ip_address: IPvAnyAddress = Field(..., description="Server IP address (v4 or v6)")
    hostname: Optional[str] = Field(None, min_length=1, max_length=255, description="Server hostname (optional)")
    description: Optional[str] = Field(None, description="Additional notes about the server")
    is_active: bool = Field(True, description="Whether the server is active")
    location_id: Optional[int] = Field(None, description="Foreign key to location")

# Properties to receive via API on creation
class ServerCreate(ServerBase):
    """Schema for creating a new server."""
    pass # Inherits all fields from ServerBase

# Properties to receive via API on update
class ServerUpdate(BaseModel):
    """Schema for updating an existing server."""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Server name")
    ip_address: Optional[IPvAnyAddress] = Field(None, description="Server IP address (v4 or v6)")
    hostname: Optional[str] = Field(None, min_length=1, max_length=255, description="Server hostname")
    description: Optional[str] = Field(None, description="Additional notes about the server")
    is_active: Optional[bool] = Field(None, description="Whether the server is active")
    location_id: Optional[int] = Field(None, description="Foreign key to location")

# Properties shared by models stored in DB
class ServerInDBBase(ServerBase):
    """Base schema for server data from the database."""
    id: int = Field(..., description="Unique identifier for the server")
    created_at: datetime = Field(..., description="When the server was created")
    updated_at: Optional[datetime] = Field(None, description="When the server was last updated")

    class Config:
        orm_mode = True

# Properties to return to client
class Server(ServerInDBBase):
    """Schema for server data returned from the API."""
    pass # Include all fields from ServerInDBBase

# Properties stored in DB
class ServerInDB(ServerInDBBase):
    """Schema for server data stored in the database."""
    pass

# Schema for executing commands on a server
class ServerCommandExecute(BaseModel):
    """Schema for executing a command on a server."""
    command: str = Field(..., min_length=1, description="Command to execute")

# Schema for server status information
class ServerStatus(BaseModel):
    """Schema for server status information."""
    server_id: int
    server_name: str
    ip_address: str
    is_up: bool
    latency_ms: Optional[float] = None
    checked_at: str

# Schema for server metrics
class ServerMetrics(BaseModel):
    """Schema for server performance metrics."""
    server_id: int
    cpu_usage_percent: Optional[float] = None
    memory_usage_percent: Optional[float] = None
    active_connections: Optional[int] = None
    collected_at: str

# Schema for system information
class ServerSystemInfo(BaseModel):
    """Schema for detailed system information."""
    server_id: int
    cpu_model: str
    memory_info: str
    disk_usage: str
    uptime: str
    load_average: str
    os_info: str
    xray_running: bool
    collected_at: str

# Schema for command execution result
class ServerCommandResult(BaseModel):
    """Schema for command execution results."""
    command: str
    exit_status: int
    success: bool
    stdout: str
    stderr: str
    executed_at: str 