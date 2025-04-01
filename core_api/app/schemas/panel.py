# Import necessary types from typing and pydantic
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

# --- Panel Schemas ---

# Define the base schema for Panel properties.
class PanelBase(BaseModel):
    """
    Shared base properties for a V2Ray panel.
    """
    name: str
    api_url: str
    username: str
    # Password is included in the base for creation/update internal logic
    # but excluded from response models.
    # password: str # Handled in specialized schemas
    description: Optional[str] = None
    is_active: bool = True

# Define the schema for creating a new panel.
# Explicitly includes password.
class PanelCreate(PanelBase):
    """
    Properties required to create a new panel.
    Includes the password field needed for initial setup.
    """
    password: str # Password is required for creation

# Define the schema for updating an existing panel.
# All fields are optional, including password.
class PanelUpdate(BaseModel):
    """
    Properties required to update an existing panel.
    All fields are optional.
    """
    name: Optional[str] = None
    api_url: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None # Allow password update
    description: Optional[str] = None
    is_active: Optional[bool] = None

# Define the base schema for panel properties stored in the database.
# Inherits from PanelBase but excludes the password.
class PanelInDBBase(PanelBase):
    """
    Base properties of a panel as stored in the database, including the ID.
    Excludes sensitive fields like password.
    """
    id: int
    # Exclude password from database representation returned by API
    password: Optional[str] = Field(None, exclude=True) # Exclude password field

    # Pydantic V2 configuration
    model_config = ConfigDict(
        from_attributes=True # Enable ORM mode
    )

# Define the schema for properties returned to the client (API responses).
# Inherits from PanelInDBBase (which excludes password).
class Panel(PanelInDBBase):
    """
    Properties of a panel to be returned to the client.
    Excludes sensitive information like the password.
    """
    # Inherits fields from PanelInDBBase (ID, name, api_url, username, description, is_active)
    pass

# Define the schema representing a panel fully stored in the database.
# This might be used internally and could potentially include the password
# if needed for specific backend operations, but usually PanelInDBBase is sufficient.
class PanelInDB(PanelInDBBase):
    """
    Properties of a panel as fully represented in the database.
    Typically used internally. For API responses, use Panel schema.
    """
    # For internal use, we might re-include password if necessary for CRUD logic
    # that doesn't use PanelCreate/Update, but it's generally safer to handle
    # password separately during create/update operations.
    password: str # Re-include password for internal representation if needed
    pass 