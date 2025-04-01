# Import necessary types from typing and pydantic
from typing import Optional
from pydantic import BaseModel, ConfigDict
from decimal import Decimal # Use Decimal for precise price representation

# --- Plan Schemas ---

# Define the base schema for Plan properties.
class PlanBase(BaseModel):
    """
    Shared base properties for a subscription plan.
    """
    name: str
    price: Decimal # Use Decimal for accurate currency values
    duration_days: int
    traffic_limit_gb: Optional[int] = None # Optional, None means unlimited
    description: Optional[str] = None
    is_active: bool = True # Default to active

# Define the schema for creating a new plan. Inherits from PlanBase.
class PlanCreate(PlanBase):
    """
    Properties required to create a new plan.
    """
    # All required fields are in PlanBase for now.
    pass

# Define the schema for updating an existing plan. Inherits from PlanBase.
# All fields are optional for partial updates.
class PlanUpdate(BaseModel):
    """
    Properties required to update an existing plan.
    All fields are optional.
    """
    name: Optional[str] = None
    price: Optional[Decimal] = None
    duration_days: Optional[int] = None
    traffic_limit_gb: Optional[int] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

# Define the base schema for plan properties stored in the database. Inherits from PlanBase.
class PlanInDBBase(PlanBase):
    """
    Base properties of a plan as stored in the database, including the ID.
    """
    id: int

    # Pydantic V2 configuration using model_config
    model_config = ConfigDict(
        from_attributes=True # Enable ORM mode (reading data from model attributes)
    )

# Define the schema for properties returned to the client (API responses). Inherits from PlanInDBBase.
class Plan(PlanInDBBase):
    """
    Properties of a plan to be returned to the client.
    """
    # No additional fields needed for client response beyond PlanInDBBase for now.
    pass

# Define the schema representing a plan fully stored in the database.
class PlanInDB(PlanInDBBase):
    """
    Properties of a plan as fully represented in the database.
    """
    # No additional fields needed beyond PlanInDBBase for now.
    pass 