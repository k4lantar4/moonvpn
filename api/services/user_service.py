"""
User Service

This module provides user-related service functions.
"""

import logging
from typing import Optional, List, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.users import User
from api.repositories.users import UserRepository
from core.security.password import verify_password, get_password_hash

logger = logging.getLogger(__name__)


class UserService:
    """User service class for handling user-related operations."""
    
    def __init__(self, db: AsyncSession):
        """Initialize UserService with a database session.
        
        Args:
            db: Database session
        """
        self.db = db
        self.repository = UserRepository(db)
    
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get a user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User object if found, None otherwise
        """
        return await self.repository.get(user_id)
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get a user by username.
        
        Args:
            username: Username
            
        Returns:
            User object if found, None otherwise
        """
        return await self.repository.get_by_username(username)
    
    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Get a user by Telegram ID.
        
        Args:
            telegram_id: Telegram user ID
            
        Returns:
            User object if found, None otherwise
        """
        return await self.repository.get_by_telegram_id(telegram_id)
    
    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate a user with username and password.
        
        Args:
            username: Username
            password: Plain text password
            
        Returns:
            User object if authenticated, None otherwise
        """
        user = await self.get_user_by_username(username)
        if not user:
            return None
        if not verify_password(password, user.password):
            return None
        return user
    
    async def create_user(self, user_data: Dict[str, Any]) -> User:
        """Create a new user.
        
        Args:
            user_data: User data dictionary
            
        Returns:
            Created user object
        """
        if "password" in user_data:
            user_data["password"] = get_password_hash(user_data["password"])
        return await self.repository.create(user_data)
    
    async def update_user(self, user_id: int, user_data: Dict[str, Any]) -> Optional[User]:
        """Update a user.
        
        Args:
            user_id: User ID
            user_data: User data dictionary
            
        Returns:
            Updated user object if found, None otherwise
        """
        if "password" in user_data:
            user_data["password"] = get_password_hash(user_data["password"])
        return await self.repository.update(user_id, user_data)
    
    async def delete_user(self, user_id: int) -> bool:
        """Delete a user.
        
        Args:
            user_id: User ID
            
        Returns:
            True if deleted, False otherwise
        """
        return await self.repository.delete(user_id)
    
    async def list_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """List users with pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of user objects
        """
        return await self.repository.list(skip, limit)
    
    async def count_users(self) -> int:
        """Count total number of users.
        
        Returns:
            Total number of users
        """
        return await self.repository.count()
    
    async def ban_user(self, user_id: int) -> Optional[User]:
        """Ban a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Updated user object if found, None otherwise
        """
        return await self.repository.update(user_id, {"is_banned": True})
    
    async def unban_user(self, user_id: int) -> Optional[User]:
        """Unban a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Updated user object if found, None otherwise
        """
        return await self.repository.update(user_id, {"is_banned": False})
    
    async def change_role(self, user_id: int, role_id: int) -> Optional[User]:
        """Change a user's role.
        
        Args:
            user_id: User ID
            role_id: Role ID
            
        Returns:
            Updated user object if found, None otherwise
        """
        return await self.repository.update(user_id, {"role_id": role_id}) 