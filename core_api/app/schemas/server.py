from pydantic import BaseModel, Field, IPvAnyAddress
from typing import Optional

# --- Server Schemas ---

# Base properties shared by other schemas
class ServerBase(BaseModel):
    name: str = Field(..., max_length=100)
    ip_address: IPvAnyAddress # Use Pydantic's IP address validation
    hostname: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    is_active: bool = True
    location_id: Optional[int] = None

# Properties to receive via API on creation
class ServerCreate(ServerBase):
    pass # Inherits all fields from ServerBase

# Properties to receive via API on update
class ServerUpdate(ServerBase):
    name: Optional[str] = Field(None, max_length=100) # Make fields optional for update
    ip_address: Optional[IPvAnyAddress] = None
    is_active: Optional[bool] = None
    # hostname, description, location_id already optional in Base

# Properties shared by models stored in DB
class ServerInDBBase(ServerBase):
    id: int
    created_at: Optional[str] = None # Adjust type if needed (e.g., datetime)
    updated_at: Optional[str] = None

    class Config:
        orm_mode = True # Compatibility with ORM objects

# Properties to return to client
class Server(ServerInDBBase):
    pass # Include all fields from ServerInDBBase

# Properties stored in DB
class ServerInDB(ServerInDBBase):
    pass 