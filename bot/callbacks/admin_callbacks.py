"""
هندلرهای کالبک پنل ادمین - نسخه بازنویسی شده

این فایل برای حفظ سازگاری با کد قبلی حفظ شده است.
تمام توابع به فایل‌های جداگانه در دایرکتوری admin/ منتقل شده‌اند.
"""

import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.callbacks.admin import register_all_admin_callbacks
from bot.keyboards.admin_keyboard import get_admin_panel_keyboard
from core.services.user_service import UserService
from core.services.panel_service import PanelService
from core.services.plan_service import PlanService
from core.services.notification_service import NotificationService
from bot.buttons.buy_buttons import get_plans_keyboard
from bot.states.buy_states import BuyState

logger = logging.getLogger(__name__)

def register_admin_callbacks(router: Router, session_pool: async_sessionmaker[AsyncSession]) -> None:
    """ثبت تمامی کالبک‌های ادمین"""
    logger.info("فراخوانی کالبک‌های ماژولار ادمین")
    register_all_admin_callbacks(router)

    @router.callback_query(F.data == "admin_panel")
    async def admin_panel_callback(callback: CallbackQuery):
        """نمایش پنل ادمین"""
        await callback.message.edit_text(
            "🎛 <b>پنل مدیریت</b>\n\n"
            "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
            reply_markup=get_admin_panel_keyboard()
        )
        await callback.answer()
    
    @router.callback_query(F.data == "admin:buy")
    async def admin_buy_callback(callback: CallbackQuery, state: FSMContext):
        """
        هدایت ادمین به منوی خرید سرویس
        
        این کالبک برای ایجاد یکپارچگی بین تجربه کاربر عادی و ادمین استفاده می‌شود.
        ادمین‌ها نیز می‌توانند مانند کاربران عادی از روند خرید سرویس استفاده کنند.
        """
        logger.info(f"Admin {callback.from_user.id} using buy service feature")
        
        try:
            # ارجاع به روند خرید با استفاده از کالبک
            await callback.answer("در حال انتقال به صفحه خرید سرویس...")
            
            # پاکسازی وضعیت فعلی
            await state.clear()
            
            user_id = callback.from_user.id
            
            # نمایش پیام در حال بارگذاری
            processing_message = await callback.message.edit_text(
                "🔄 در حال بارگذاری لیست پلن‌ها...\n"
                "لطفا چند لحظه صبر کنید."
            )
            
            # اجرای مستقیم کد به جای فراخوانی cmd_buy
            async with session_pool() as session:
                # بررسی وجود کاربر در سیستم
                user_service = UserService(session)
                user = await user_service.get_user_by_telegram_id(user_id)
                
                if not user:
                    logger.warning(f"Admin {user_id} tried to buy but is not registered")
                    await processing_message.edit_text(
                        "⚠️ شما هنوز در سیستم ثبت‌نام نکرده‌اید!\n"
                        "لطفاً ابتدا با ارسال دستور /start ثبت‌نام کنید."
                    )
                    return
                
                # دریافت پلن‌های فعال
                plan_service = PlanService(session)
                plans = await plan_service.get_all_active_plans()
                
                if not plans:
                    logger.warning(f"No active plans available for admin {user_id}")
                    await processing_message.edit_text(
                        "⚠️ در حال حاضر هیچ پلن فعالی موجود نیست.\n"
                        "لطفاً بعداً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید."
                    )
                    return
                
                # نمایش موجودی کیف پول
                balance = getattr(user, 'balance', 0)
                balance_message = f"💰 موجودی کیف پول شما: {int(balance):,} تومان\n\n"
                
                # نمایش لیست پلن‌ها با دکمه‌های انتخاب
                await processing_message.edit_text(
                    text=balance_message + "🔍 لطفاً پلن مورد نظر خود را انتخاب کنید:",
                    reply_markup=get_plans_keyboard(plans)
                )
                
                # تنظیم وضعیت به انتخاب پلن
                await state.set_state(BuyState.select_plan)
                
                logger.info(f"Sent plans list to admin {user_id} for purchasing. Found {len(plans)} active plans.")
            
        except Exception as e:
            logger.error(f"Error in admin buy callback: {e}", exc_info=True)
            await callback.message.edit_text(
                "❌ خطا در انتقال به صفحه خرید سرویس. لطفاً مجدداً تلاش کنید.",
                reply_markup=get_admin_panel_keyboard()
            )
