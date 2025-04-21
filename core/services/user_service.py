# سرویس مدیریت کاربران، ثبت‌نام و پروفایل

"""
سرویس مدیریت کاربران
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from db.repositories.user_repo import UserRepository
from db.models.user import User


class UserService:
    """سرویس مدیریت کاربران با منطق کسب و کار مرتبط"""
    
    def __init__(self, session: AsyncSession):
        """مقداردهی اولیه سرویس"""
        self.user_repo = UserRepository(session)
    
    async def register_user(self, telegram_id: int, username: Optional[str] = None) -> User:
        """ثبت کاربر جدید یا دریافت اطلاعات کاربر موجود"""
        return await self.user_repo.get_or_create_user(telegram_id, username)
    
    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """دریافت اطلاعات کاربر با آیدی تلگرام"""
        return await self.user_repo.get_by_telegram_id(telegram_id)
    
    async def is_user_registered(self, telegram_id: int) -> bool:
        """بررسی اینکه آیا کاربر در سیستم ثبت شده است"""
        user = await self.get_user_by_telegram_id(telegram_id)
        return user is not None
    
    async def is_admin(self, telegram_id: int) -> bool:
        """بررسی اینکه آیا کاربر ادمین است"""
        user = await self.get_user_by_telegram_id(telegram_id)
        if not user:
            return False
        return user.role.value == "admin"
    
    async def update_username(self, telegram_id: int, new_username: str) -> Optional[User]:
        """بروزرسانی نام کاربری"""
        # Rely on repository to handle commit and refresh
        return await self.user_repo.update_user(
            telegram_id=telegram_id,
            update_data={'username': new_username}
        )
