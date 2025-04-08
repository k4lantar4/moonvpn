from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator

class ClientBase(BaseModel):
    """Base schema for clients."""
    user_id: int = Field(..., description="User ID")
    location_id: int = Field(..., description="Location ID")
    panel_id: int = Field(..., description="Panel ID")
    plan_id: int = Field(..., description="Plan ID")
    remark: str = Field(..., description="Client remark")
    status: str = Field(..., description="Client status (ACTIVE, EXPIRED, DISABLED)")
    protocol: str = Field("vmess", description="Connection protocol")
    
    class Config:
        from_attributes = True

class ClientCreate(BaseModel):
    """Schema for client creation."""
    user_id: int = Field(..., description="User ID")
    location_id: int = Field(..., description="Location ID")
    plan_id: int = Field(..., description="Plan ID")
    order_id: Optional[int] = Field(None, description="Order ID")
    custom_name: Optional[str] = Field(None, description="Custom name for the client")
    protocol: str = Field("vmess", description="Connection protocol")
    is_trial: bool = Field(False, description="Whether this is a trial client")
    
class ClientUpdate(BaseModel):
    """Schema for client update."""
    status: Optional[str] = Field(None, description="Client status")
    expire_date: Optional[datetime] = Field(None, description="New expiry date")
    traffic: Optional[float] = Field(None, description="Total allocated traffic")
    
class ClientResponse(ClientBase):
    """Response schema for clients."""
    id: int
    client_uuid: str
    email: str
    traffic: float
    used_traffic: float
    expire_date: datetime
    created_at: datetime
    updated_at: Optional[datetime]
    is_trial: bool
    subscription_url: Optional[str]
    original_location_id: Optional[int]
    original_remark: Optional[str]
    migration_count: int
    location_changes_today: int
    custom_name: Optional[str]
    
    class Config:
        from_attributes = True

class ClientDetailResponse(ClientResponse):
    """Detailed response schema for clients."""
    migration_history: Optional[List[Dict[str, Any]]]
    
    class Config:
        from_attributes = True

class ClientConfigResponse(BaseModel):
    """Response schema for client configuration."""
    id: int
    client_uuid: str
    remark: str
    subscription_url: Optional[str]
    panel_url: str
    connection_details: Dict[str, Any]
    
    class Config:
        from_attributes = True

class ClientTrafficUpdate(BaseModel):
    """Schema for updating client traffic."""
    used_traffic: float = Field(..., description="Used traffic in Gigabytes")

class ClientLocationChange(BaseModel):
    """Schema for changing a client's location."""
    new_location_id: int = Field(..., description="ID of the new location")
    reason: Optional[str] = Field(None, description="Reason for changing location")
    force: bool = Field(False, description="Force the change even if daily limit exceeded (admin only)") 