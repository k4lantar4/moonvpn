"""
هندلرهای کالبک برای مدیریت پلن‌ها در پنل ادمین
"""

import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.utils.keyboard import InlineKeyboardBuilder

from core.services.user_service import UserService
from bot.buttons.admin.plan_buttons import get_plan_list_keyboard, get_plan_manage_buttons

logger = logging.getLogger(__name__)

def register_admin_plan_callbacks(router: Router) -> None:
    """ثبت کالبک‌های مدیریت پلن‌ها در پنل ادمین"""
    
    @router.callback_query(F.data == "admin:plans")
    async def admin_plans(callback: CallbackQuery, session: AsyncSession) -> None:
        """
        هندلر کلیک روی دکمه مدیریت پلن‌ها
        
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
            
            # ساخت کیبورد لیست پلن‌ها
            keyboard = get_plan_list_keyboard()
            
            await callback.message.edit_text(
                "📋 <b>مدیریت پلن‌ها</b>\n\n"
                "لیست پلن‌های موجود را مشاهده کنید یا پلن جدید ایجاد کنید:",
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            
        except Exception as e:
            logger.error(f"خطا در کالبک مدیریت پلن‌ها: {e}", exc_info=True)
            await callback.answer("⚠️ خطا در اجرای درخواست", show_alert=True)
    
    # اینجا کالبک‌های اضافی مربوط به مدیریت پلن‌ها را اضافه کنید 