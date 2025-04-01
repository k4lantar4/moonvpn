# core_api/app/core/security.py
from datetime import datetime, timedelta, timezone
from typing import Any, Union

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

# Password hashing context using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = settings.ALGORITHM
SECRET_KEY = settings.SECRET_KEY
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

def create_access_token(subject: Union[str, Any], expires_delta: timedelta | None = None) -> str:
    """
    Creates a JWT access token.

    Args:
        subject: The subject of the token (e.g., user ID or username).
        expires_delta: Optional timedelta for token expiry. Defaults to configured minutes.

    Returns:
        The encoded JWT access token as a string.
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {"exp": expire, "sub": str(subject)} # Ensure subject is string
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plain password against a hashed password.

    Args:
        plain_password: The password input by the user.
        hashed_password: The password stored in the database.

    Returns:
        True if the passwords match, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    Hashes a plain password using bcrypt.

    Args:
        password: The plain password to hash.

    Returns:
        The hashed password string.
    """
    return pwd_context.hash(password) 