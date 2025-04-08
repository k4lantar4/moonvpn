"""
Token Utilities

This module provides token utilities for the application.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from jose import JWTError, jwt

from core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def create_jwt_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create a JWT token.
    
    Args:
        data: Token payload
        expires_delta: Token expiration time
        
    Returns:
        str: JWT token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def validate_jwt_token(token: str) -> Dict[str, Any]:
    """Validate a JWT token.
    
    Args:
        token: JWT token
        
    Returns:
        Dict[str, Any]: Token payload
        
    Raises:
        HTTPException: If the token is invalid
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) 