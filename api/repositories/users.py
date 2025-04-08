"""
User Repository

This module provides database operations for user entities.
"""

import logging
from typing import Optional, List, Dict, Any, Union
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.users import User
from api.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class UserRepository(BaseRepository):
    """Repository for User model operations."""
    
    def __init__(self, db: AsyncSession):
        """Initialize UserRepository with a database session.
        
        Args:
            db: Database session
        """
        super().__init__(db, User)
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get a user by username.
        
        Args:
            username: Username
            
        Returns:
            User object if found, None otherwise
        """
        query = select(User).where(User.username == username)
        result = await self.db.execute(query)
        return result.scalars().first()
    
    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Get a user by Telegram ID.
        
        Args:
            telegram_id: Telegram user ID
            
        Returns:
            User object if found, None otherwise
        """
        query = select(User).where(User.telegram_id == telegram_id)
        result = await self.db.execute(query)
        return result.scalars().first()
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get a user by email.
        
        Args:
            email: Email address
            
        Returns:
            User object if found, None otherwise
        """
        query = select(User).where(User.email == email)
        result = await self.db.execute(query)
        return result.scalars().first()
    
    async def list_admins(self, skip: int = 0, limit: int = 100) -> List[User]:
        """List admin users with pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of admin user objects
        """
        query = select(User).where(User.is_admin == True).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def list_active_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """List active (not banned) users with pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of active user objects
        """
        query = select(User).where(User.is_banned == False).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def list_banned_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """List banned users with pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of banned user objects
        """
        query = select(User).where(User.is_banned == True).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def count_admins(self) -> int:
        """Count total number of admin users.
        
        Returns:
            Total number of admin users
        """
        query = select(func.count()).where(User.is_admin == True)
        result = await self.db.execute(query)
        return result.scalar_one() 