"""
Admin panel callback handlers
"""

import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.services.panel_service import PanelService
from core.services.user_service import UserService
from bot.keyboards.admin_keyboard import get_admin_panel_keyboard
from db.models.panel import PanelStatus

logger = logging.getLogger(__name__)

def register_admin_callbacks(router: Router, session_pool: async_sessionmaker[AsyncSession]) -> None:
    """Register admin panel callback handlers"""
    
    @router.callback_query(F.data == "admin_panel")
    async def admin_panel(callback: CallbackQuery, session: AsyncSession) -> None:
        """Handle admin panel button click"""
        user_id = callback.from_user.id
        
        try:
            # Check if user is admin
            user_service = UserService(session)
            user = await user_service.get_user_by_telegram_id(user_id)
            
            if not user or user.role not in ["admin", "superadmin"]:
                await callback.answer("⛔️ Access denied!", show_alert=True)
                return
            
            # Get admin panel stats
            panel_service = PanelService(session)
            active_panels = await panel_service.get_active_panels()
            
            admin_text = (
                "🎛 <b>Admin Panel</b>\n\n"
                f"📊 Active Panels: {len(active_panels)}\n"
                "Select an option below:"
            )
            
            await callback.message.edit_text(
                admin_text,
                reply_markup=get_admin_panel_keyboard()
            )
            
        except Exception as e:
            logger.error(f"Error in admin panel callback: {e}", exc_info=True)
            await callback.answer("⚠️ Error loading admin panel", show_alert=True)
    
    @router.callback_query(F.data == "sync_panels")
    async def sync_panels(callback: CallbackQuery, session: AsyncSession) -> None:
        """Handle panel sync button click"""
        user_id = callback.from_user.id
        
        try:
            # Check if user is admin
            user_service = UserService(session)
            user = await user_service.get_user_by_telegram_id(user_id)
            
            if not user or user.role not in ["admin", "superadmin"]:
                await callback.answer("⛔️ Access denied!", show_alert=True)
                return
            
            # Sync panels
            panel_service = PanelService(session)
            sync_results = await panel_service.sync_all_panels_inbounds()
            
            await callback.answer(
                f"✅ Successfully synced {len(sync_results)} panels!",
                show_alert=True
            )
            
        except Exception as e:
            logger.error(f"Error in sync panels callback: {e}", exc_info=True)
            await callback.answer("⚠️ Error syncing panels", show_alert=True)
    
    @router.callback_query(F.data == "admin_stats")
    async def admin_stats(callback: CallbackQuery, session: AsyncSession) -> None:
        """Handle admin stats button click"""
        user_id = callback.from_user.id
        
        try:
            # Check if user is admin
            user_service = UserService(session)
            user = await user_service.get_user_by_telegram_id(user_id)
            
            if not user or user.role not in ["admin", "superadmin"]:
                await callback.answer("⛔️ Access denied!", show_alert=True)
                return
            
            # Get stats
            total_users = len(await user_service.get_all_users())
            admins = len(await user_service.get_users_by_role("admin"))
            
            stats_text = (
                "📈 <b>System Statistics</b>\n\n"
                f"👥 Total Users: {total_users}\n"
                f"👮‍♂️ Admins: {admins}\n"
            )
            
            await callback.message.edit_text(
                stats_text,
                reply_markup=get_admin_panel_keyboard()
            )
            
        except Exception as e:
            logger.error(f"Error in admin stats callback: {e}", exc_info=True)
            await callback.answer("⚠️ Error loading stats", show_alert=True)

    @router.callback_query(F.data.startswith("panel_manage:"))
    async def panel_manage(callback: CallbackQuery, session: AsyncSession):
        """Display management menu for a specific panel"""
        await callback.answer()

        try:
            panel_id = int(callback.data.split(":")[1])
            # Fetch panel data
            panel_service = PanelService(session)
            panel = await panel_service.get_panel_by_id(panel_id)

            if not panel:
                await callback.message.answer("❌ پنل مورد نظر یافت نشد.", show_alert=True)
                return

            # Build panel info text with localized status
            status_text = "فعال" if panel.status == PanelStatus.ACTIVE else "غیرفعال" if panel.status == PanelStatus.DISABLED else "حذف شده"
            status_emoji = "✅" if panel.status == PanelStatus.ACTIVE else "❌"
            text = (
                f"📟 پنل #{panel.id} – {panel.flag_emoji} {panel.location_name}\n"
                f"وضعیت: {status_text} {status_emoji}\n"
                f"آدرس: {panel.url}\n"
                f"نوع: {panel.type.value}\n"
                f"یادداشت: {panel.notes or '-'}\n\n"
                "🔧 عملیات پنل:"  
            )

            # Get management buttons
            from bot.buttons.panel_buttons import get_panel_management_keyboard
            keyboard = get_panel_management_keyboard(panel.id)

            # Edit message
            await callback.message.edit_text(text, reply_markup=keyboard)

        except Exception as e:
            logger.error(f"Error in panel_manage handler: {e}", exc_info=True)
            await callback.answer("⚠️ خطایی در نمایش منو رخ داد.", show_alert=True) 