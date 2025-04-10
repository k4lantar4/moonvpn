"""Pydantic models (Schemas) for Client Accounts."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, UUID4, EmailStr, model_validator
from datetime import datetime

from core.schemas.plan import Plan # Import Plan schema for nesting
from core.schemas.user import User # Import User schema for nesting

# Enum for Client Account Status (assuming it's defined in models or constants)
# from core.database.models.client_account import ClientAccountStatus
from enum import Enum
class ClientAccountStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    EXPIRED = "EXPIRED"
    SUSPENDED = "SUSPENDED"
    CANCELLED = "CANCELLED"
    TRIAL = "TRIAL"
    FROZEN = "FROZEN"

class ClientAccountBase(BaseModel):
    remark: str = Field(..., max_length=100)
    client_uuid: UUID4
    user_id: int
    panel_id: int
    plan_id: int
    panel_inbound_id: int
    allocated_traffic: int = Field(..., ge=0) # In bytes
    used_traffic: int = Field(0, ge=0) # In bytes
    start_date: Optional[datetime] = None
    expire_date: Optional[datetime] = None
    status: ClientAccountStatus = ClientAccountStatus.INACTIVE
    subscription_url: Optional[str] = None
    panel_client_id: Optional[str] = None # Panel's internal ID for the client
    notes: Optional[str] = None

class ClientAccountCreate(ClientAccountBase):
    # start_date and expire_date might be set upon creation
    start_date: datetime
    expire_date: datetime
    pass

class ClientAccountUpdate(BaseModel):
    remark: Optional[str] = Field(None, max_length=100)
    client_uuid: Optional[UUID4] = None
    user_id: Optional[int] = None
    panel_id: Optional[int] = None
    plan_id: Optional[int] = None
    panel_inbound_id: Optional[int] = None
    allocated_traffic: Optional[int] = Field(None, ge=0)
    used_traffic: Optional[int] = Field(None, ge=0)
    start_date: Optional[datetime] = None
    expire_date: Optional[datetime] = None
    status: Optional[ClientAccountStatus] = None
    subscription_url: Optional[str] = None
    panel_client_id: Optional[str] = None
    notes: Optional[str] = None

class ClientAccountInDBBase(ClientAccountBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Schema for representing a ClientAccount in API responses, with nested info
class ClientAccount(ClientAccountInDBBase):
    user: Optional[User] = None
    plan: Optional[Plan] = None
    # Add panel and inbound details if needed
    # panel: Optional[Panel] = None
    # inbound: Optional[PanelInbound] = None

# Schema for updating traffic usage
class ClientTrafficUpdate(BaseModel):
    used_traffic: int = Field(..., ge=0) 