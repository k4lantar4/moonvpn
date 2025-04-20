"""
سرویس ارسال پیام به کاربران، ادمین‌ها و کانال
"""

import logging
import asyncio
from typing import List, Optional, Union
from sqlalchemy.orm import Session

from core import settings

logger = logging.getLogger(__name__)

class NotificationService:
    """سرویس مدیریت نوتیفیکیشن‌ها با قابلیت ارسال به کاربران، ادمین‌ها و کانال عمومی"""
    
    def __init__(self, db_session: Session):
        """مقداردهی اولیه سرویس"""
        self.db_session = db_session
        # در اینجا bot_instance در زمان اجرا تنظیم می‌شود
        # مقدار پیش‌فرض None است اما در init_bot این مقدار تنظیم می‌شود
        self.bot_instance = None
    
    def set_bot(self, bot):
        """تنظیم نمونه بات برای ارسال پیام‌ها"""
        self.bot_instance = bot
        
    def notify_user(self, user_id: int, message: str) -> bool:
        """
        ارسال پیام به یک کاربر
        
        Args:
            user_id (int): شناسه تلگرام کاربر
            message (str): متن پیام
            
        Returns:
            bool: موفقیت یا عدم موفقیت ارسال
        """
        try:
            # اگر بات تنظیم شده باشد، پیام را ارسال می‌کنیم
            if self.bot_instance:
                # در حالت اجرا، پیام به کاربر ارسال می‌شود
                try:
                    # برای بات‌های aiogram، باید کد ارسال را به صورت async اجرا کنیم
                    event_loop = asyncio.get_event_loop()
                    if not event_loop.is_running():
                        # اگر event loop در حال اجرا نباشد، یک loop جدید ایجاد می‌کنیم
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        loop.run_until_complete(self._send_telegram_message(user_id, message))
                    else:
                        # اگر event loop در حال اجرا باشد، از create_task استفاده می‌کنیم
                        asyncio.create_task(self._send_telegram_message(user_id, message))
                except Exception as e:
                    logger.error(f"Error sending async telegram message: {e}")
                
                logger.info(f"Notification sent to user {user_id}: {message[:50]}...")
                return True
            else:
                # در حالت CLI یا تست، پیام در لاگ ثبت می‌شود
                logger.info(f"[CLI MODE] Would send to user {user_id}: {message}")
                return True
        except Exception as e:
            logger.error(f"Failed to send notification to user {user_id}: {str(e)}")
            return False
    
    async def _send_telegram_message(self, user_id: int, message: str):
        """
        ارسال پیام تلگرام به صورت async
        
        Args:
            user_id (int): شناسه تلگرام کاربر
            message (str): متن پیام
        """
        try:
            await self.bot_instance.send_message(chat_id=user_id, text=message)
            logger.info(f"Async message sent to user {user_id}")
        except Exception as e:
            logger.error(f"Error in async message sending: {str(e)}")
    
    def notify_admin(self, message: str) -> bool:
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
            if not self.bot_instance:
                for admin_id in admin_ids:
                    logger.info(f"[CLI MODE] Would send to admin {admin_id}: {message}")
                return True
            
            # در حالت اجرای ربات، پیام به همه ادمین‌ها ارسال می‌شود
            success = True
            for admin_id in admin_ids:
                if not self.notify_user(admin_id, message):
                    success = False
            
            return success
        except Exception as e:
            logger.error(f"Failed to send notification to admins: {str(e)}")
            return False
    
    def notify_channel(self, message: str) -> bool:
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
            if not self.bot_instance:
                logger.info(f"[CLI MODE] Would send to channel {channel_id}: {message}")
                return True
            
            # در حالت اجرای ربات، پیام به کانال ارسال می‌شود
            try:
                # برای بات‌های aiogram، باید کد ارسال را به صورت async اجرا کنیم
                event_loop = asyncio.get_event_loop()
                if not event_loop.is_running():
                    # اگر event loop در حال اجرا نباشد، یک loop جدید ایجاد می‌کنیم
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(self._send_telegram_message(channel_id, message))
                else:
                    # اگر event loop در حال اجرا باشد، از create_task استفاده می‌کنیم
                    asyncio.create_task(self._send_telegram_message(channel_id, message))
            except Exception as e:
                logger.error(f"Error sending async telegram message to channel: {e}")
                
            logger.info(f"Channel notification sent: {message[:50]}...")
            return True
        except Exception as e:
            logger.error(f"Failed to send notification to channel: {str(e)}")
            return False
