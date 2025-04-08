"""
Authentication Utilities

This module provides authentication utilities for the application.
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.security.token import validate_jwt_token
from api.services.user_service import UserService
from api.models.users import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get the current authenticated user.
    
    Args:
        token: JWT token
        db: Database session
    
    Returns:
        User: Current user
    
    Raises:
        HTTPException: If authentication fails
    """
    payload = validate_jwt_token(token)
    username: str = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    user_service = UserService(db)
    user = await user_service.get_user_by_username(username)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    return user

async def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get the current authenticated admin user.
    
    Args:
        current_user: Current authenticated user
    
    Returns:
        User: Current admin user
    
    Raises:
        HTTPException: If the user is not an admin
    """
    if not current_user.role.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return current_user 