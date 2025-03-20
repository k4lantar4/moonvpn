"""
Pydantic schemas for security models.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, constr

class PermissionBase(BaseModel):
    name: str
    description: Optional[str] = None

class PermissionCreate(PermissionBase):
    pass

class Permission(PermissionBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None

class RoleCreate(RoleBase):
    permission_ids: List[int]

class Role(RoleBase):
    id: int
    created_at: datetime
    updated_at: datetime
    permissions: List[Permission]

    class Config:
        orm_mode = True

class UserBase(BaseModel):
    username: str
    email: EmailStr
    is_active: bool = True
    is_verified: bool = False
    two_factor_enabled: bool = False

class UserCreate(UserBase):
    password: constr(min_length=8)
    role_id: int

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[constr(min_length=8)] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    two_factor_enabled: Optional[bool] = None
    role_id: Optional[int] = None

class User(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime]
    role: Role

    class Config:
        orm_mode = True

class UserSessionBase(BaseModel):
    ip_address: str
    user_agent: str
    is_active: bool = True

class UserSessionCreate(UserSessionBase):
    user_id: int
    token: str
    refresh_token: str
    expires_at: datetime

class UserSession(UserSessionBase):
    id: int
    created_at: datetime
    last_activity: datetime
    expires_at: datetime
    user: User

    class Config:
        orm_mode = True

class SecurityEventBase(BaseModel):
    event_type: str
    severity: str
    description: str
    ip_address: str
    user_id: Optional[int] = None
    metadata: Optional[str] = None

class SecurityEventCreate(SecurityEventBase):
    pass

class SecurityEvent(SecurityEventBase):
    id: int
    created_at: datetime
    user: Optional[User] = None

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class TokenPayload(BaseModel):
    sub: int
    exp: datetime
    type: str
    role: str 