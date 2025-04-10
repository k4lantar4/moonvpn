"""Admin handlers."""
import logging

from aiogram import Router # Keep Router
# from aiogram import F, Bot
# from aiogram.filters import Command, StateFilter
# from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
# from aiogram.fsm.context import FSMContext
# from aiogram.fsm.state import State, StatesGroup
# from aiogram.enums import ParseMode
# from aiogram.dependencies import Depends

# from sqlalchemy.ext.asyncio import AsyncSession

# from bot.services.user import UserService
# from bot.services.plan import PlanService # Need PlanService
# from bot.services.location import LocationService # Need LocationService
# from bot.services.category import CategoryService # Need CategoryService
# from bot.services.statistics import StatisticsService # Need StatisticsService
# from core.database.session import get_db_session
# from core.exceptions import ServiceError, NotFoundError
# from core.config import settings # Import settings

# from bot.keyboards.inline import admin_keyboards as inline_admin_keyboards # Example keyboard import
# from bot.filters.role import RoleFilter # Assuming RoleFilter exists

logger = logging.getLogger(__name__)

# Define admin router
admin_router = Router()

# --- Commented out all handlers --- 

# @admin_router.message.filter(RoleFilter(admin_ids=settings.ADMIN_IDS.split(',')))
# @admin_router.callback_query.filter(RoleFilter(admin_ids=settings.ADMIN_IDS.split(',')))

# Example command handler for admins
# @admin_router.message(Command("admin_panel"))
# async def cmd_admin_panel(message: Message, session: AsyncSession = Depends(get_db_session)):
#     """Handles the /admin_panel command for administrators."""
#     # admin_service = AdminService(session)
#     # user_count = await admin_service.get_total_users() # Example usage
#     await message.answer(
#         "پنل مدیریت 🛡️\n\nلطفا یک گزینه را انتخاب کنید:",
#         reply_markup=inline_admin_keyboards.main_admin_keyboard() # Example usage
#     )

# Add more admin handlers here...

# Example callback query handler
# @admin_router.callback_query(F.data == "manage_users")
# async def cq_manage_users(callback: CallbackQuery, session: AsyncSession = Depends(get_db_session)):
#     await callback.message.edit_text("مدیریت کاربران...", reply_markup=...)
#     await callback.answer()

# --- End of commented out handlers ---

# Function to register handlers (remains the same, but router has no handlers attached)
def register_admin_handlers(dp):
    """Register all admin handlers."""
    dp.include_router(admin_router)
    logger.info("Admin handlers registered (currently empty).")
