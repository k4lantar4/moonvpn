# Import Optional for optional fields and BaseModel from Pydantic
from typing import Optional, List, Any, TYPE_CHECKING
from pydantic import BaseModel, ConfigDict

# --- Permission Schemas ---

# Define the base schema for Permission properties shared across different operations.
class PermissionBase(BaseModel):
    """
    Shared base properties for a permission.
    Includes the essential fields required for identifying and describing a permission.
    """
    # Name of the permission (e.g., 'create_user', 'manage_settings')
    name: str
    # Optional detailed description of what the permission allows.
    description: Optional[str] = None

# Define the schema for creating a new permission. Inherits from PermissionBase.
class PermissionCreate(PermissionBase):
    """
    Properties required to create a new permission.
    Currently identical to PermissionBase, but provides structure for potential future additions.
    """
    # No additional fields needed for creation beyond the base fields for now.
    pass

# Define the schema for updating an existing permission. Inherits from PermissionBase.
# All fields are optional because the client might only want to update specific fields.
class PermissionUpdate(PermissionBase):
    """
    Properties required to update an existing permission.
    All fields are optional to allow partial updates.
    """
    # Override base fields to make them optional for updates.
    name: Optional[str] = None
    description: Optional[str] = None

# Define the base schema for permission properties stored in the database. Inherits from PermissionBase.
class PermissionInDBBase(PermissionBase):
    """
    Base properties of a permission as stored in the database.
    Includes the database primary key 'id'.
    """
    # The unique identifier for the permission in the database.
    id: int
    
    if TYPE_CHECKING:
        # For type checking only
        from .role import Role
        roles: List[Role] = []
    else:
        # For runtime
        roles: List[Any] = []

    # Pydantic configuration settings.
    model_config = ConfigDict(
        from_attributes=True  # Enable creating Pydantic models from ORM objects.
    )

# Define the schema for properties returned to the client (API responses). Inherits from PermissionInDBBase.
class Permission(PermissionInDBBase):
    """
    Properties of a permission to be returned to the client via the API.
    Represents the full permission object as seen by the end-user or frontend.
    """
    # No additional fields needed beyond what's inherited from PermissionInDBBase for now.
    pass

# Define the schema representing a permission fully stored in the database, potentially including relationships later.
class PermissionInDB(PermissionInDBBase):
    """
    Properties of a permission as fully represented in the database.
    This schema can be extended later to include relationships if needed.
    """
    # No additional fields needed beyond what's inherited from PermissionInDBBase for now.
    pass