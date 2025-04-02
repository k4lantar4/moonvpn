# Import necessary components from FastAPI and standard libraries
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Any, Dict
from sqlalchemy.orm import Session
from decimal import Decimal

# Import CRUD instance, schemas, models, and dependencies
from app import crud # crud.user will be available now
from app import schemas
from app import models
from app.api import deps # Dependency injection for DB session and potentially authentication
from app.core.config import settings

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

# --- Seller Related Endpoints --- #
@router.get("/me/seller-requirements", response_model=Dict[str, Any])
async def check_seller_requirements(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Check if the current user meets the requirements to become a seller.
    """
    # Refresh user to get the latest data
    db.refresh(current_user, attribute_names=['role', 'wallet_balance'])
    
    # Check if user is already a seller
    seller_role = crud.role.get_role_by_name(db, name=settings.SELLER_ROLE_NAME)
    if not seller_role:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Seller role '{settings.SELLER_ROLE_NAME}' not found in the system"
        )
    
    is_seller = current_user.role_id == seller_role.id
    
    # Get the threshold from settings
    threshold = settings.SELLER_UPGRADE_THRESHOLD or Decimal('1000000.00')
    
    # Check if user has enough wallet balance
    has_enough_balance = current_user.wallet_balance >= threshold
    
    # Calculate how much more is needed
    if has_enough_balance:
        balance_needed = Decimal('0.00')
    else:
        balance_needed = threshold - current_user.wallet_balance
    
    return {
        "is_seller": is_seller,
        "wallet_balance": current_user.wallet_balance,
        "threshold": threshold,
        "has_enough_balance": has_enough_balance,
        "balance_needed": balance_needed,
        "can_become_seller": has_enough_balance and not is_seller,
    }

@router.post("/me/become-seller", response_model=schemas.User)
async def become_seller(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Upgrade current user to seller role if they meet the requirements.
    """
    # Refresh user to get the latest data
    db.refresh(current_user, attribute_names=['role', 'wallet_balance'])
    
    # Check if user is already a seller
    seller_role = crud.role.get_role_by_name(db, name=settings.SELLER_ROLE_NAME)
    if not seller_role:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Seller role '{settings.SELLER_ROLE_NAME}' not found in the system"
        )
    
    if current_user.role_id == seller_role.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a seller"
        )
    
    # Get the threshold from settings
    threshold = settings.SELLER_UPGRADE_THRESHOLD or Decimal('1000000.00')
    
    # Check if user has enough wallet balance
    if current_user.wallet_balance < threshold:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient wallet balance. You need {threshold} but have {current_user.wallet_balance}"
        )
    
    # Upgrade user to seller role
    user_update = schemas.UserUpdate(role_id=seller_role.id)
    updated_user = crud.user.update(db=db, db_obj=current_user, obj_in=user_update)
    
    return updated_user 