from pydantic import BaseModel

class PanelBase(BaseModel):
    pass # Add common fields if any

class PanelCreate(PanelBase):
    # Add fields required for creation
    name: str
    url: str
    # ... other fields

class PanelUpdate(PanelBase):
    # Add fields allowed for update
    name: str | None = None
    url: str | None = None
    # ... other fields

class PanelInDBBase(PanelBase):
    id: int
    # Add fields present in DB model
    name: str
    url: str
    # ... other fields

    class Config:
        orm_mode = True # For SQLAlchemy 1.x, use from_attributes=True for v2
        # from_attributes = True

# Additional schemas if needed (e.g., Panel)
class Panel(PanelInDBBase):
    pass 