from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_back_button(callback_data: str = "main_menu") -> InlineKeyboardButton:
    """Creates a standard back button."""
    return InlineKeyboardButton(text="🔙 بازگشت", callback_data=callback_data)

def get_cancel_button(callback_data: str = "cancel_action") -> InlineKeyboardButton:
    """Creates a standard cancel button."""
    return InlineKeyboardButton(text="❌ لغو", callback_data=callback_data)

def get_cancel_keyboard(callback_data: str = "cancel_action") -> InlineKeyboardMarkup:
    """Get a simple keyboard with just a cancel button."""
    builder = InlineKeyboardBuilder()
    builder.add(get_cancel_button(callback_data))
    return builder.as_markup() 