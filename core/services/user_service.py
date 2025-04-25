# سرویس مدیریت کاربران، ثبت‌نام و پروفایل

"""
سرویس مدیریت کاربران
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from db.repositories.user_repo import UserRepository
from db.models.user import User, UserRole, UserStatus


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
        return await self.user_repo.get_user_by_telegram_id(telegram_id)
    
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
        # Get user first to ensure exists, or adjust repo method
        user = await self.user_repo.get_user_by_telegram_id(telegram_id)
        if not user:
            return None
            
        # Use the updated repo method which doesn't commit
        updated_user = await self.user_repo.update_user(
            user_id=user.id, # Pass user_id
            user_data={'username': new_username}
        )
        if updated_user:
            try:
                await self.user_repo.session.commit()
                await self.user_repo.session.refresh(updated_user)
                return updated_user
            except Exception:
                await self.user_repo.session.rollback()
                raise # Re-raise the exception
        return None # Should not happen if update_user returns the object
    
    async def update_user(
        self,
        user_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None
    ) -> Optional[User]:
        """بروزرسانی اطلاعات کاربر"""
        # Combine first and last name into full_name
        full_name = " ".join(filter(None, [first_name, last_name]))
        update_data = {}
        if username is not None:
            update_data['username'] = username
        if full_name:
            update_data['full_name'] = full_name
            
        if not update_data: # No changes requested
             return await self.user_repo.get_by_id(user_id)
             
        # Use the updated repo method which doesn't commit
        updated_user = await self.user_repo.update_user(user_id, update_data)
        
        if updated_user:
            try:
                await self.user_repo.session.commit()
                await self.user_repo.session.refresh(updated_user)
                return updated_user
            except Exception:
                await self.user_repo.session.rollback()
                raise # Re-raise the exception
        return None # User not found by repo method
    
    async def create_user(
        self,
        telegram_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        role: UserRole = UserRole.USER
    ) -> User:
        """ایجاد کاربر جدید با اطلاعات کامل"""
        # Combine first and last name into full_name
        full_name = " ".join(filter(None, [first_name, last_name]))
        session = self.user_repo.session
        new_user = User(
            telegram_id=telegram_id,
            username=username,
            full_name=full_name,
            role=role,
            created_at=datetime.utcnow(),
            status=UserStatus.ACTIVE,
        )
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
        return new_user
