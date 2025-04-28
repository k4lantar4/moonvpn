"""
هندلرهای کالبک برای مدیریت سفارشات در پنل ادمین
"""

import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.utils.keyboard import InlineKeyboardBuilder

from core.services.user_service import UserService
from bot.buttons.admin.order_buttons import get_order_list_keyboard, get_order_manage_buttons

logger = logging.getLogger(__name__)

def register_admin_order_callbacks(router: Router) -> None:
    """ثبت کالبک‌های مدیریت سفارشات در پنل ادمین"""
    
    @router.callback_query(F.data == "admin:orders")
    async def admin_orders(callback: CallbackQuery, session: AsyncSession) -> None:
        """
        هندلر کلیک روی دکمه مدیریت سفارشات
        
        Args:
            callback (CallbackQuery): کالبک تلگرام
            session (AsyncSession): نشست دیتابیس
        """
        try:
            # بررسی دسترسی ادمین
            user_service = UserService(session)
            user = await user_service.get_user_by_telegram_id(callback.from_user.id)
            
            if not user or user.role not in ["admin", "superadmin"]:
                await callback.answer("⛔️ دسترسی غیرمجاز!", show_alert=True)
                return
            
            # ساخت کیبورد لیست سفارشات
            # ترجیحاً از یک سرویس برای دریافت سفارشات استفاده کنید
            keyboard = get_order_list_keyboard()
            
            await callback.message.edit_text(
                "🛒 <b>مدیریت سفارشات</b>\n\n"
                "لیست سفارشات اخیر:",
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            
        except Exception as e:
            logger.error(f"خطا در کالبک مدیریت سفارشات: {e}", exc_info=True)
            await callback.answer("⚠️ خطا در اجرای درخواست", show_alert=True)
    
    @router.callback_query(F.data.startswith("order:manage:"))
    async def order_manage(callback: CallbackQuery, session: AsyncSession) -> None:
        """
        هندلر کلیک روی دکمه مدیریت سفارش خاص
        
        Args:
            callback (CallbackQuery): کالبک تلگرام
            session (AsyncSession): نشست دیتابیس
        """
        try:
            # بررسی دسترسی ادمین
            user_service = UserService(session)
            user = await user_service.get_user_by_telegram_id(callback.from_user.id)
            
            if not user or user.role not in ["admin", "superadmin"]:
                await callback.answer("⛔️ دسترسی غیرمجاز!", show_alert=True)
                return
            
            # دریافت شناسه سفارش از کالبک
            order_id = int(callback.data.split(":")[-1])
            
            # ساخت کیبورد مدیریت سفارش
            keyboard = get_order_manage_buttons(order_id)
            
            # نمایش اطلاعات سفارش
            order_info = (
                f"🛒 <b>مدیریت سفارش #{order_id}</b>\n\n"
                "اطلاعات سفارش را در اینجا نمایش دهید...\n"
                "این قسمت باید با اطلاعات واقعی سفارش تکمیل شود."
            )
            
            await callback.message.edit_text(
                order_info,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            
        except Exception as e:
            logger.error(f"خطا در مدیریت سفارش: {e}", exc_info=True)
            await callback.answer("⚠️ خطا در اجرای درخواست", show_alert=True)
    
    # اینجا کالبک‌های اضافی مربوط به مدیریت سفارشات را اضافه کنید 