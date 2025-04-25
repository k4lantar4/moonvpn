from aiogram.types import InlineKeyboardButton

def get_renewal_log_button() -> InlineKeyboardButton:
    """Returns the button for viewing client renewal logs."""
    return InlineKeyboardButton(
        text="📄 گزارش تمدید کلاینت‌ها",
        callback_data="admin:renewal_log"
    ) 