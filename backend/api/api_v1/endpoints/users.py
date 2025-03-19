"""
User endpoints for user management.
"""

from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.security import get_current_active_user, get_current_admin_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.services.user import create_user, delete_user, get_user_by_id, get_users, update_user

router = APIRouter()


@router.get("/", response_model=List[UserResponse])
async def read_users(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_admin_user),
) -> Any:
    """
    Retrieve users.
    
    Args:
        db: Database session
        skip: Number of users to skip
        limit: Maximum number of users to return
        current_user: Current admin user (from token)
        
    Returns:
        List of users
    """
    users = get_users(db, skip=skip, limit=limit)
    return users


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user_endpoint(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate,
    current_user: User = Depends(get_current_admin_user),
) -> Any:
    """
    Create new user.
    
    Args:
        db: Database session
        user_in: User creation data
        current_user: Current admin user (from token)
        
    Returns:
        Created user
        
    Raises:
        HTTPException: If user already exists
    """
    try:
        user = create_user(db, user_in)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/me", response_model=UserResponse)
async def read_user_me(
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get current user.
    
    Args:
        current_user: Current active user (from token)
        
    Returns:
        Current user
    """
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_user_me(
    *,
    db: Session = Depends(get_db),
    user_in: UserUpdate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Update own user.
    
    Args:
        db: Database session
        user_in: User update data
        current_user: Current active user (from token)
        
    Returns:
        Updated user
    """
    # Prevent users from granting themselves admin privileges
    if user_in.is_admin is not None:
        user_in.is_admin = current_user.is_admin
    
    updated_user = update_user(db, user_id=current_user.id, user_data=user_in)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return updated_user


@router.get("/{user_id}", response_model=UserResponse)
async def read_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get user by ID.
    
    Args:
        user_id: User ID
        db: Database session
        current_user: Current active user (from token)
        
    Returns:
        User
        
    Raises:
        HTTPException: If user not found or unauthorized
    """
    # Regular users can only view their own profile
    if not current_user.is_admin and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    user = get_user_by_id(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user_endpoint(
    *,
    db: Session = Depends(get_db),
    user_id: int,
    user_in: UserUpdate,
    current_user: User = Depends(get_current_admin_user),
) -> Any:
    """
    Update a user.
    
    Args:
        db: Database session
        user_id: User ID
        user_in: User update data
        current_user: Current admin user (from token)
        
    Returns:
        Updated user
        
    Raises:
        HTTPException: If user not found
    """
    user = update_user(db, user_id=user_id, user_data=user_in)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


@router.delete("/{user_id}", response_model=bool)
async def delete_user_endpoint(
    *,
    db: Session = Depends(get_db),
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
) -> Any:
    """
    Delete a user.
    
    Args:
        db: Database session
        user_id: User ID
        current_user: Current admin user (from token)
        
    Returns:
        True if user was deleted
        
    Raises:
        HTTPException: If user not found or can't delete self
    """
    # Prevent admins from deleting themselves
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself",
        )
    
    result = delete_user(db, user_id=user_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return result 