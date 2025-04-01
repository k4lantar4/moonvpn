# Import necessary components for CRUD operations
from sqlalchemy.orm import Session
from typing import Any, Dict, Optional, Union, List

# Import models and schemas
from app.models.panel import Panel
from app.schemas.panel import PanelCreate, PanelUpdate
from app.crud.base import CRUDBase
# Import password hashing utilities if needed
# from app.core.security import get_password_hash, verify_password

class CRUDPanel(CRUDBase[Panel, PanelCreate, PanelUpdate]):
    def get_by_name(self, db: Session, *, name: str) -> Optional[Panel]:
        """ Retrieves a single panel by its unique name. """
        return db.query(self.model).filter(self.model.name == name).first()

    # Override get_multi if filtering by active status is common
    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        only_active: bool = False
    ) -> List[Panel]:
        query = db.query(self.model)
        if only_active:
            query = query.filter(self.model.is_active == True)
        return query.offset(skip).limit(limit).all()

    # Override create and update if password handling is needed
    # def create(self, db: Session, *, obj_in: PanelCreate) -> Panel:
    #     # Add password hashing before calling super().create
    #     ...
    #     return super().create(db, obj_in=db_obj)
    #
    # def update(self, db: Session, *, db_obj: Panel, obj_in: Union[PanelUpdate, Dict[str, Any]]) -> Panel:
    #     # Add password hashing if password is updated
    #     ...
    #     return super().update(db, db_obj=db_obj, obj_in=update_data)

    # Add any other panel-specific methods here

# Create a singleton instance
panel = CRUDPanel(Panel)

# --- Deprecated Individual Functions ---

def get_panel(db: Session, panel_id: int) -> Optional[Panel]:
    """
    Retrieves a single panel by its primary key ID.

    Args:
        db: The database session.
        panel_id: The ID of the panel to retrieve.

    Returns:
        The Panel object if found, otherwise None.
    """
    return db.query(Panel).filter(Panel.id == panel_id).first()

def get_panels(db: Session, skip: int = 0, limit: int = 100, only_active: bool = False) -> List[Panel]:
    """
    Retrieves a list of panels with pagination and optional filtering for active panels.

    Args:
        db: The database session.
        skip: The number of records to skip.
        limit: The maximum number of records to return.
        only_active: If True, only returns panels where is_active is True.

    Returns:
        A list of Panel objects.
    """
    query = db.query(Panel)
    if only_active:
        query = query.filter(Panel.is_active == True)
    return query.offset(skip).limit(limit).all()

def create_panel(db: Session, *, obj_in: PanelCreate) -> Panel:
    """
    Creates a new panel in the database.
    Remember to handle password securely in a real application.

    Args:
        db: The database session.
        obj_in: The Pydantic schema containing the panel creation data.

    Returns:
        The newly created Panel object.
    """
    # TODO: Add password hashing/encryption before saving
    create_data = obj_in.model_dump()
    db_obj = Panel(**create_data)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def update_panel(db: Session, *, db_obj: Panel, obj_in: Union[PanelUpdate, Dict[str, Any]]) -> Panel:
    """
    Updates an existing panel in the database.
    Remember to handle password securely if it's updated.

    Args:
        db: The database session.
        db_obj: The existing Panel object to update.
        obj_in: The Pydantic schema or dictionary containing the update data.

    Returns:
        The updated Panel object.
    """
    if isinstance(obj_in, dict):
        update_data = obj_in
    else:
        update_data = obj_in.model_dump(exclude_unset=True)

    # TODO: If 'password' is in update_data, hash/encrypt it before setting
    # if "password" in update_data and update_data["password"]:
    #     hashed_password = hash_password(update_data["password"])
    #     setattr(db_obj, "password", hashed_password)
    #     del update_data["password"] # Don't update with plain text
    # else:
    #     # Ensure password is not accidentally nulled if not provided
    #     update_data.pop("password", None)

    for field, value in update_data.items():
        # Only set attribute if the field is actually part of the model
        if hasattr(db_obj, field):
             setattr(db_obj, field, value)

    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def remove_panel(db: Session, *, panel_id: int) -> Optional[Panel]:
    """
    Removes a panel from the database by its ID (hard delete).

    Args:
        db: The database session.
        panel_id: The ID of the panel to remove.

    Returns:
        The removed Panel object if found and deleted, otherwise None.
    """
    db_obj = db.query(Panel).get(panel_id)
    if db_obj:
        db.delete(db_obj)
        db.commit()
    return db_obj 