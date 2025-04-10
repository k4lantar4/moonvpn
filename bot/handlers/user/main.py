"""User handlers."""
import logging

from aiogram import Router # Keep Router
# from aiogram import F, Bot
# from aiogram.filters import Command, StateFilter
# from aiogram.types import Message, CallbackQuery
# from aiogram.fsm.context import FSMContext
# from aiogram.dependencies import Depends

# from sqlalchemy.ext.asyncio import AsyncSession

# from core.database.session import get_db_session # Correct import
# from bot.services import UserService, PlanService, ClientService # Example service imports
# from bot.keyboards.inline import user_keyboards # Example keyboard import
# from bot.states.order_states import OrderSG # Example state import

logger = logging.getLogger(__name__)

# Define user router
user_router = Router()

# --- Commented out all handlers --- 

# Example /start command
# @user_router.message(Command("start"))
# async def cmd_start(message: Message, session: AsyncSession = Depends(get_db_session)):
#     """Handles the /start command, registers or greets the user."""
#     # user_service = UserService(session)
#     # user = await user_service.get_or_create_user(message.from_user)
#     await message.answer(
#         f"سلام {message.from_user.first_name}! ✨\n\nبه ربات MoonVPN خوش آمدید. 🚀",
#         reply_markup=user_keyboards.main_menu_keyboard() # Example usage
#     )

# Example command to view plans
# @user_router.message(Command("plans"))
# async def cmd_plans(message: Message, session: AsyncSession = Depends(get_db_session)):
#     plan_service = PlanService(session)
#     active_plans = await plan_service.get_active_plans()
#     await message.answer("لیست پلان‌های فعال:", reply_markup=user_keyboards.plans_keyboard(active_plans))

# Add more user handlers here (profile, wallet, my_accounts, purchase flow etc.)

# --- End of commented out handlers ---

# Function to register handlers
def register_user_handlers(dp):
    """Register all user handlers."""
    dp.include_router(user_router)
    logger.info("User handlers registered (currently empty).")
