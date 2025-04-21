"""
فرمان /start - شروع کار با ربات و ثبت‌نام کاربر
"""

import logging
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.services.user_service import UserService
from bot.buttons.start_buttons import get_start_keyboard

# تنظیم لاگر
logger = logging.getLogger(__name__)

def register_start_command(router: Router, session_pool: async_sessionmaker[AsyncSession]):
    """ثبت فرمان /start برای شروع کار با ربات"""
    
    @router.message(Command("start"))
    async def cmd_start(message: Message):
        """پردازش فرمان /start و ثبت‌نام کاربر"""
        user_id = message.from_user.id
        username = message.from_user.username
        logger.info(f"Start command received from user {user_id}")
        
        try:
            # ایجاد جلسه دیتابیس
            async with session_pool() as session:
                # ثبت یا به‌روزرسانی اطلاعات کاربر
                user_service = UserService(session)
                user = await user_service.register_user(
                    telegram_id=user_id,
                    username=username
                )
                
                # ارسال پیام خوش‌آمدگویی
                welcome_text = (
                    f"👋 سلام {message.from_user.first_name} عزیز!\n\n"
                    "به ربات MoonVPN خوش آمدید. من اینجا هستم تا به شما در خرید و مدیریت "
                    "اکانت VPN کمک کنم.\n\n"
                    "چه کاری می‌توانم برای شما انجام دهم؟"
                )
                
                await message.answer(
                    text=welcome_text,
                    reply_markup=get_start_keyboard(user.role)
                )
                logger.info(f"Sent welcome message to user {user_id}")
                
        except Exception as e:
            logger.error(f"Error in start command: {e}", exc_info=True)
            await message.answer(
                "متأسفانه در حال حاضر امکان ثبت‌نام وجود ندارد. لطفاً کمی بعد دوباره تلاش کنید."
            )
