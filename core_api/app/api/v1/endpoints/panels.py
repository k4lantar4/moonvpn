# Import necessary components from FastAPI and standard libraries
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Any, Optional
from sqlalchemy.orm import Session

# Import CRUD functions, schemas, models, and dependencies
from app import crud
from app import schemas
from app import models
from app.api import deps # Dependency injection for DB session and potential authentication

# Create a new FastAPI router for panel endpoints
router = APIRouter()

# --- Panel API Endpoints ---

@router.post("/", response_model=schemas.Panel, status_code=status.HTTP_201_CREATED)
def create_panel(
    *, # Enforce keyword-only arguments
    db: Session = Depends(deps.get_db),
    panel_in: schemas.PanelCreate,
    # current_user: models.User = Depends(deps.get_current_active_superuser) # Example: Auth needed
) -> Any:
    """
    Create a new V2Ray panel configuration.
    Requires appropriate permissions (e.g., superuser).
    Handles potential duplicate panel names.
    Password is required in the input but excluded from the response.
    """
    # Check if a panel with the same name already exists
    existing_panel = crud.panel.get_panel_by_name(db, name=panel_in.name)
    if existing_panel:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A panel with the name '{panel_in.name}' already exists.",
        )
    # Create the panel using the CRUD function
    # Remember that password storage should be secured in production
    panel = crud.panel.create_panel(db=db, obj_in=panel_in)
    # The response_model=schemas.Panel ensures the password is not returned
    return panel

@router.get("/", response_model=List[schemas.Panel])
def read_panels(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    only_active: Optional[bool] = Query(None, description="Filter to return only active panels"),
    # current_user: models.User = Depends(deps.get_current_active_user) # Example: Auth needed
) -> Any:
    """
    Retrieve a list of V2Ray panel configurations.
    Includes pagination and optional filtering by active status.
    Password is not included in the response.
    """
    panels = crud.panel.get_panels(db, skip=skip, limit=limit, only_active=only_active or False)
    return panels

@router.get("/{panel_id}", response_model=schemas.Panel)
def read_panel(
    *, # Enforce keyword-only arguments
    db: Session = Depends(deps.get_db),
    panel_id: int, # Path parameter
    # current_user: models.User = Depends(deps.get_current_active_user) # Example: Auth needed
) -> Any:
    """
    Retrieve a specific panel configuration by its ID.
    Handles not found errors. Password is not included.
    """
    panel = crud.panel.get_panel(db, panel_id=panel_id)
    if not panel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Panel not found")
    return panel

@router.put("/{panel_id}", response_model=schemas.Panel)
def update_panel(
    *, # Enforce keyword-only arguments
    db: Session = Depends(deps.get_db),
    panel_id: int, # Path parameter
    panel_in: schemas.PanelUpdate, # Request body with update data
    # current_user: models.User = Depends(deps.get_current_active_superuser) # Example: Auth needed
) -> Any:
    """
    Update an existing panel configuration.
    Requires appropriate permissions.
    Handles not found errors and potential duplicate names.
    Password can be updated (sent in request) but is not returned.
    """
    panel = crud.panel.get_panel(db, panel_id=panel_id)
    if not panel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Panel not found")

    # Check for duplicate name if the name is being changed
    if panel_in.name is not None and panel_in.name != panel.name:
        existing_panel = crud.panel.get_panel_by_name(db, name=panel_in.name)
        if existing_panel and existing_panel.id != panel_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A panel with the name '{panel_in.name}' already exists.",
            )

    # Perform the update (remember to handle password security if updated)
    updated_panel = crud.panel.update_panel(db=db, db_obj=panel, obj_in=panel_in)
    # Response model ensures password isn't returned
    return updated_panel

@router.delete("/{panel_id}", response_model=schemas.Panel)
def delete_panel(
    *, # Enforce keyword-only arguments
    db: Session = Depends(deps.get_db),
    panel_id: int, # Path parameter
    # current_user: models.User = Depends(deps.get_current_active_superuser) # Example: Auth needed
) -> Any:
    """
    Delete a panel configuration by ID.
    Requires appropriate permissions.
    Handles not found errors.
    Returns the deleted panel data (excluding password) as confirmation.
    """
    panel = crud.panel.get_panel(db, panel_id=panel_id)
    if not panel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Panel not found")

    # Perform deletion
    deleted_panel = crud.panel.remove_panel(db=db, panel_id=panel_id)
    # Response model ensures password isn't returned
    return deleted_panel 