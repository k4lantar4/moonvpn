"""
Language selection handlers for the Telegram bot.

This module provides handlers for managing user language preferences.
"""

import logging
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.inline.language_kb import language_selection_keyboard
from bot.services.user_service import UserService
from core.config import settings
# Assuming translation utility exists
# from bot.utils.translation import gettext_lazy as _ 
# Placeholder for translation
def _(text):
    return text

logger = logging.getLogger(__name__)

router = Router(name="language-handlers")

@router.message(Command("language"))
async def language_command_handler(message: types.Message, state: FSMContext, session: AsyncSession): # Changed user_service to session
    """Handles the /language command, offering language selection."""
    user_id = message.from_user.id
    logger.info(f"User {user_id} initiated /language command.")
    await state.clear() # Clear any previous state
    
    user_service = UserService() # Instantiate service
    try:
        current_lang = await user_service.get_user_language(session, telegram_id=user_id)
    except Exception as e:
        logger.error(f"Error getting language for user {user_id}: {e}", exc_info=True)
        current_lang = None
        await message.reply(_("Error fetching current language setting."))
        return

    await message.answer(
        text=_("Please select your preferred language. Current: {current_lang}").format(current_lang=current_lang or 'default'),
        reply_markup=language_selection_keyboard()
    )

@router.callback_query(F.data.startswith("set_lang_"))
async def set_language_callback_handler(callback_query: types.CallbackQuery, session: AsyncSession): # Changed user_service to session
    """Handles the language selection callback."""
    lang_code = callback_query.data.split("_")[-1]
    user_id = callback_query.from_user.id
    logger.info(f"User {user_id} selected language: {lang_code}")

    user_service = UserService() # Instantiate service
    updated_user = None
    try:
        # Call service method, passing session
        updated_user = await user_service.update_user_language(session, telegram_id=user_id, lang_code=lang_code)
        if updated_user:
            await session.commit() # Commit on success
            logger.info(f"Successfully updated language for user {user_id} to {lang_code}.")
            await callback_query.message.edit_text(
                text=_("Language updated to {lang_code}.").format(lang_code=lang_code)
            )
            await callback_query.answer(_("Language set!"), show_alert=False)
        else:
            # User not found during update (shouldn't normally happen)
            await session.rollback() # Rollback just in case
            logger.error(f"Failed to update language for user {user_id}: User not found.")
            await callback_query.message.edit_text(
                text=_("Sorry, couldn't find your user record to update the language.")
            )
            await callback_query.answer(_("Error!"), show_alert=True)

    except Exception as e:
        logger.error(f"Error updating language for user {user_id} to {lang_code}: {e}", exc_info=True)
        await session.rollback() # Rollback on any other error
        try:
            await callback_query.message.edit_text(
                text=_("Sorry, there was an error updating your language. Please try again.")
            )
            await callback_query.answer(_("Error!"), show_alert=True)
        except Exception as reply_err:
            logger.error(f"Failed to send error message to user {user_id} after language update failure: {reply_err}")

    # Answer callback query if not already answered in case of success
    # This might not be needed if answer() is always called within try/except
    # await callback_query.answer()

# def setup_handlers(application):
#     """Set up language-related handlers."""
#     application.include_router(router)
#     
#     logger.info("Language handlers registered") 