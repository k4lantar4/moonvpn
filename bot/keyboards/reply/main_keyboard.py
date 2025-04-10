from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

def get_main_keyboard() -> ReplyKeyboardMarkup:
    """
    Get the main keyboard for the bot.

    Returns:
        ReplyKeyboardMarkup: The main keyboard markup.
    """
    keyboard = ReplyKeyboardBuilder()

    # Add buttons (Consider fetching labels from localization)
    keyboard.button(text="🔑 سرویس‌های من")
    keyboard.button(text="👤 حساب کاربری")
    keyboard.button(text="💰 کیف پول")
    keyboard.button(text="🛒 خرید سرویس") # Renamed from 'خرید پلن'
    keyboard.button(text="🎁 سرویس رایگان (بزودی)")
    keyboard.button(text="📞 پشتیبانی") # Renamed from 'پشتیبانی'
    keyboard.button(text="⚙️ تنظیمات (بزودی)")
    keyboard.button(text="ℹ️ راهنما") # Added Help

    # Adjust layout, e.g., 2 columns
    keyboard.adjust(2)

    return keyboard.as_markup(resize_keyboard=True) 