"""
هندلرهای کالبک برای مدیریت کاربران در پنل ادمین
"""

import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.utils.keyboard import InlineKeyboardBuilder

from core.services.user_service import UserService
from bot.buttons.admin.user_buttons import get_user_list_keyboard, get_user_manage_buttons
from bot.buttons.admin.main_buttons import get_admin_panel_keyboard

logger = logging.getLogger(__name__)

def register_admin_user_callbacks(router: Router) -> None:
    """ثبت کالبک‌های مدیریت کاربران در پنل ادمین"""
    
    @router.callback_query(F.data == "admin:users")
    async def admin_users(callback: CallbackQuery, session: AsyncSession) -> None:
        """
        هندلر کلیک روی دکمه مدیریت کاربران
        
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
            
            # دریافت لیست کاربران
            users = await user_service.get_all_users()
            
            # ساخت کیبورد لیست کاربران
            keyboard = get_user_list_keyboard(users[:10])  # نمایش 10 کاربر اول
            
            await callback.message.edit_text(
                "👥 <b>مدیریت کاربران</b>\n\n"
                f"🔢 تعداد کل کاربران: {len(users)}\n\n"
                "لطفاً کاربر مورد نظر را انتخاب کنید:",
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            
        except Exception as e:
            logger.error(f"خطا در کالبک مدیریت کاربران: {e}", exc_info=True)
            await callback.answer("⚠️ خطا در اجرای درخواست", show_alert=True)
    
    @router.callback_query(F.data.startswith("user:manage:"))
    async def user_manage(callback: CallbackQuery, session: AsyncSession) -> None:
        """
        هندلر کلیک روی دکمه مدیریت کاربر خاص
        
        Args:
            callback (CallbackQuery): کالبک تلگرام
            session (AsyncSession): نشست دیتابیس
        """
        try:
            # بررسی دسترسی ادمین
            user_service = UserService(session)
            admin = await user_service.get_user_by_telegram_id(callback.from_user.id)
            
            if not admin or admin.role not in ["admin", "superadmin"]:
                await callback.answer("⛔️ دسترسی غیرمجاز!", show_alert=True)
                return
            
            # دریافت شناسه کاربر از کالبک
            user_id = int(callback.data.split(":")[-1])
            
            # دریافت اطلاعات کاربر
            user = await user_service.get_user(user_id)
            
            if not user:
                await callback.answer("⚠️ کاربر مورد نظر یافت نشد!", show_alert=True)
                return
            
            # ساخت کیبورد مدیریت کاربر
            keyboard = get_user_manage_buttons(user.id)
            
            # نمایش اطلاعات کاربر
            user_info = (
                f"👤 <b>اطلاعات کاربر</b>\n\n"
                f"🆔 شناسه: {user.id}\n"
                f"📱 تلگرام: {user.telegram_id}\n"
                f"👤 نام: {user.first_name} {user.last_name or ''}\n"
                f"🌟 نقش: {user.role}\n"
                f"📅 تاریخ ثبت‌نام: {user.created_at.strftime('%Y-%m-%d')}\n"
            )
            
            await callback.message.edit_text(
                user_info,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            
        except Exception as e:
            logger.error(f"خطا در مدیریت کاربر: {e}", exc_info=True)
            await callback.answer("⚠️ خطا در اجرای درخواست", show_alert=True)
    
    # اینجا کالبک‌های اضافی مربوط به مدیریت کاربران را اضافه کنید 