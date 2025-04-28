"""
هندلرهای کالبک اصلی برای پنل ادمین
"""

import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from core.services.panel_service import PanelService
from core.services.user_service import UserService
from bot.buttons.admin.main_buttons import get_admin_panel_keyboard

logger = logging.getLogger(__name__)

def register_admin_main_callbacks(router: Router) -> None:
    """ثبت کالبک‌های اصلی پنل ادمین"""
    
    @router.callback_query(F.data == "admin:panel")
    async def admin_panel(callback: CallbackQuery, session: AsyncSession) -> None:
        """
        هندلر کلیک روی دکمه پنل ادمین
        
        Args:
            callback (CallbackQuery): کالبک تلگرام
            session (AsyncSession): نشست دیتابیس
        """
        user_id = callback.from_user.id
        
        try:
            # بررسی دسترسی ادمین
            user_service = UserService(session)
            user = await user_service.get_user_by_telegram_id(user_id)
            
            if not user or user.role not in ["admin", "superadmin"]:
                await callback.answer("⛔️ دسترسی غیرمجاز!", show_alert=True)
                return
            
            # دریافت آمار پنل ادمین
            panel_service = PanelService(session)
            active_panels = await panel_service.get_active_panels()
            
            admin_text = (
                "🎛 <b>پنل مدیریت</b>\n\n"
                f"📊 پنل‌های فعال: {len(active_panels)}\n"
                "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:"
            )
            
            await callback.message.edit_text(
                admin_text,
                reply_markup=get_admin_panel_keyboard(),
                parse_mode="HTML"
            )
            
        except Exception as e:
            logger.error(f"خطا در کالبک پنل ادمین: {e}", exc_info=True)
            await callback.answer("⚠️ خطا در بارگذاری پنل ادمین", show_alert=True)
    
    @router.callback_query(F.data == "admin:stats")
    async def admin_stats(callback: CallbackQuery, session: AsyncSession) -> None:
        """
        هندلر کلیک روی دکمه آمار ادمین
        
        Args:
            callback (CallbackQuery): کالبک تلگرام
            session (AsyncSession): نشست دیتابیس
        """
        user_id = callback.from_user.id
        
        try:
            # بررسی دسترسی ادمین
            user_service = UserService(session)
            user = await user_service.get_user_by_telegram_id(user_id)
            
            if not user or user.role not in ["admin", "superadmin"]:
                await callback.answer("⛔️ دسترسی غیرمجاز!", show_alert=True)
                return
            
            # دریافت آمار
            total_users = len(await user_service.get_all_users())
            admins = len(await user_service.get_users_by_role("admin"))
            
            stats_text = (
                "📈 <b>آمار سیستم</b>\n\n"
                f"👥 کل کاربران: {total_users}\n"
                f"👮‍♂️ ادمین‌ها: {admins}\n"
            )
            
            await callback.message.edit_text(
                stats_text,
                reply_markup=get_admin_panel_keyboard(),
                parse_mode="HTML"
            )
            
        except Exception as e:
            logger.error(f"خطا در کالبک آمار ادمین: {e}", exc_info=True)
            await callback.answer("⚠️ خطا در بارگذاری آمار", show_alert=True) 