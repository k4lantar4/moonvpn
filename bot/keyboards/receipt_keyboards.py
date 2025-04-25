from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def get_receipt_admin_keyboard(receipt_id: int) -> InlineKeyboardMarkup:
    """Builds the admin keyboard for managing a receipt."""
    buttons = [
        [
            InlineKeyboardButton(text="✅ تایید", callback_data=f"confirm_receipt:{receipt_id}"),
            InlineKeyboardButton(text="❌ رد", callback_data=f"reject_receipt:{receipt_id}")
        ],
        [
            InlineKeyboardButton(text="💬 پیام به کاربر", callback_data=f"message_user:{receipt_id}")
            # Optional: Add a note button
            # InlineKeyboardButton(text="📝 یادداشت‌گذاری", callback_data=f"note_receipt:{receipt_id}")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons) 