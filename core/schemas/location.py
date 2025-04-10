from pydantic import BaseModel

class LocationBase(BaseModel):
    name: str
    flag: str | None = None

class LocationCreate(LocationBase):
    pass

class LocationUpdate(LocationBase):
    name: str | None = None
    # flag can also be updated

class LocationInDBBase(LocationBase):
    id: int

    class Config:
        orm_mode = True
        # from_attributes = True

class Location(LocationInDBBase):
    pass 