# Import necessary types from typing and pydantic
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, ConfigDict, Field, UUID4
from datetime import datetime, timedelta
import uuid

# --- Panel Schemas ---

# Define the base schema for Panel properties.
class PanelBase(BaseModel):
    """
    Shared base properties for a V2Ray panel.
    """
    name: str
    api_url: str
    username: str
    # Password is included in the base for creation/update internal logic
    # but excluded from response models.
    # password: str # Handled in specialized schemas
    description: Optional[str] = None
    is_active: bool = True

# Define the schema for creating a new panel.
# Explicitly includes password.
class PanelCreate(PanelBase):
    """
    Properties required to create a new panel.
    Includes the password field needed for initial setup.
    """
    password: str # Password is required for creation

# Define the schema for updating an existing panel.
# All fields are optional, including password.
class PanelUpdate(BaseModel):
    """
    Properties required to update an existing panel.
    All fields are optional.
    """
    name: Optional[str] = None
    api_url: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None # Allow password update
    description: Optional[str] = None
    is_active: Optional[bool] = None

# Define the base schema for panel properties stored in the database.
# Inherits from PanelBase but excludes the password.
class PanelInDBBase(PanelBase):
    """
    Base properties of a panel as stored in the database, including the ID.
    Excludes sensitive fields like password.
    """
    id: int
    # Exclude password from database representation returned by API
    password: Optional[str] = Field(None, exclude=True) # Exclude password field

    # Pydantic V2 configuration
    model_config = ConfigDict(
        from_attributes=True # Enable ORM mode
    )

# Define the schema for properties returned to the client (API responses).
# Inherits from PanelInDBBase (which excludes password).
class Panel(PanelInDBBase):
    """
    Properties of a panel to be returned to the client.
    Excludes sensitive information like the password.
    """
    # Inherits fields from PanelInDBBase (ID, name, api_url, username, description, is_active)
    pass

# Define the schema representing a panel fully stored in the database.
# This might be used internally and could potentially include the password
# if needed for specific backend operations, but usually PanelInDBBase is sufficient.
class PanelInDB(PanelInDBBase):
    """
    Properties of a panel as fully represented in the database.
    Typically used internally. For API responses, use Panel schema.
    """
    # For internal use, we might re-include password if necessary for CRUD logic
    # that doesn't use PanelCreate/Update, but it's generally safer to handle
    # password separately during create/update operations.
    password: str # Re-include password for internal representation if needed
    pass

# --- Base Models --- #

class PanelClientBase(BaseModel):
    email: str = Field(..., description="Email/remark for the client")
    total_gb: Optional[int] = Field(0, description="Total GB limit for the client (0 for unlimited)")
    expire_days: Optional[int] = Field(0, description="Expiry in days from now (0 for never)")
    limit_ip: Optional[int] = Field(0, description="IP limit for the client (0 for unlimited)")

class PanelInboundBase(BaseModel):
    id: int = Field(..., description="Inbound ID")
    protocol: str = Field(..., description="Protocol type (vmess, vless, trojan, etc.)")
    enable: bool = Field(..., description="Whether the inbound is enabled")
    remark: Optional[str] = Field(None, description="Remark/description for the inbound")
    port: int = Field(..., description="Port number")

# --- Request Models --- #

class PanelClientCreate(PanelClientBase):
    client_uuid: Optional[str] = Field(
        None, 
        description="UUID for the client (auto-generated if not provided)"
    )

    def __init__(self, **data):
        super().__init__(**data)
        if not self.client_uuid:
            self.client_uuid = str(uuid.uuid4())

class PanelClientUpdate(BaseModel):
    total_gb: Optional[int] = Field(None, description="Total GB limit (0 for unlimited)")
    expire_days: Optional[int] = Field(None, description="Expiry in days from now (0 for never)")
    limit_ip: Optional[int] = Field(None, description="IP limit (0 for unlimited)")

# --- Response Models --- #

class PanelClientResponse(PanelClientBase):
    id: Optional[str] = Field(None, description="Client ID within the inbound")
    uuid: str = Field(..., description="UUID of the client")
    enable: bool = Field(..., description="Whether the client is enabled")
    created_at: Optional[datetime] = None
    total_used_traffic: Optional[int] = Field(0, description="Used traffic in bytes")
    up: Optional[int] = Field(0, description="Upload traffic in bytes")
    down: Optional[int] = Field(0, description="Download traffic in bytes")
    expiry_time: Optional[int] = Field(None, description="Expiry timestamp")
    inbound_id: Optional[int] = Field(None, description="ID of the inbound this client belongs to")

    class Config:
        from_attributes = True

class PanelInboundResponse(PanelInboundBase):
    up: Optional[int] = Field(0, description="Upload traffic in bytes")
    down: Optional[int] = Field(0, description="Download traffic in bytes")
    total: Optional[int] = Field(0, description="Total traffic in bytes")
    tag: Optional[str] = Field(None, description="Tag for the inbound")
    settings: Optional[Dict[str, Any]] = Field(None, description="Inbound settings")
    stream_settings: Optional[Dict[str, Any]] = Field(None, description="Stream settings")
    sniffing: Optional[Dict[str, Any]] = Field(None, description="Sniffing settings")
    client_count: Optional[int] = Field(0, description="Number of clients in this inbound")
    
    class Config:
        from_attributes = True

class PanelTrafficResponse(BaseModel):
    up: int = Field(..., description="Upload traffic in bytes")
    down: int = Field(..., description="Download traffic in bytes")
    total: int = Field(..., description="Total traffic in bytes")
    enable: bool = Field(..., description="Whether the client is enabled")
    expiry_time: Optional[int] = Field(None, description="Expiry timestamp")
    expiry_status: Optional[bool] = Field(True, description="Whether the client is expired")
    
    class Config:
        from_attributes = True

class PanelClientConfigResponse(BaseModel):
    client_id: Optional[str] = Field(None, description="Client ID within the inbound")
    uuid: str = Field(..., description="UUID of the client")
    email: str = Field(..., description="Email/remark of the client")
    protocol: str = Field(..., description="Protocol type (vmess, vless, trojan, etc.)")
    port: int = Field(..., description="Port number")
    address: str = Field(..., description="Server address")
    network: str = Field("tcp", description="Network type (tcp, ws, etc.)")
    security: str = Field("none", description="Security type (none, tls, etc.)")
    enabled: bool = Field(..., description="Whether the client is enabled")
    inbound_id: int = Field(..., description="ID of the inbound this client belongs to")
    created_at: Optional[datetime] = None
    expire_time: Optional[int] = Field(None, description="Expiry timestamp")
    total_traffic: Optional[int] = Field(0, description="Total traffic limit in bytes")
    used_traffic: Optional[int] = Field(0, description="Used traffic in bytes")
    link: str = Field(..., description="Connection link for the client")
    
    class Config:
        from_attributes = True

class PanelClientQRCodeResponse(BaseModel):
    email: str = Field(..., description="Email/remark of the client")
    protocol: str = Field(..., description="Protocol type (vmess, vless, trojan, etc.)")
    qrcode: str = Field(..., description="Base64 encoded QR code image")
    link: str = Field(..., description="Connection link for the client")
    
    class Config:
        from_attributes = True 