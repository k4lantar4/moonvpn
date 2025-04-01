# Import necessary components from FastAPI and standard libraries
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Any, Optional
from sqlalchemy.orm import Session

# Import CRUD functions, schemas, models, and dependencies
from app import crud
from app import schemas
from app import models
from app.api import deps # Dependency injection for DB session

# Create a new FastAPI router for location endpoints
router = APIRouter()

# --- Location API Endpoints ---

@router.post("/", response_model=schemas.Location, status_code=status.HTTP_201_CREATED)
def create_location(
    *, # Enforce keyword-only arguments
    db: Session = Depends(deps.get_db),
    location_in: schemas.LocationCreate,
    # current_user: models.User = Depends(deps.get_current_active_superuser) # Example: Auth needed
) -> Any:
    """
    Create a new geographical location.
    Requires appropriate permissions.
    Handles potential duplicate location names.
    Validates country code format.
    """
    # Check if a location with the same name already exists
    existing_location = crud.location.get_location_by_name(db, name=location_in.name)
    if existing_location:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A location with the name '{location_in.name}' already exists.",
        )
    # Pydantic schema already validates country_code format and case
    location = crud.location.create_location(db=db, obj_in=location_in)
    return location

@router.get("/", response_model=List[schemas.Location])
def read_locations(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    only_active: Optional[bool] = Query(None, description="Filter to return only active locations"),
    # current_user: models.User = Depends(deps.get_current_active_user) # Example: Auth needed
) -> Any:
    """
    Retrieve a list of geographical locations.
    Includes pagination and optional filtering by active status.
    """
    locations = crud.location.get_locations(db, skip=skip, limit=limit, only_active=only_active or False)
    return locations

@router.get("/{location_id}", response_model=schemas.Location)
def read_location(
    *, # Enforce keyword-only arguments
    db: Session = Depends(deps.get_db),
    location_id: int, # Path parameter
    # current_user: models.User = Depends(deps.get_current_active_user) # Example: Auth needed
) -> Any:
    """
    Retrieve a specific location by its ID.
    Handles not found errors.
    """
    location = crud.location.get_location(db, location_id=location_id)
    if not location:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")
    return location

@router.put("/{location_id}", response_model=schemas.Location)
def update_location(
    *, # Enforce keyword-only arguments
    db: Session = Depends(deps.get_db),
    location_id: int, # Path parameter
    location_in: schemas.LocationUpdate, # Request body with update data
    # current_user: models.User = Depends(deps.get_current_active_superuser) # Example: Auth needed
) -> Any:
    """
    Update an existing location.
    Requires appropriate permissions.
    Handles not found errors and potential duplicate names.
    Validates country code if updated.
    """
    location = crud.location.get_location(db, location_id=location_id)
    if not location:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")

    # Check for duplicate name if the name is being changed
    if location_in.name is not None and location_in.name != location.name:
        existing_location = crud.location.get_location_by_name(db, name=location_in.name)
        if existing_location and existing_location.id != location_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A location with the name '{location_in.name}' already exists.",
            )

    # Pydantic schema handles country_code validation if provided
    updated_location = crud.location.update_location(db=db, db_obj=location, obj_in=location_in)
    return updated_location

@router.delete("/{location_id}", response_model=schemas.Location)
def delete_location(
    *, # Enforce keyword-only arguments
    db: Session = Depends(deps.get_db),
    location_id: int, # Path parameter
    # current_user: models.User = Depends(deps.get_current_active_superuser) # Example: Auth needed
) -> Any:
    """
    Delete a location by ID.
    Requires appropriate permissions.
    Handles not found errors.
    Returns the deleted location data as confirmation.
    """
    location = crud.location.get_location(db, location_id=location_id)
    if not location:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")

    # Perform deletion
    deleted_location = crud.location.remove_location(db=db, location_id=location_id)
    return deleted_location 