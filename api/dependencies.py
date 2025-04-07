"""
API Dependencies

This module defines FastAPI dependencies used across the application.
"""

from typing import Annotated, Optional
from fastapi import Depends, HTTPException, status, Security
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader

from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from core.security import validate_jwt_token
from api.services.panel_service import PanelService

# OAuth2 scheme for token-based authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

# API key scheme for alternative authentication
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)]
):
    """Get the current authenticated user from a JWT token.
    
    Args:
        token: JWT token from request
        
    Returns:
        dict: User data from token
        
    Raises:
        HTTPException: If token is invalid
    """
    payload = validate_jwt_token(token)
    if "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


async def get_panel_service(db: AsyncSession = Depends(get_db)) -> PanelService:
    """Get a panel service instance.
    
    Args:
        db: Database session
        
    Returns:
        PanelService: Panel service instance
    """
    return PanelService(db=db)
