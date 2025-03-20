"""
Security endpoints for handling authentication and authorization.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from ...core.database.session import get_db
from ...core.middleware.security_middleware import SecurityMiddleware
from ...schemas.security import (
    UserCreate,
    UserUpdate,
    Token,
    User,
    SecurityEvent
)
from ...services.security import SecurityService

router = APIRouter()
security = HTTPBearer()

@router.post("/auth/register", response_model=User)
async def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """Register a new user."""
    security_service = SecurityService(db)
    return await security_service.create_user(user_data)

@router.post("/auth/login", response_model=Token)
async def login(
    username: str,
    password: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Login user and return access token."""
    security_service = SecurityService(db)
    
    # Authenticate user
    user = await security_service.authenticate_user(username, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    # Check 2FA if enabled
    if user.two_factor_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA verification required"
        )

    # Create session and return tokens
    return await security_service.create_user_session(
        user=user,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )

@router.post("/auth/2fa/verify")
async def verify_2fa(
    user_id: int,
    token: str,
    db: Session = Depends(get_db)
):
    """Verify 2FA token."""
    security_service = SecurityService(db)
    is_valid = await security_service.verify_2fa(user_id, token)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid 2FA token"
        )
    return {"message": "2FA verification successful"}

@router.post("/auth/2fa/enable")
async def enable_2fa(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Enable 2FA for a user."""
    security_service = SecurityService(db)
    return await security_service.enable_2fa(user_id)

@router.post("/auth/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token."""
    security_service = SecurityService(db)
    return await security_service.refresh_token(refresh_token)

@router.post("/auth/logout")
async def logout(
    user_id: int,
    session_id: int,
    db: Session = Depends(get_db)
):
    """Logout user and revoke session."""
    security_service = SecurityService(db)
    success = await security_service.revoke_session(user_id, session_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    return {"message": "Successfully logged out"}

@router.get("/users/me", response_model=User)
async def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
):
    """Get current user information."""
    return request.state.user

@router.put("/users/me", response_model=User)
async def update_current_user(
    user_data: UserUpdate,
    request: Request,
    db: Session = Depends(get_db)
):
    """Update current user information."""
    security_service = SecurityService(db)
    return await security_service.update_user(request.state.user.id, user_data)

@router.get("/security/events", response_model=list[SecurityEvent])
async def get_security_events(
    request: Request,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """Get security events (admin only)."""
    if request.state.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    security_service = SecurityService(db)
    events = security_service.db.query(SecurityEvent).offset(skip).limit(limit).all()
    return events 