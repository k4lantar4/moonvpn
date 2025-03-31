# Import necessary components from FastAPI and standard libraries
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Any
from sqlalchemy.orm import Session

# Import CRUD functions, schemas, models, and dependencies
from app import crud
from app import schemas
from app import models
from app.api import deps # Dependency injection for DB session and potentially authentication

# Create a new FastAPI router for user endpoints
router = APIRouter()

# --- User API Endpoints ---

@router.post("/", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
def create_user(
    *, # Enforce keyword-only arguments after this
    db: Session = Depends(deps.get_db), # Dependency to get DB session
    user_in: schemas.UserCreate # Request body containing user data
) -> Any:
    """
    Create a new user.
    Validates input using UserCreate schema.
    Handles potential duplicate Telegram IDs.
    """
    # Check if a user with the same Telegram ID already exists
    existing_user = crud.user.get_user_by_telegram_id(db, telegram_id=user_in.telegram_id)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this Telegram ID already exists.",
        )
    # Create the user using the CRUD function
    user = crud.user.create_user(db=db, obj_in=user_in)
    return user

@router.get("/", response_model=List[schemas.User])
def read_users(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    # current_user: models.User = Depends(deps.get_current_active_superuser) # Example: Add authorization
) -> Any:
    """
    Retrieve a list of users.
    Includes pagination (skip, limit).
    (Example shows how to add authorization for superusers only)
    """
    users = crud.user.get_users(db, skip=skip, limit=limit)
    return users

@router.get("/{user_id}", response_model=schemas.User)
def read_user(
    *, # Enforce keyword-only arguments
    db: Session = Depends(deps.get_db),
    user_id: int, # Path parameter for the user ID
    # current_user: models.User = Depends(deps.get_current_active_user) # Example: Authorization
) -> Any:
    """
    Retrieve a specific user by their ID.
    Handles the case where the user is not found.
    (Example shows potential authorization)
    """
    user = crud.user.get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    # Add authorization check here if needed, e.g.:
    # if user != current_user and not crud.user.is_superuser(current_user):
    #     raise HTTPException(status_code=403, detail="Not authorized")
    return user

@router.put("/{user_id}", response_model=schemas.User)
def update_user(
    *, # Enforce keyword-only arguments
    db: Session = Depends(deps.get_db),
    user_id: int, # Path parameter
    user_in: schemas.UserUpdate, # Request body with update data
    # current_user: models.User = Depends(deps.get_current_active_user) # Example: Authorization
) -> Any:
    """
    Update an existing user.
    Validates input using UserUpdate schema.
    Handles not found errors and potential authorization.
    """
    user = crud.user.get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    # Add authorization check here, e.g., only user can update themselves or superuser
    # if user.id != current_user.id and not crud.user.is_superuser(current_user):
    #     raise HTTPException(status_code=403, detail="Not authorized to update this user")

    # Perform the update using the CRUD function
    user = crud.user.update_user(db=db, db_obj=user, obj_in=user_in)
    return user

@router.delete("/{user_id}", response_model=schemas.User)
def delete_user(
    *, # Enforce keyword-only arguments
    db: Session = Depends(deps.get_db),
    user_id: int, # Path parameter
    # current_user: models.User = Depends(deps.get_current_active_superuser) # Example: Superuser auth
) -> Any:
    """
    Delete a user by ID.
    Handles not found errors.
    (Example shows potential superuser authorization)
    """
    user = crud.user.get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Perform the deletion using the CRUD function
    deleted_user = crud.user.remove_user(db=db, user_id=user_id)
    # Note: remove_user returns the deleted object or None, but we already checked existence.
    # We return the object data before deletion as confirmation.
    return deleted_user # Return the data of the user that was deleted 