"""
Password Utilities

This module provides password utilities for the application.
"""

import logging
from passlib.context import CryptContext

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash.
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password
        
    Returns:
        bool: True if the password matches the hash
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate a hash for a password.
    
    Args:
        password: Plain text password
        
    Returns:
        str: Password hash
    """
    return pwd_context.hash(password) 