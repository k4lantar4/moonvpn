from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

class User(BaseModel):
    """User schema with basic information."""
    id: int
    username: str
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: str = "user"
    is_active: bool = True
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
        
class UserCreate(BaseModel):
    """Schema for user creation."""
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    role: Optional[str] = "user"
    
class UserUpdate(BaseModel):
    """Schema for user update."""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    
class UserResponse(User):
    """User response schema."""
    pass

class UserWithStats(User):
    """User with additional statistics."""
    total_clients: int = 0
    active_clients: int = 0
    total_traffic_gb: float = 0
    
    class Config:
        from_attributes = True 