from pydantic import BaseModel, Field
from typing import Optional, List
import datetime # Import datetime for type hints

# --- Plan Category Schemas ---

# Base properties
class PlanCategoryBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    is_active: bool = True
    sort_order: int = 100

# Properties for creation
class PlanCategoryCreate(PlanCategoryBase):
    pass

# Properties for update
class PlanCategoryUpdate(PlanCategoryBase):
    name: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None

# Properties shared by models stored in DB - used for relationships
class PlanCategoryInDBBase(PlanCategoryBase):
    id: int
    # Use Optional[datetime.datetime] for timestamps
    created_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = None

    class Config:
        orm_mode = True # Use orm_mode = True for Pydantic v1 compatibility if needed
        # from_attributes=True # For Pydantic v2

# Properties to return to client (potentially including relationships)
class PlanCategory(PlanCategoryInDBBase):
    # If you want to include related plans when fetching a category:
    # plans: List['Plan'] = [] # Requires Plan schema to be defined/imported carefully
    pass

# Properties stored in DB (if needed separately)
class PlanCategoryInDB(PlanCategoryInDBBase):
    pass

# Forward reference update if needed for relationships (e.g., with Plan schema)
# from .plan import Plan # Import Plan schema
# PlanCategory.model_rebuild() # Update model references for Pydantic v2
# PlanCategory.update_forward_refs() # For Pydantic v1 