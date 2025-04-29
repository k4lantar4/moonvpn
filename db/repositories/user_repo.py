"""
User repository for database operations
"""

from typing import List, Optional, Union
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from db.models.user import User
from db.models.enums import UserRole
from .base_repository import BaseRepository


class UserRepository:
    """Repository for user-related database operations"""
    
    def __init__(self, session: Union[AsyncSession, Session]):
        """مقداردهی اولیه با سشن دیتابیس"""
        self.session = session
        self.model = User
        self._is_async = isinstance(session, AsyncSession)
        
    def get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Get user by Telegram ID"""
        if self._is_async:
            return self._get_user_by_telegram_id_async(telegram_id)
        else:
            return self.session.query(User).filter(User.telegram_id == telegram_id).first()
    
    async def _get_user_by_telegram_id_async(self, telegram_id: int) -> Optional[User]:
        """Async version of get_user_by_telegram_id"""
        query = select(User).where(User.telegram_id == telegram_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        if self._is_async:
            return self._get_by_id_async(user_id)
        else:
            return self.session.query(User).filter(User.id == user_id).first()
    
    async def _get_by_id_async(self, user_id: int) -> Optional[User]:
        """Async version of get_by_id"""
        query = select(User).where(User.id == user_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    def create_user(self, telegram_id: int, username: Optional[str] = None) -> User:
        """Create a new user"""
        if self._is_async:
            return self._create_user_async(telegram_id, username)
        else:
            try:
                user = User(
                    telegram_id=telegram_id,
                    username=username,
                    role=UserRole.USER
                )
                self.session.add(user)
                self.session.flush()
                return user
            except IntegrityError:
                self.session.rollback()
                # If user already exists, get and return it
                existing_user = self.get_user_by_telegram_id(telegram_id)
                if existing_user:
                    return existing_user
                else:
                    # This case should ideally not happen if IntegrityError was due to telegram_id
                    raise  # Re-raise the original exception
    
    async def _create_user_async(self, telegram_id: int, username: Optional[str] = None) -> User:
        """Async version of create_user"""
        try:
            user = User(
                telegram_id=telegram_id,
                username=username,
                role=UserRole.USER
            )
            self.session.add(user)
            await self.session.flush()
            return user
        except IntegrityError:
            await self.session.rollback()
            # If user already exists, get and return it
            existing_user = await self.get_user_by_telegram_id(telegram_id)
            if existing_user:
                return existing_user
            else:
                # This case should ideally not happen if IntegrityError was due to telegram_id
                raise  # Re-raise the original exception

    def get_or_create_user(self, telegram_id: int, username: Optional[str] = None) -> User:
        """دریافت کاربر در صورت وجود یا ایجاد کاربر جدید"""
        if self._is_async:
            return self._get_or_create_user_async(telegram_id, username)
        else:
            user = self.get_user_by_telegram_id(telegram_id)
            if user:
                # اگر یوزرنیم تغییر کرده بود، آپدیت شود
                if username and user.username != username:
                    user.username = username
                    self.session.flush()
                return user
            # Create user without internal commit
            new_user = User(
                telegram_id=telegram_id,
                username=username,
                role=UserRole.USER
            )
            self.session.add(new_user)
            self.session.flush()
            return new_user
    
    async def _get_or_create_user_async(self, telegram_id: int, username: Optional[str] = None) -> User:
        """Async version of get_or_create_user"""
        user = await self.get_user_by_telegram_id(telegram_id)
        if user:
            # اگر یوزرنیم تغییر کرده بود، آپدیت شود
            if username and user.username != username:
                user.username = username
                await self.session.flush()
            return user
        # Create user without internal commit
        new_user = User(
            telegram_id=telegram_id,
            username=username,
            role=UserRole.USER
        )
        self.session.add(new_user)
        await self.session.flush()
        return new_user
    
    def get_all_users(self) -> List[User]:
        """Get all users"""
        if self._is_async:
            return self._get_all_users_async()
        else:
            return self.session.query(User).all()
    
    async def _get_all_users_async(self) -> List[User]:
        """Async version of get_all_users"""
        query = select(User)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    def update_balance(self, user_id: int, new_balance: Decimal) -> bool:
        """بروزرسانی موجودی کیف پول کاربر"""
        if self._is_async:
            return self._update_balance_async(user_id, new_balance)
        else:
            user = self.get_by_id(user_id)
            if not user:
                return False
            
            user.balance = new_balance
            self.session.flush()
            return True
    
    async def _update_balance_async(self, user_id: int, new_balance: Decimal) -> bool:
        """Async version of update_balance"""
        user = await self.get_by_id(user_id)
        if not user:
            return False
        
        user.balance = new_balance
        await self.session.flush()
        return True

    async def get_all_admins(self) -> List[User]:
        """دریافت همه ادمین‌ها"""
        query = select(User).where(User.role == UserRole.ADMIN)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def update_user_status(self, telegram_id: int, status: bool) -> Optional[User]:
        """بروزرسانی وضعیت کاربر (فعال/غیرفعال)"""
        user = await self.get_user_by_telegram_id(telegram_id)
        if user:
            user.status = status
            return user
        return user
    
    async def update_user(self, user_id: int, user_data: dict) -> Optional[User]:
        """Update user data"""
        user = await self.get_by_id(user_id)
        if user:
            for key, value in user_data.items():
                setattr(user, key, value)
            return user
        return user
    
    async def delete_user(self, user_id: int) -> bool:
        """Delete a user"""
        user = await self.get_by_id(user_id)
        if user:
            await self.session.delete(user)
            return True
        return False
    
    async def get_users_by_role(self, role: str) -> List[User]:
        """Get users by role"""
        query = select(User).where(User.role == role)
        result = await self.session.execute(query)
        return list(result.scalars().all())
