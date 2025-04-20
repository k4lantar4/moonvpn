# سرویس مدیریت کاربران، ثبت‌نام و پروفایل

"""
سرویس مدیریت کاربران
"""

from typing import Optional
from sqlalchemy.orm import Session

from db.repositories.user_repo import UserRepository
from db.models.user import User


class UserService:
    """سرویس مدیریت کاربران با منطق کسب و کار مرتبط"""
    
    def __init__(self, db_session: Session):
        """مقداردهی اولیه سرویس"""
        self.user_repo = UserRepository(db_session)
    
    def register_user(self, telegram_id: int, username: Optional[str] = None) -> User:
        """ثبت کاربر جدید یا دریافت اطلاعات کاربر موجود"""
        return self.user_repo.get_or_create_user(telegram_id, username)
    
    def get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """دریافت اطلاعات کاربر با آیدی تلگرام"""
        return self.user_repo.get_by_telegram_id(telegram_id)
    
    def is_user_registered(self, telegram_id: int) -> bool:
        """بررسی اینکه آیا کاربر در سیستم ثبت شده است"""
        return self.get_user_by_telegram_id(telegram_id) is not None
    
    def is_admin(self, telegram_id: int) -> bool:
        """بررسی اینکه آیا کاربر ادمین است"""
        user = self.get_user_by_telegram_id(telegram_id)
        if not user:
            return False
        return user.role.value == "admin"
    
    def update_username(self, telegram_id: int, new_username: str) -> Optional[User]:
        """بروزرسانی نام کاربری"""
        user = self.get_user_by_telegram_id(telegram_id)
        if user:
            user.username = new_username
            return user
        return None
