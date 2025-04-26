"""
فرمان /buy - خرید پلن و دریافت کانفیگ VPN
"""

import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import async_sessionmaker

from core.services.plan_service import PlanService
from core.services.user_service import UserService
from core.services.notification_service import NotificationService
from bot.buttons.buy_buttons import get_plans_keyboard
from bot.states.buy_states import BuyState

# تنظیم لاگر
logger = logging.getLogger(__name__)

def register_buy_command(router: Router, session_pool: async_sessionmaker):
    """ثبت فرمان /buy برای شروع فرایند خرید"""
    
    @router.message(Command("buy"))
    @router.message(F.text == "🛒 خرید سرویس")
    async def cmd_buy(message: Message, state: FSMContext):
        """شروع فرایند خرید پلن و دریافت کانفیگ"""
        user_id = message.from_user.id
        logger.info(f"Buy command received from user {user_id}")
        
        try:
            # پاکسازی وضعیت فعلی کاربر
            await state.clear()
            
            # ایجاد جلسه دیتابیس
            async with session_pool() as session:
                # بررسی وجود کاربر در سیستم
                user_service = UserService(session)
                user = await user_service.get_user_by_telegram_id(user_id)
                
                if not user:
                    logger.warning(f"User {user_id} tried to buy but is not registered")
                    await message.answer(
                        "⚠️ شما هنوز در سیستم ثبت‌نام نکرده‌اید!\n"
                        "لطفاً ابتدا با ارسال دستور /start ثبت‌نام کنید."
                    )
                    return
                
                # دریافت پلن‌های فعال
                plan_service = PlanService(session)
                plans = await plan_service.get_all_active_plans()
                
                if not plans:
                    logger.warning(f"No active plans available for user {user_id}")
                    await message.answer(
                        "⚠️ در حال حاضر هیچ پلن فعالی موجود نیست.\n"
                        "لطفاً بعداً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید."
                    )
                    
                    # اطلاع‌رسانی به ادمین
                    notification_service = NotificationService(session)
                    await notification_service.notify_admin(
                        f"⚠️ کاربر {user_id} قصد خرید داشت اما هیچ پلن فعالی وجود ندارد!"
                    )
                    return
                
                # نمایش موجودی کیف پول
                balance = getattr(user, 'balance', 0)
                balance_message = f"💰 موجودی کیف پول شما: {int(balance):,} تومان\n\n"
                
                # نمایش لیست پلن‌ها با دکمه‌های انتخاب
                await message.answer(
                    text=balance_message + "🔍 لطفاً پلن مورد نظر خود را انتخاب کنید:",
                    reply_markup=get_plans_keyboard(plans)
                )
                
                # تنظیم وضعیت به انتخاب پلن
                await state.set_state(BuyState.select_plan)
                
                logger.info(f"Sent plans list to user {user_id} for purchasing. Found {len(plans)} active plans.")
                
        except Exception as e:
            logger.error(f"Error in buy command: {e}", exc_info=True)
            await message.answer(
                "❌ متاسفانه خطایی در سیستم رخ داده است.\n"
                "لطفاً بعداً دوباره تلاش کنید یا با استفاده از دستور /support با پشتیبانی تماس بگیرید."
            ) 