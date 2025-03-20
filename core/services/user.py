"""
User service for handling user-related operations.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from passlib.context import CryptContext

from core.database.models import User, UserActivity
from core.schemas.user import UserCreate, UserUpdate, UserProfile

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserService:
    """Service for handling user operations."""
    
    def __init__(self, db: Session):
        """Initialize the user service."""
        self.db = db
    
    def get_password_hash(self, password: str) -> str:
        """Generate password hash."""
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_user(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        return self.db.query(User).filter(User.email == email).first()
    
    def get_users(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        status: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[User]:
        """Get list of users with filtering."""
        query = self.db.query(User)
        
        if search:
            query = query.filter(
                (User.username.ilike(f"%{search}%")) |
                (User.email.ilike(f"%{search}%"))
            )
        
        if status:
            query = query.filter(User.status == status)
        
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        
        return query.offset(skip).limit(limit).all()
    
    def get_users_count(
        self,
        search: Optional[str] = None,
        status: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> int:
        """Get total count of users with filtering."""
        query = self.db.query(User)
        
        if search:
            query = query.filter(
                (User.username.ilike(f"%{search}%")) |
                (User.email.ilike(f"%{search}%"))
            )
        
        if status:
            query = query.filter(User.status == status)
        
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        
        return query.count()
    
    def create_user(self, data: UserCreate) -> User:
        """Create a new user."""
        # Check if user exists
        if self.get_user_by_email(data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new user
        user = User(
            username=data.username,
            email=data.email,
            password_hash=self.get_password_hash(data.password),
            is_active=data.is_active,
            is_superuser=data.is_superuser,
            status=data.status
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def update_user(self, user_id: int, data: UserUpdate) -> User:
        """Update user information."""
        user = self.get_user(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check email uniqueness if being updated
        if data.email and data.email != user.email:
            if self.get_user_by_email(data.email):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
            user.email = data.email
        
        # Update other fields
        if data.username:
            user.username = data.username
        if data.password:
            user.password_hash = self.get_password_hash(data.password)
        if data.is_active is not None:
            user.is_active = data.is_active
        if data.status:
            user.status = data.status
        
        user.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def delete_user(self, user_id: int) -> bool:
        """Delete a user."""
        user = self.get_user(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        self.db.delete(user)
        self.db.commit()
        return True
    
    def get_user_profile(self, user_id: int) -> UserProfile:
        """Get user profile with additional information."""
        user = self.get_user(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # TODO: Get additional profile information from related models
        return UserProfile(
            user=user,
            points=0,
            traffic_used=0,
            traffic_limit=0,
            subscription_end=None,
            referral_code=None,
            referral_count=0
        )
    
    def log_activity(
        self,
        user_id: int,
        action: str,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> UserActivity:
        """Log user activity."""
        activity = UserActivity(
            user_id=user_id,
            action=action,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=datetime.utcnow()
        )
        
        self.db.add(activity)
        self.db.commit()
        self.db.refresh(activity)
        
        return activity
    
    def get_user_activities(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[UserActivity]:
        """Get user activity history."""
        return (
            self.db.query(UserActivity)
            .filter(UserActivity.user_id == user_id)
            .order_by(UserActivity.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        ) 