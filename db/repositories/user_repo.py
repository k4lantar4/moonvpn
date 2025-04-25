"""
User repository for database operations
"""

from typing import List, Optional
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from db.models.user import User, UserRole
from .base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for user-related database operations"""
    
    def __init__(self, session: AsyncSession):
        """مقداردهی اولیه با سشن دیتابیس"""
        super().__init__(session, User)
        
    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Get user by Telegram ID"""
        query = select(User).where(User.telegram_id == telegram_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return await super().get_by_id(user_id)
    
    async def create_user(self, telegram_id: int, username: Optional[str] = None) -> User:
        """Create a new user"""
        try:
            user = await self.create(
                telegram_id=telegram_id,
                username=username,
                role=UserRole.USER
            )
            return user
        except IntegrityError:
            await self.session.rollback()
            # اگر کاربر از قبل وجود داشت، آن را برگردان
            existing_user = await self.get_user_by_telegram_id(telegram_id)
            if existing_user:
                return existing_user
            else:
                # This case should ideally not happen if IntegrityError was due to telegram_id
                raise # Re-raise the original exception

    async def get_or_create_user(self, telegram_id: int, username: Optional[str] = None) -> User:
        """دریافت کاربر در صورت وجود یا ایجاد کاربر جدید"""
        user = await self.get_user_by_telegram_id(telegram_id)
        if user:
            # اگر یوزرنیم تغییر کرده بود، آپدیت شود
            if username and user.username != username:
                user.username = username
                await self.session.flush() # Flush change within transaction
            return user
        # Create user without internal commit
        new_user = User(
            telegram_id=telegram_id,
            username=username,
            role=UserRole.USER
        )
        self.session.add(new_user)
        await self.session.flush() # Make sure it's added before returning
        return new_user
    
    async def get_all_users(self) -> List[User]:
        """Get all users"""
        query = select(User)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
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
        user = await self.get_user_by_id(user_id)
        if user:
            for key, value in user_data.items():
                setattr(user, key, value)
            return user
        return user
    
    async def update_balance(self, user_id: int, new_balance: Decimal) -> bool:
        """بروزرسانی موجودی کیف پول کاربر"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return False
        
        user.balance = new_balance
        return True
            
    async def delete_user(self, user_id: int) -> bool:
        """Delete a user"""
        user = await self.get_user_by_id(user_id)
        if user:
            await self.session.delete(user)
            return True
        return False
    
    async def get_users_by_role(self, role: str) -> List[User]:
        """Get users by role"""
        query = select(User).where(User.role == role)
        result = await self.session.execute(query)
        return list(result.scalars().all())
