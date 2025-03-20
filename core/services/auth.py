"""
Authentication service for handling user authentication and authorization.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status

from core.config import settings
from core.database.models import User
from core.schemas.auth import TokenPayload, LoginRequest, RegisterRequest, PasswordResetRequest

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    """Service for handling authentication and authorization."""
    
    def __init__(self, db: Session):
        """Initialize the auth service."""
        self.db = db
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Generate password hash."""
        return pwd_context.hash(password)
    
    def create_access_token(self, user_id: int, expires_delta: Optional[timedelta] = None) -> str:
        """Create a new access token."""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            
        to_encode = {
            "sub": str(user_id),
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        }
        
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    def create_refresh_token(self, user_id: int, expires_delta: Optional[timedelta] = None) -> str:
        """Create a new refresh token."""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
            
        to_encode = {
            "sub": str(user_id),
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        }
        
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate a user by email and password."""
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            return None
        if not self.verify_password(password, user.password_hash):
            return None
        return user
    
    def register_user(self, data: RegisterRequest) -> User:
        """Register a new user."""
        # Check if user exists
        if self.db.query(User).filter(User.email == data.email).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
            
        # Create new user
        user = User(
            username=data.username,
            email=data.email,
            password_hash=self.get_password_hash(data.password),
            status="active",
            is_active=True
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def reset_password(self, data: PasswordResetRequest) -> bool:
        """Request password reset."""
        user = self.db.query(User).filter(User.email == data.email).first()
        if not user:
            # Don't reveal if email exists
            return True
            
        # Generate reset token
        reset_token = self.create_access_token(
            user.id,
            expires_delta=timedelta(hours=24)
        )
        
        # TODO: Send reset email with token
        # For now, just return success
        return True
    
    def verify_token(self, token: str) -> TokenPayload:
        """Verify a JWT token."""
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            return TokenPayload(**payload)
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    def get_current_user(self, token: str) -> User:
        """Get current user from token."""
        payload = self.verify_token(token)
        user = self.db.query(User).filter(User.id == payload.sub).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user 