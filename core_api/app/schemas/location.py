# Import necessary types from typing and pydantic
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, validator

# --- Location Schemas ---

# Define the base schema for Location properties.
class LocationBase(BaseModel):
    """
    Shared base properties for a geographical location.
    """
    name: str
    country_code: str = Field(..., min_length=2, max_length=2, description="ISO 3166-1 alpha-2 country code")
    flag_emoji: Optional[str] = Field(None, max_length=10)
    is_active: bool = True

    # Validator to ensure country_code is uppercase
    @validator('country_code', pre=True, always=True)
    def uppercase_country_code(cls, v):
        if isinstance(v, str):
            return v.upper()
        return v

# Define the schema for creating a new location. Inherits from LocationBase.
class LocationCreate(LocationBase):
    """
    Properties required to create a new location.
    """
    pass

# Define the schema for updating an existing location. Inherits from LocationBase.
# All fields are optional for partial updates.
class LocationUpdate(BaseModel):
    """
    Properties required to update an existing location.
    All fields are optional.
    """
    name: Optional[str] = None
    country_code: Optional[str] = Field(None, min_length=2, max_length=2, description="ISO 3166-1 alpha-2 country code")
    flag_emoji: Optional[str] = Field(None, max_length=10)
    is_active: Optional[bool] = None

    # Validator to ensure country_code is uppercase if provided
    @validator('country_code', pre=True, always=True)
    def uppercase_country_code_update(cls, v):
        if isinstance(v, str):
            return v.upper()
        return v

# Define the base schema for location properties stored in the database. Inherits from LocationBase.
class LocationInDBBase(LocationBase):
    """
    Base properties of a location as stored in the database, including the ID.
    """
    id: int

    # Pydantic V2 configuration
    model_config = ConfigDict(
        from_attributes=True # Enable ORM mode
    )

# Define the schema for properties returned to the client (API responses). Inherits from LocationInDBBase.
class Location(LocationInDBBase):
    """
    Properties of a location to be returned to the client.
    """
    pass

# Define the schema representing a location fully stored in the database.
class LocationInDB(LocationInDBBase):
    """
    Properties of a location as fully represented in the database.
    """
    pass 