"""
Authentication endpoints for user authentication and authorization.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from core.database.session import get_db
from core.schemas.auth import (
    Token, LoginRequest, RegisterRequest, PasswordResetRequest,
    PasswordResetConfirm, PasswordChange, VerifyEmail, RefreshToken
)
from core.services.auth import AuthService

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login user and return access and refresh tokens."""
    auth_service = AuthService(db)
    user = auth_service.authenticate_user(form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    access_token = auth_service.create_access_token(user.id)
    refresh_token = auth_service.create_refresh_token(user.id)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": 3600,  # 1 hour
        "expires_at": None  # TODO: Calculate actual expiration
    }

@router.post("/register")
async def register(
    data: RegisterRequest,
    db: Session = Depends(get_db)
):
    """Register a new user."""
    auth_service = AuthService(db)
    user = auth_service.register_user(data)
    
    # TODO: Send welcome email
    
    return {"message": "User registered successfully"}

@router.post("/password-reset")
async def request_password_reset(
    data: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """Request password reset."""
    auth_service = AuthService(db)
    success = auth_service.reset_password(data)
    
    if success:
        return {"message": "Password reset email sent"}
    return {"message": "Password reset email sent"}

@router.post("/password-reset/confirm")
async def confirm_password_reset(
    data: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """Confirm password reset."""
    auth_service = AuthService(db)
    try:
        payload = auth_service.verify_token(data.token)
        user = db.query(User).filter(User.id == payload.sub).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token"
            )
        
        user.password_hash = auth_service.get_password_hash(data.new_password)
        db.commit()
        
        return {"message": "Password reset successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token"
        )

@router.post("/password-change")
async def change_password(
    data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user password."""
    auth_service = AuthService(db)
    
    if not auth_service.verify_password(data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
    
    current_user.password_hash = auth_service.get_password_hash(data.new_password)
    db.commit()
    
    return {"message": "Password changed successfully"}

@router.post("/verify-email")
async def verify_email(
    data: VerifyEmail,
    db: Session = Depends(get_db)
):
    """Verify user email."""
    auth_service = AuthService(db)
    try:
        payload = auth_service.verify_token(data.token)
        user = db.query(User).filter(User.id == payload.sub).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token"
            )
        
        user.email_verified = True
        db.commit()
        
        return {"message": "Email verified successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token"
        )

@router.post("/refresh-token", response_model=Token)
async def refresh_token(
    data: RefreshToken,
    db: Session = Depends(get_db)
):
    """Refresh access token."""
    auth_service = AuthService(db)
    try:
        payload = auth_service.verify_token(data.refresh_token)
        if payload.type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token type"
            )
        
        user = db.query(User).filter(User.id == payload.sub).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User not found"
            )
        
        access_token = auth_service.create_access_token(user.id)
        refresh_token = auth_service.create_refresh_token(user.id)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": 3600,  # 1 hour
            "expires_at": None  # TODO: Calculate actual expiration
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        ) 