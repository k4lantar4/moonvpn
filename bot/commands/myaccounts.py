"""
فرمان /myaccounts - نمایش اشتراک‌های فعال کاربر
"""

import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters.command import Command
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

# تنظیم لاگر
logger = logging.getLogger(__name__)

async def cmd_myaccounts(message: Message):
    """نمایش لیست اشتراک‌های فعال کاربر"""
    user_id = message.from_user.id
    logger.info(f"MyAccounts command received from user {user_id}")
    
    try:
        # TODO: Implement logic to fetch user accounts from db
        # For now, just send a placeholder message
        await message.answer(
            "📊 اشتراک‌های من:\n\n" 
            "شما هنوز هیچ اشتراکی فعال ندارید.\n\n"
            "برای خرید اشتراک از دکمه '🛒 خرید اشتراک' استفاده کنید."
        )
        logger.info(f"Sent my accounts placeholder to user {user_id}")
        
    except Exception as e:
        logger.error(f"Error in myaccounts command: {e}", exc_info=True)
        await message.answer("خطایی در دریافت لیست اشتراک‌ها رخ داد. لطفاً بعداً دوباره تلاش کنید.")

def register_myaccounts_command(router: Router, session_pool: async_sessionmaker[AsyncSession]):
    """ثبت فرمان /myaccounts و هندلر متن مربوطه"""
    
    # ثبت هندلر برای دستور /myaccounts
    router.message.register(cmd_myaccounts, Command("myaccounts"))
    
    # ثبت هندلر برای متن دکمه "اشتراک‌های من"
    router.message.register(cmd_myaccounts, F.text == "📊 اشتراک‌های من") 