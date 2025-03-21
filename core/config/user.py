"""
User service for MoonVPN.

This module contains the user service implementation using the repository pattern.
"""

from typing import Optional, List
from datetime import datetime
from fastapi import HTTPException, status

from app.db.repositories.user import UserRepository
from app.models.user import User, UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password
from app.core.config import settings

class UserService:
    """User service class."""
    
    def __init__(self, repository: UserRepository):
        """Initialize service."""
        self.repository = repository
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Get a user by ID."""
        return await self.repository.get(user_id)
    
    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Get a user by Telegram ID."""
        return await self.repository.get_by_telegram_id(telegram_id)
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get a user by email."""
        return await self.repository.get_by_email(email)
    
    async def get_active_users(self) -> List[User]:
        """Get all active users."""
        return await self.repository.get_active_users()
    
    async def create(self, user_data: UserCreate) -> User:
        """Create a new user."""
        # Check if user already exists
        if await self.get_by_telegram_id(user_data.telegram_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this Telegram ID already exists"
            )
        
        if user_data.email and await self.get_by_email(user_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        # Hash password if provided
        if user_data.password:
            user_data.password = get_password_hash(user_data.password)
        
        # Create user
        user_dict = user_data.model_dump()
        user_dict["created_at"] = datetime.utcnow()
        user_dict["status"] = "active"
        
        return await self.repository.create(user_dict)
    
    async def update(self, user_id: int, user_data: UserUpdate) -> Optional[User]:
        """Update a user."""
        user = await self.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check email uniqueness if being updated
        if user_data.email and user_data.email != user.email:
            if await self.get_by_email(user_data.email):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already in use"
                )
        
        # Hash password if being updated
        if user_data.password:
            user_data.password = get_password_hash(user_data.password)
        
        update_data = user_data.model_dump(exclude_unset=True)
        return await self.repository.update(db_obj=user, obj_in=update_data)
    
    async def delete(self, user_id: int) -> bool:
        """Delete a user."""
        user = await self.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return await self.repository.delete(user)
    
    async def authenticate(self, telegram_id: int, password: str) -> Optional[User]:
        """Authenticate a user."""
        user = await self.get_by_telegram_id(telegram_id)
        if not user:
            return None
        
        if not verify_password(password, user.password):
            return None
        
        return user
    
    async def update_status(self, user_id: int, status: str) -> Optional[User]:
        """Update a user's status."""
        user = await self.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return await self.repository.update_status(user_id, status)
    
    async def get_user_stats(self, user_id: int) -> dict:
        """Get user statistics."""
        user = await self.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return {
            "id": user.id,
            "telegram_id": user.telegram_id,
            "email": user.email,
            "status": user.status,
            "created_at": user.created_at,
            "last_login": user.last_login,
            "is_admin": user.is_admin,
            "is_premium": user.is_premium
        } 