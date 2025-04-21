"""
سرویس ارسال پیام به کاربران، ادمین‌ها و کانال
"""

import logging
from typing import List, Optional, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime
from aiogram import Bot

from core import settings
from db.repositories.user_repo import UserRepository
from db.models.notification_log import NotificationLog

logger = logging.getLogger(__name__)

class NotificationService:
    """سرویس مدیریت نوتیفیکیشن‌ها با قابلیت ارسال به کاربران، ادمین‌ها و کانال عمومی"""
    
    def __init__(self, session: AsyncSession):
        """مقداردهی اولیه سرویس"""
        self.session = session
        self.user_repo = UserRepository(session)
        # در اینجا bot_instance در زمان اجرا تنظیم می‌شود
        # مقدار پیش‌فرض None است اما در init_bot این مقدار تنظیم می‌شود
        self.bot: Optional[Bot] = None
    
    def set_bot(self, bot: Bot) -> None:
        """تنظیم نمونه بات برای ارسال پیام‌ها"""
        self.bot = bot
        
    async def notify_user(self, user_id: int, message: str) -> bool:
        """
        ارسال پیام به یک کاربر
        
        Args:
            user_id (int): شناسه تلگرام کاربر
            message (str): متن پیام
            
        Returns:
            bool: موفقیت یا عدم موفقیت ارسال
        """
        if not self.bot:
            return False
        
        try:
            # اگر بات تنظیم شده باشد، پیام را ارسال می‌کنیم
            # در حالت اجرا، پیام به کاربر ارسال می‌شود
            await self.bot.send_message(user_id, message)
            
            # Log notification
            log_entry = NotificationLog(
                user_id=user_id,
                message=message,
                status="sent",
                sent_at=datetime.utcnow()
            )
            self.session.add(log_entry)
            await self.session.flush()
            
            logger.info(f"Notification sent to user {user_id}: {message[:50]}...")
            return True
        except Exception as e:
            # Log failed notification
            log_entry = NotificationLog(
                user_id=user_id,
                message=message,
                status="failed",
                error=str(e),
                sent_at=datetime.utcnow()
            )
            self.session.add(log_entry)
            await self.session.flush()
            
            logger.error(f"Error sending telegram message: {e}")
            return False
    
    async def notify_admin(self, message: str) -> bool:
        """
        ارسال پیام به همه ادمین‌ها
        
        Args:
            message (str): متن پیام
            
        Returns:
            bool: موفقیت یا عدم موفقیت ارسال
        """
        try:
            # لیست شناسه‌های ادمین‌ها
            admin_ids = settings.ADMIN_IDS
            
            # در حالت CLI یا تست، پیام در لاگ ثبت می‌شود
            if not self.bot:
                for admin_id in admin_ids:
                    logger.info(f"[CLI MODE] Would send to admin {admin_id}: {message}")
                return True
            
            # در حالت اجرای ربات، پیام به همه ادمین‌ها ارسال می‌شود
            success = True
            for admin_id in admin_ids:
                if not await self.notify_user(admin_id, message):
                    success = False
            
            return success
        except Exception as e:
            logger.error(f"Failed to send notification to admins: {str(e)}")
            return False
    
    async def notify_channel(self, message: str) -> bool:
        """
        ارسال پیام به کانال عمومی
        
        Args:
            message (str): متن پیام
            
        Returns:
            bool: موفقیت یا عدم موفقیت ارسال
        """
        try:
            # شناسه کانال از تنظیمات
            channel_id = settings.CHANNEL_ID
            
            # در حالت CLI یا تست، پیام در لاگ ثبت می‌شود
            if not self.bot:
                logger.info(f"[CLI MODE] Would send to channel {channel_id}: {message}")
                return True
            
            # در حالت اجرای ربات، پیام به کانال ارسال می‌شود
            try:
                await self.bot.send_message(channel_id, message)
                logger.info(f"Channel notification sent: {message[:50]}...")
                return True
            except Exception as e:
                logger.error(f"Error sending telegram message to channel: {e}")
                return False
        except Exception as e:
            logger.error(f"Failed to send notification to channel: {str(e)}")
            return False
    
    async def notify_admins(self, message: str) -> List[bool]:
        """Send notification to all admin users"""
        admins = await self.user_repo.get_users_by_role("admin")
        results = []
        
        for admin in admins:
            result = await self.notify_user(admin.telegram_id, message)
            results.append(result)
        
        return results
    
    async def get_notification_logs(self, user_id: int, limit: int = 10) -> List[NotificationLog]:
        """Get notification logs for a user"""
        stmt = (
            select(NotificationLog)
            .where(NotificationLog.user_id == user_id)
            .order_by(desc(NotificationLog.sent_at))
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def cleanup(self) -> None:
        """Cleanup resources"""
        if self.bot:
            await self.bot.session.close()
            self.bot = None
        await self.session.close()
