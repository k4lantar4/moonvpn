from pydantic import BaseModel, ConfigDict
from typing import Optional, List

# --- Role Schemas ---

# Base properties shared by all related schemas
class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None

# Properties required for creating a new role
class RoleCreate(RoleBase):
    pass

# Properties required for updating a role
class RoleUpdate(RoleBase):
    name: Optional[str] = None # Make fields optional for updates

# Properties stored in the database
class RoleInDBBase(RoleBase):
    id: int
    # Add the list of permissions associated with this role
    permissions: List[PermissionSchema] = [] # Default to empty list

    model_config = ConfigDict(
        from_attributes=True
    )

# Properties to return to the client (API response)
class Role(RoleInDBBase):
    pass

# Properties stored in DB (might include relationships later)
class RoleInDB(RoleInDBBase):
    pass

# Import Permission schema to represent nested permissions
from .permission import Permission as PermissionSchema 