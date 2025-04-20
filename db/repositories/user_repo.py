"""
ریپوزیتوری عملیات دیتابیسی مرتبط با کاربران
"""

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional, List

from db.models.user import User, UserRole


class UserRepository:
    """کلاس مدیریت عملیات CRUD کاربران در دیتابیس"""
    
    def __init__(self, db_session: Session):
        """مقداردهی اولیه با سشن دیتابیس"""
        self.db = db_session
        
    def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """دریافت کاربر با آیدی تلگرام"""
        return self.db.query(User).filter(User.telegram_id == telegram_id).first()
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        """دریافت کاربر با شناسه داخلی"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def create_user(self, telegram_id: int, username: Optional[str] = None) -> User:
        """ایجاد کاربر جدید"""
        try:
            user = User(
                telegram_id=telegram_id,
                username=username,
                role=UserRole.USER
            )
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            return user
        except IntegrityError:
            self.db.rollback()
            # اگر کاربر از قبل وجود داشت، آن را برگردان
            return self.get_by_telegram_id(telegram_id)
            
    def get_or_create_user(self, telegram_id: int, username: Optional[str] = None) -> User:
        """دریافت کاربر در صورت وجود یا ایجاد کاربر جدید"""
        user = self.get_by_telegram_id(telegram_id)
        if user:
            # اگر یوزرنیم تغییر کرده بود، آپدیت شود
            if username and user.username != username:
                user.username = username
                self.db.commit()
            return user
        return self.create_user(telegram_id, username)
    
    def get_all_users(self) -> List[User]:
        """دریافت همه کاربران"""
        return self.db.query(User).all()
    
    def get_all_admins(self) -> List[User]:
        """دریافت همه ادمین‌ها"""
        return self.db.query(User).filter(User.role == UserRole.ADMIN).all()
    
    def update_user_status(self, telegram_id: int, status: bool) -> Optional[User]:
        """بروزرسانی وضعیت کاربر (فعال/غیرفعال)"""
        user = self.get_by_telegram_id(telegram_id)
        if user:
            user.status = status
            self.db.commit()
            self.db.refresh(user)
        return user
