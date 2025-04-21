"""
فرمان /buy - خرید پلن و دریافت کانفیگ VPN
"""

import logging
from aiogram import Router
from aiogram.types import Message
from aiogram.filters.command import Command
from sqlalchemy.ext.asyncio import async_sessionmaker

from core.services.plan_service import PlanService
from core.services.panel_service import PanelService
from core.services.user_service import UserService
from bot.buttons.plan_buttons import get_plans_keyboard

# تنظیم لاگر
logger = logging.getLogger(__name__)

def register_buy_command(router: Router, session_pool):
    """ثبت فرمان /buy برای شروع فرایند خرید"""
    
    @router.message(Command("buy"))
    async def cmd_buy(message: Message):
        """شروع فرایند خرید پلن و دریافت کانفیگ"""
        user_id = message.from_user.id
        logger.info(f"Buy command received from user {user_id}")
        
        try:
            # ایجاد جلسه دیتابیس
            async with session_pool() as session:
                # بررسی وجود کاربر در سیستم
                user_service = UserService(session)
                user = await user_service.get_user_by_telegram_id(user_id)
                
                if not user:
                    await message.answer(
                        "⚠️ شما هنوز در سیستم ثبت‌نام نکرده‌اید!\n"
                        "لطفاً ابتدا با ارسال دستور /start ثبت‌نام کنید."
                    )
                    return
                
                # دریافت پلن‌های فعال
                plan_service = PlanService(session)
                plans = await plan_service.get_all_active_plans()
                
                if not plans:
                    await message.answer("در حال حاضر هیچ پلنی برای خرید موجود نیست.")
                    return
                
                # نمایش موجودی کیف پول
                balance_message = f"💰 موجودی کیف پول شما: {int(user.balance):,} تومان\n\n"
                
                # نمایش لیست پلن‌ها با دکمه‌های انتخاب
                await message.answer(
                    text=balance_message + "🔍 لطفاً پلن مورد نظر خود را انتخاب کنید:",
                    reply_markup=get_plans_keyboard(plans)
                )
                
                logger.info(f"Sent plans list to user {user_id} for purchasing")
                
        except Exception as e:
            logger.error(f"Error in buy command: {e}", exc_info=True)
            await message.answer("خطایی در پردازش درخواست رخ داد. لطفاً بعداً دوباره تلاش کنید.") 