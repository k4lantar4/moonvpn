"""
دستور خرید پلن و ایجاد اکانت VPN
"""

import logging
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from core.services.plan_service import PlanService
from bot.buttons.plan_buttons import get_plans_keyboard

logger = logging.getLogger(__name__)

def register_buy_command(router: Router, session_pool):
    """ثبت دستور خرید"""
    
    @router.message(Command("buy"))
    async def buy_command(message: Message):
        """پردازش دستور خرید"""
        try:
            # ایجاد جلسه دیتابیس
            session = session_pool()
            
            try:
                # دریافت لیست پلن‌های فعال
                plan_service = PlanService(session)
                plans = plan_service.get_all_plans(active_only=True)
                
                if not plans:
                    await message.answer(
                        "⚠️ در حال حاضر هیچ پلنی برای خرید موجود نیست.\n"
                        "لطفاً بعداً دوباره تلاش کنید."
                    )
                    return
                
                # نمایش لیست پلن‌ها
                await message.answer(
                    "🛍 لطفاً پلن مورد نظر خود را انتخاب کنید:",
                    reply_markup=get_plans_keyboard(plans)
                )
                
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Error in buy command: {e}")
            await message.answer(
                "خطایی در پردازش درخواست رخ داد. لطفاً دوباره تلاش کنید."
            ) 