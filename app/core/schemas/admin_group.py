"""
Admin group schemas for MoonVPN.

This module provides Pydantic models for admin group data validation and serialization.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator

from app.core.database.models.admin import AdminGroupType, NotificationLevel

class AdminGroupBase(BaseModel):
    """Base schema for admin group data."""
    
    name: str = Field(..., description="Name of the admin group")
    description: Optional[str] = Field(None, description="Description of the admin group")
    type: AdminGroupType = Field(..., description="Type of the admin group")
    icon: Optional[str] = Field(None, description="Icon emoji for the admin group")
    notification_level: NotificationLevel = Field(
        default=NotificationLevel.INFO,
        description="Notification level for the group"
    )
    notification_types: List[str] = Field(
        default_factory=list,
        description="Types of notifications the group receives"
    )
    is_active: bool = Field(default=True, description="Whether the group is active")

class AdminGroupCreate(AdminGroupBase):
    """Schema for creating a new admin group."""
    
    chat_id: Optional[int] = Field(None, description="Telegram chat ID of the group")
    
    @validator('notification_types')
    def validate_notification_types(cls, v):
        """Validate notification types."""
        if not v:
            return []
        return list(set(v))  # Remove duplicates

class AdminGroupUpdate(BaseModel):
    """Schema for updating an admin group."""
    
    name: Optional[str] = Field(None, description="Name of the admin group")
    description: Optional[str] = Field(None, description="Description of the admin group")
    type: Optional[AdminGroupType] = Field(None, description="Type of the admin group")
    icon: Optional[str] = Field(None, description="Icon emoji for the admin group")
    notification_level: Optional[NotificationLevel] = Field(
        None,
        description="Notification level for the group"
    )
    notification_types: Optional[List[str]] = Field(
        None,
        description="Types of notifications the group receives"
    )
    is_active: Optional[bool] = Field(None, description="Whether the group is active")
    chat_id: Optional[int] = Field(None, description="Telegram chat ID of the group")
    
    @validator('notification_types')
    def validate_notification_types(cls, v):
        """Validate notification types."""
        if v is None:
            return None
        return list(set(v))  # Remove duplicates

class AdminGroupInDB(AdminGroupBase):
    """Schema for admin group data from database."""
    
    id: int = Field(..., description="Unique identifier of the admin group")
    chat_id: Optional[int] = Field(None, description="Telegram chat ID of the group")
    created_at: datetime = Field(..., description="When the group was created")
    updated_at: datetime = Field(..., description="When the group was last updated")
    
    class Config:
        """Pydantic model configuration."""
        orm_mode = True

class AdminGroupResponse(AdminGroupInDB):
    """Schema for admin group response data."""
    
    member_count: int = Field(..., description="Number of members in the group")
    active_member_count: int = Field(..., description="Number of active members in the group")

class AdminGroupMemberBase(BaseModel):
    """Base schema for admin group member data."""
    
    user_id: int = Field(..., description="Telegram user ID of the member")
    role: str = Field(..., description="Role of the member in the group")
    is_active: bool = Field(default=True, description="Whether the member is active")
    added_by: int = Field(..., description="User ID of who added the member")
    notes: Optional[str] = Field(None, description="Additional notes about the member")

class AdminGroupMemberCreate(AdminGroupMemberBase):
    """Schema for creating a new admin group member."""
    
    group_id: int = Field(..., description="ID of the admin group")

class AdminGroupMemberUpdate(BaseModel):
    """Schema for updating an admin group member."""
    
    role: Optional[str] = Field(None, description="Role of the member in the group")
    is_active: Optional[bool] = Field(None, description="Whether the member is active")
    notes: Optional[str] = Field(None, description="Additional notes about the member")

class AdminGroupMemberInDB(AdminGroupMemberBase):
    """Schema for admin group member data from database."""
    
    id: int = Field(..., description="Unique identifier of the group member")
    group_id: int = Field(..., description="ID of the admin group")
    created_at: datetime = Field(..., description="When the member was added")
    updated_at: datetime = Field(..., description="When the member was last updated")
    
    class Config:
        """Pydantic model configuration."""
        orm_mode = True

class AdminGroupMemberResponse(AdminGroupMemberInDB):
    """Schema for admin group member response data."""
    
    username: Optional[str] = Field(None, description="Telegram username of the member")
    first_name: Optional[str] = Field(None, description="First name of the member")
    last_name: Optional[str] = Field(None, description="Last name of the member")
    added_by_username: Optional[str] = Field(None, description="Username of who added the member")
    added_by_first_name: Optional[str] = Field(None, description="First name of who added the member")
    added_by_last_name: Optional[str] = Field(None, description="Last name of who added the member")

class AdminGroupListResponse(BaseModel):
    """Schema for list of admin groups response."""
    
    groups: List[AdminGroupResponse] = Field(..., description="List of admin groups")
    total_count: int = Field(..., description="Total number of groups")
    active_count: int = Field(..., description="Number of active groups")

class AdminGroupMemberListResponse(BaseModel):
    """Schema for list of admin group members response."""
    
    members: List[AdminGroupMemberResponse] = Field(..., description="List of group members")
    total_count: int = Field(..., description="Total number of members")
    active_count: int = Field(..., description="Number of active members") 