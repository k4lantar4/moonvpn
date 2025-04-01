from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime, timedelta
from enum import Enum

# Status enum
class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    FROZEN = "frozen"

# Base schema for Subscription
class SubscriptionBase(BaseModel):
    user_id: int
    plan_id: int
    status: Optional[SubscriptionStatus] = Field(default=SubscriptionStatus.ACTIVE)
    is_frozen: Optional[bool] = Field(default=False)
    auto_renew: Optional[bool] = Field(default=False)
    notes: Optional[str] = None

# Schema for creating a new Subscription
class SubscriptionCreate(SubscriptionBase):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    
    @validator('end_date', pre=True, always=True)
    def set_end_date(cls, v, values):
        """Set end_date based on start_date if not provided."""
        if v:
            return v
        # If end_date not provided but start_date is, calculate based on plan duration (would need to fetch plan)
        # Here we just return None since plan duration would be fetched in the actual service
        return None

# Schema for Freezing a Subscription
class SubscriptionFreeze(BaseModel):
    freeze_end_date: Optional[datetime] = None
    freeze_reason: Optional[str] = None

# Schema for Unfreezing a Subscription
class SubscriptionUnfreeze(BaseModel):
    pass

# Schema for adding a Note to a Subscription
class SubscriptionAddNote(BaseModel):
    note: str = Field(..., min_length=1, max_length=1000)

# Schema for toggling Auto-Renew
class SubscriptionToggleAutoRenew(BaseModel):
    auto_renew: bool
    auto_renew_payment_method: Optional[str] = None

# Schema for changing protocol or location
class SubscriptionChangeProtocolLocation(BaseModel):
    new_inbound_id: Optional[int] = Field(None, description="The ID of the new inbound (protocol) to use")
    new_panel_id: Optional[int] = Field(None, description="The ID of the new panel (location) to use")
    
    @validator('new_inbound_id', 'new_panel_id')
    def validate_has_at_least_one(cls, v, values):
        """Ensure at least one of new_inbound_id or new_panel_id is provided."""
        # On first field validation, we only have this field so we can't check yet
        if 'new_inbound_id' not in values and 'new_panel_id' not in values:
            return v
            
        # On second field validation, check if at least one has a value
        if not v and not values.get('new_inbound_id') and not values.get('new_panel_id'):
            raise ValueError("At least one of new_inbound_id or new_panel_id must be provided")
        return v

# Schema for updating an existing Subscription
class SubscriptionUpdate(BaseModel):
    status: Optional[SubscriptionStatus] = None
    is_frozen: Optional[bool] = None
    freeze_start_date: Optional[datetime] = None
    freeze_end_date: Optional[datetime] = None
    freeze_reason: Optional[str] = None
    auto_renew: Optional[bool] = None
    auto_renew_payment_method: Optional[str] = None
    notes: Optional[str] = None
    end_date: Optional[datetime] = None

# Schema for Subscription in DB
class SubscriptionInDBBase(SubscriptionBase):
    id: int
    is_frozen: bool
    freeze_start_date: Optional[datetime] = None
    freeze_end_date: Optional[datetime] = None
    freeze_reason: Optional[str] = None
    auto_renew: bool
    auto_renew_payment_method: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    
    class Config:
        orm_mode = True

# Schema for Subscription response
class SubscriptionResponse(SubscriptionInDBBase):
    # Additional fields that might be calculated or joined
    days_left: Optional[int] = None
    
    @validator('days_left', pre=True, always=True)
    def calculate_days_left(cls, v, values):
        """Calculate days left based on end_date."""
        if 'end_date' in values and values['end_date']:
            if values['end_date'] > datetime.utcnow():
                return (values['end_date'] - datetime.utcnow()).days
            return 0
        return None 