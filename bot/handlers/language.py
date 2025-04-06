"""
Language selection handlers for the Telegram bot.

This module provides handlers for managing user language preferences.
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from core.config import settings
from core.database import get_db
from core.models.user import User
from bot.utils.text import get_language_changed_message

router = Router(name="language")

@router.message(Command("language"))
async def language_command(message: Message):
    """Handle the /language command."""
    # Create language selection keyboard
    builder = InlineKeyboardBuilder()
    for lang in settings.SUPPORTED_LANGUAGES_LIST:
        emoji = "🇮🇷" if lang == "fa" else "🇬🇧"
        text = "فارسی" if lang == "fa" else "English"
        builder.button(text=f"{emoji} {text}", callback_data=f"lang_{lang}")
    builder.adjust(1)
    
    await message.answer(
        "🌐 Please select your language:\n\n"
        "🗣 لطفاً زبان خود را انتخاب کنید:",
        reply_markup=builder.as_markup()
    )

@router.callback_query(F.data.startswith("lang_"))
async def language_callback(callback: CallbackQuery):
    """Handle language selection callback."""
    lang = callback.data.split("_")[1]
    
    # Update user's language preference in database
    async with get_db() as db:
        user = await db.execute(
            User.__table__.update()
            .where(User.telegram_id == callback.from_user.id)
            .values(lang=lang)
        )
        await db.commit()
    
    # Send confirmation message
    await callback.message.edit_text(
        get_language_changed_message(lang),
        reply_markup=None
    )
    await callback.answer() 