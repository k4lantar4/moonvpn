import logging
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from bot.filters.role import IsAdminFilter # Assuming Role enum exists
from bot.services.panel_service import PanelService
from bot.dependencies import get_async_session
from core.database.models import User # For type hinting message.from_user

logger = logging.getLogger(__name__)

# Create a new router for admin panel management commands
admin_panel_router = Router()
admin_panel_router.message.filter(IsAdminFilter())
admin_panel_router.callback_query.filter(IsAdminFilter())


@admin_panel_router.message(Command("syncinbounds"))
async def sync_inbounds_handler(message: types.Message, state: FSMContext, user: User):
    """Handles the /syncinbounds command for admins."""
    logger.info(f"Admin {user.id} initiated inbound sync.")
    # Get session and service
    session = await anext(get_async_session()) # Get session via dependency
    panel_service = PanelService(session)
    
    await message.answer("⏳ در حال همگام‌سازی inboundها از پنل‌های فعال... لطفاً کمی صبر کنید.")

    try:
        sync_result = await panel_service.sync_inbounds_from_panels()
        
        # Format the result message
        result_message = f"✅ **همگام‌سازی Inboundها تمام شد!**\n\n"
        result_message += f"- پنل‌های بررسی شده: {len(sync_result.get('details', []))}\n"
        result_message += f"- پنل‌های موفق: {sync_result.get('synced_panels', 0)}\n"
        result_message += f"- مجموع Inboundهای همگام شده: {sync_result.get('total_inbounds', 0)}\n\n"
        
        if sync_result.get('details'):
            result_message += "**جزئیات هر پنل:**\n"
            for detail in sync_result['details']:
                status_emoji = "✔️" if detail['status'] == "Success" else "❌"
                result_message += f"  {status_emoji} پنل {detail['panel_name']} (ID: {detail['panel_id']}): "
                if detail['status'] == "Success":
                    result_message += f"{detail['inbounds_synced']} inbound همگام شد.\n"
                else:
                    result_message += f"خطا - {detail.get('error', 'Unknown error')}\n"
                    
        await message.answer(result_message, parse_mode="Markdown")
        logger.info(f"Inbound sync completed. Result: {sync_result}")

    except Exception as e:
        logger.exception(f"Error during /syncinbounds command for admin {user.id}: {e}")
        await message.answer(f"❌ متاسفانه هنگام همگام‌سازی خطای غیرمنتظره‌ای رخ داد: {e}")
    finally:
        await session.close()

# --- Add other panel management handlers here later --- 
# (e.g., /addpanel, /listpanels, /removepanel) 