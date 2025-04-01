# Import necessary components for CRUD operations
from sqlalchemy.orm import Session
from typing import Any, Dict, Optional, Union, List

# Import models and schemas
from app.models.location import Location
from app.schemas.location import LocationCreate, LocationUpdate
from app.crud.base import CRUDBase

class CRUDLocation(CRUDBase[Location, LocationCreate, LocationUpdate]):
    def get_by_name(self, db: Session, *, name: str) -> Optional[Location]:
        """ Retrieves a single location by its unique name. """
        return db.query(self.model).filter(self.model.name == name).first()

    # Override get_multi if filtering by active status is common
    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        only_active: bool = False
    ) -> List[Location]:
        query = db.query(self.model)
        if only_active:
            query = query.filter(self.model.is_active == True)
        return query.offset(skip).limit(limit).all()

    # Add any other location-specific methods here (e.g., get children)

# Create a singleton instance
location = CRUDLocation(Location)

# --- Deprecated Individual Functions ---

def get_location(db: Session, location_id: int) -> Optional[Location]:
    """
    Retrieves a single location by its primary key ID.

    Args:
        db: The database session.
        location_id: The ID of the location to retrieve.

    Returns:
        The Location object if found, otherwise None.
    """
    return db.query(Location).filter(Location.id == location_id).first()

def get_locations(db: Session, skip: int = 0, limit: int = 100, only_active: bool = False) -> List[Location]:
    """
    Retrieves a list of locations with pagination and optional filtering for active locations.

    Args:
        db: The database session.
        skip: The number of records to skip.
        limit: The maximum number of records to return.
        only_active: If True, only returns locations where is_active is True.

    Returns:
        A list of Location objects.
    """
    query = db.query(Location)
    if only_active:
        query = query.filter(Location.is_active == True)
    return query.offset(skip).limit(limit).all()

def create_location(db: Session, *, obj_in: LocationCreate) -> Location:
    """
    Creates a new location in the database.

    Args:
        db: The database session.
        obj_in: The Pydantic schema containing the location creation data.

    Returns:
        The newly created Location object.
    """
    # Ensure country_code is uppercase (handled by Pydantic validator, but good practice)
    create_data = obj_in.model_dump()
    db_obj = Location(**create_data)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def update_location(db: Session, *, db_obj: Location, obj_in: Union[LocationUpdate, Dict[str, Any]]) -> Location:
    """
    Updates an existing location in the database.

    Args:
        db: The database session.
        db_obj: The existing Location object to update.
        obj_in: The Pydantic schema or dictionary containing the update data.

    Returns:
        The updated Location object.
    """
    if isinstance(obj_in, dict):
        update_data = obj_in
    else:
        update_data = obj_in.model_dump(exclude_unset=True)

    # Ensure country_code is uppercase if updated (handled by Pydantic validator)
    for field, value in update_data.items():
        if hasattr(db_obj, field):
            setattr(db_obj, field, value)

    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def remove_location(db: Session, *, location_id: int) -> Optional[Location]:
    """
    Removes a location from the database by its ID (hard delete).

    Args:
        db: The database session.
        location_id: The ID of the location to remove.

    Returns:
        The removed Location object if found and deleted, otherwise None.
    """
    db_obj = db.query(Location).get(location_id)
    if db_obj:
        db.delete(db_obj)
        db.commit()
    return db_obj 