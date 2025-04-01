from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Any, TYPE_CHECKING

# --- Role Schemas ---

# Base properties shared by all related schemas
class RoleBase(BaseModel):
    """
    Shared base properties for a role.
    """
    name: str
    description: Optional[str] = None

# Properties required for creating a new role
class RoleCreate(RoleBase):
    """
    Properties required to create a new role.
    """
    pass

# Properties required for updating a role
class RoleUpdate(RoleBase):
    """
    Properties required to update an existing role.
    All fields are optional to allow partial updates.
    """
    name: Optional[str] = None # Make fields optional for updates

# Properties stored in the database
class RoleInDBBase(RoleBase):
    """
    Base properties of a role as stored in the database.
    Includes the database primary key 'id' and permission relationships.
    """
    id: int
    
    if TYPE_CHECKING:
        # For type checking only
        from .permission import Permission
        permissions: List[Permission] = []
    else:
        # For runtime
        permissions: List[Any] = []

    model_config = ConfigDict(
        from_attributes=True
    )

# Properties to return to the client (API response)
class Role(RoleInDBBase):
    """
    Properties of a role to be returned to the client via the API.
    """
    pass

# Properties stored in DB (might include relationships later)
class RoleInDB(RoleInDBBase):
    """
    Properties of a role as fully represented in the database.
    """
    pass 