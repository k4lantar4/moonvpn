"""Seller handlers."""
import logging

from aiogram import Router # Keep Router
# from aiogram import F, Bot
# from aiogram.filters import Command, StateFilter
# from aiogram.types import Message, CallbackQuery
# from aiogram.fsm.context import FSMContext
# from aiogram.dependencies import Depends

# from sqlalchemy.ext.asyncio import AsyncSession

# from core.config import settings
# from core.database.session import get_db_session
# from bot.services import SellerService, UserService # Example service imports
# from bot.keyboards.inline import seller_keyboards # Example keyboard import
# from bot.filters.role import RoleFilter # Assuming RoleFilter exists

logger = logging.getLogger(__name__)

# Define seller router
seller_router = Router()

# --- Commented out all handlers --- 

# Assuming RoleFilter checks for 'SELLER' role
# seller_router.message.filter(RoleFilter(role_name="SELLER"))
# seller_router.callback_query.filter(RoleFilter(role_name="SELLER"))

# Example command handler for sellers
# @seller_router.message(Command("seller_panel"))
# async def cmd_seller_panel(message: Message, session: AsyncSession = Depends(get_db_session)):
#     """Handles the /seller_panel command for sellers."""
#     # seller_service = SellerService(session)
#     # referral_link = await seller_service.get_referral_link(message.from_user.id)
#     await message.answer(
#         "پنل فروشندگی 🛍️\n\nبه پنل خود خوش آمدید!",
#         reply_markup=seller_keyboards.main_seller_keyboard() # Example usage
#     )

# Add more seller handlers here...

# --- End of commented out handlers ---

# Function to register handlers
def register_seller_handlers(dp):
    """Register all seller handlers."""
    dp.include_router(seller_router)
    logger.info("Seller handlers registered (currently empty).")
