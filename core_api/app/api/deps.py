from typing import Generator, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal # Assuming session management is here
from app import crud
from app.models.user import User  # Import User model directly
from app import schemas # Need TokenPayload schema
from app.models import User as models  # Import User model from models

# --- Database Dependency --- #
def get_db() -> Generator:
    """Dependency to get a database session."""
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

# --- Security Dependencies --- #

# OAuth2 scheme definition
# tokenUrl should point to your login endpoint (where token is issued)
# In our case, it's the OTP verification endpoint
reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/verify-otp" # This might need adjustment based on frontend flow
)

# Pydantic model for token payload (data inside JWT)
class TokenPayload(BaseModel):
    sub: Optional[int] = None # Subject of the token (user ID)

async def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(reusable_oauth2)
) -> User:
    """
    Dependency to get the current user based on JWT token.
    Verifies token, extracts user ID, and fetches user from DB.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        # Extract user ID (subject) from payload
        user_id: Optional[int] = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = TokenPayload(sub=user_id)
    except JWTError:
        # Handle invalid token format or signature
        raise credentials_exception

    # Fetch user from database using the ID from the token
    user = crud.user.get(db, id=token_data.sub)

    if not user:
        # Handle case where user ID in token doesn't exist in DB
        raise credentials_exception
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency to get the current *active* user.
    Raises exception if the user fetched by get_current_user is inactive.
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_current_active_superuser(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Dependency to get the current active *superuser*.
    Raises exception if the user is not a superuser.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )
    return current_user

def check_user_permission(user: models.User, permission_name: str) -> bool:
    """
    Check if a user has a specific permission.
    
    Args:
        user: The user to check permissions for
        permission_name: The name of the permission to check
        
    Returns:
        True if the user has the permission, False otherwise
    """
    # Superusers have all permissions
    if user.is_superuser:
        return True
    
    # Check user roles for the permission
    for role in user.roles:
        for permission in role.permissions:
            if permission.permission_name == permission_name:
                return True
    
    return False 