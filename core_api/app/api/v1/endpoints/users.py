# Import necessary components from FastAPI and standard libraries
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Any
from sqlalchemy.orm import Session

# Import CRUD instance, schemas, models, and dependencies
from app import crud # crud.user will be available now
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
    # Use the specific method from CRUDUser
    existing_user = crud.user.get_by_telegram_id(db, telegram_id=user_in.telegram_id)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this Telegram ID already exists.",
        )
    # Use the create method from CRUDBase (inherited by CRUDUser)
    user = crud.user.create(db=db, obj_in=user_in)
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
    # Use the get_multi method from CRUDBase
    users = crud.user.get_multi(db, skip=skip, limit=limit)
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
    # Use the get method from CRUDBase
    user = crud.user.get(db, id=user_id)
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
    # First, get the existing user object
    user = crud.user.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    # Then, update it using the update method from CRUDBase
    user = crud.user.update(db=db, db_obj=user, obj_in=user_in)
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
    # Use the remove method from CRUDBase
    deleted_user = crud.user.remove(db=db, id=user_id)
    if not deleted_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    # CRUDBase.remove returns the deleted object
    return deleted_user # Return the data of the user that was deleted

# --- Endpoint for Current User --- #
@router.get("/me", response_model=schemas.User)
async def read_users_me(
    current_user: models.User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Get current logged-in active user's profile.
    """
    # The dependency provides the 'current_user' object
    return current_user 