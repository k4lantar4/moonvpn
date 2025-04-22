"""
فرمان /plans - نمایش لیست پلن‌ها و خرید
"""

import logging
from aiogram import Router
from aiogram.types import Message
from aiogram.filters.command import Command
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.services.plan_service import PlanService
from bot.buttons.plan_buttons import get_plans_keyboard

# تنظیم لاگر
logger = logging.getLogger(__name__)

def register_plans_command(router: Router, session_pool: async_sessionmaker[AsyncSession]):
    """ثبت فرمان /plans برای نمایش لیست پلن‌ها"""
    
    @router.message(Command("plans"))
    async def cmd_plans(message: Message):
        """نمایش لیست پلن‌های موجود به کاربر"""
        logger.info(f"Plans command received from user {message.from_user.id}")
        
        try:
            # ایجاد جلسه دیتابیس با استفاده از async with
            session = session_pool()
            async with session as session:
                # دریافت پلن‌های فعال از سرویس
                plan_service = PlanService(session)
                plans = await plan_service.get_all_active_plans()
                
                # بررسی وجود پلن
                if not plans:
                    await message.answer("هیچ پلنی فعال نیست، لطفاً بعداً دوباره تلاش کنید.")
                    return
                
                # نمایش لیست پلن‌ها با دکمه‌های انتخاب
                await message.answer(
                    text="🔍 لطفاً پلن مورد نظر خود را انتخاب کنید:",
                    reply_markup=get_plans_keyboard(plans)
                )
                logger.info(f"Sent plans list to user {message.from_user.id}")
                
        except Exception as e:
            logger.error(f"Error in plans command: {e}", exc_info=True)
            await message.answer("خطایی در دریافت لیست پلن‌ها رخ داد. لطفاً بعداً دوباره تلاش کنید.")
