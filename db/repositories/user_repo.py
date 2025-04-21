"""
ریپوزیتوری عملیات دیتابیسی مرتبط با کاربران
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from typing import Optional, List

from db.models.user import User, UserRole
from .base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    """کلاس مدیریت عملیات CRUD کاربران در دیتابیس"""
    
    def __init__(self, session: AsyncSession):
        """مقداردهی اولیه با سشن دیتابیس"""
        super().__init__(User, session)
        
    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """دریافت کاربر با آیدی تلگرام"""
        query = select(User).where(User.telegram_id == telegram_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """دریافت کاربر با شناسه داخلی"""
        return await super().get_by_id(user_id)
    
    async def create_user(self, telegram_id: int, username: Optional[str] = None) -> User:
        """ایجاد کاربر جدید"""
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
            return await self.get_by_telegram_id(telegram_id)
            
    async def get_or_create_user(self, telegram_id: int, username: Optional[str] = None) -> User:
        """دریافت کاربر در صورت وجود یا ایجاد کاربر جدید"""
        user = await self.get_by_telegram_id(telegram_id)
        if user:
            # اگر یوزرنیم تغییر کرده بود، آپدیت شود
            if username and user.username != username:
                user.username = username
                await self.session.commit()
            return user
        return await self.create_user(telegram_id, username)
    
    async def get_all_users(self) -> List[User]:
        """دریافت همه کاربران"""
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
        user = await self.get_by_telegram_id(telegram_id)
        if user:
            user.status = status
            await self.session.commit()
            await self.session.refresh(user)
        return user
