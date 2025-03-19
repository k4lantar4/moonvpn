"""
Authentication endpoints.

This module provides API endpoints for user authentication, including login,
signup, password reset, and token refresh functionality.
"""

from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from core.config import settings
from core.security import create_access_token, create_refresh_token, verify_password
from core.database import get_db
from core.database.models import User
from core.schemas.token import Token, TokenPayload, RefreshToken
from core.schemas.user import UserCreate, UserResponse
from core.services.user import authenticate_user, get_user_by_id

router = APIRouter()


@router.post("/login", response_model=Token)
def login_access_token(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Any:
    """
    Get an access token for future requests using username and password.
    
    Args:
        db: Database session dependency
        form_data: OAuth2 form containing username and password
        
    Returns:
        Token object containing access and refresh tokens
        
    Raises:
        HTTPException: If authentication fails
    """
    user = authenticate_user(db, email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        user_id=user.id, expires_delta=access_token_expires
    )
    
    # Create refresh token with longer expiration
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = create_refresh_token(
        user_id=user.id, expires_delta=refresh_token_expires
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/signup", response_model=UserResponse)
def signup(
    user_in: UserCreate,
    db: Session = Depends(get_db),
) -> UserResponse:
    """
    Create new user.
    
    Register a new user account.
    """
    # Check if email already exists
    user = db.query(User).filter(User.email == user_in.email).first()
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # Create new user (this would typically hash the password internally)
    new_user = User(
        email=user_in.email,
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        phone_number=user_in.phone_number,
        is_active=True,
        is_superuser=False,
    )
    
    # Set the password (hashing happens in the model setter)
    new_user.set_password(user_in.password)
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return UserResponse.from_orm(new_user)


@router.post("/refresh-token", response_model=Token)
def refresh_access_token(
    refresh_token_data: RefreshToken,
    db: Session = Depends(get_db),
) -> Any:
    """
    Refresh an access token using a valid refresh token.
    
    Args:
        refresh_token_data: Object containing the refresh token
        db: Database session dependency
        
    Returns:
        Token object containing new access and refresh tokens
        
    Raises:
        HTTPException: If refresh token is invalid or user not found
    """
    try:
        # Validate refresh token and extract payload
        payload = TokenPayload.from_refresh_token(refresh_token_data.refresh_token)
        
        # Get user from database
        user = get_user_by_id(db, user_id=payload.sub)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user account",
            )
            
        # Create new access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            user_id=user.id, expires_delta=access_token_expires
        )
        
        # Create new refresh token
        refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        new_refresh_token = create_refresh_token(
            user_id=user.id, expires_delta=refresh_token_expires
        )
        
        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
        }
        
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        ) 