"""
Security Utilities

This module provides security utilities for the application,
including password hashing, token generation, and encryption.
"""

import base64
import os
import logging
from typing import Optional, Tuple, Any, Dict, Union
from datetime import datetime, timedelta
from fastapi import HTTPException, status, Request
from passlib.context import CryptContext
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from jose import JWTError, jwt

from core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Fernet key for symmetric encryption
FERNET_KEY = settings.SECRET_KEY.encode()[:32]
if len(FERNET_KEY) < 32:
    # Pad the key if it's shorter than 32 bytes
    FERNET_KEY = FERNET_KEY.ljust(32, b'0')

# Use key derivation to get a proper Fernet key
kdf = PBKDF2HMAC(
    algorithm=hashes.SHA256(),
    length=32,
    salt=settings.ENVIRONMENT.encode()[:16].ljust(16, b'0'),
    iterations=100000,
)
derived_key = base64.urlsafe_b64encode(kdf.derive(FERNET_KEY))
fernet = Fernet(derived_key)


def encrypt_text(text: str) -> str:
    """Encrypt a text string.
    
    Args:
        text: Text to encrypt
        
    Returns:
        str: Encrypted text
    """
    if not text:
        return ""
    try:
        encrypted = fernet.encrypt(text.encode())
        return encrypted.decode()
    except Exception as e:
        logger.error(f"Error encrypting text: {str(e)}")
        return text  # Fall back to plaintext if encryption fails


def decrypt_text(encrypted_text: str) -> str:
    """Decrypt an encrypted text string.
    
    Args:
        encrypted_text: Encrypted text
        
    Returns:
        str: Decrypted text
    """
    if not encrypted_text:
        return ""
    try:
        decrypted = fernet.decrypt(encrypted_text.encode())
        return decrypted.decode()
    except Exception as e:
        logger.error(f"Error decrypting text: {str(e)}")
        return encrypted_text  # Return the encrypted text if decryption fails


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
