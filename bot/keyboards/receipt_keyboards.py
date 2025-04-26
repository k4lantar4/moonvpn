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

def create_admin_undo_keyboard(action: str, receipt_id: int) -> InlineKeyboardMarkup:
    """Builds the keyboard for undoing an admin action (confirm/reject)."""
    if action == 'confirm':
        button_text = "↪️ لغو تایید"
        callback_action = "undo_confirm"
    elif action == 'reject':
        button_text = "↪️ لغو رد"
        callback_action = "undo_reject"
    else:
        # Should not happen
        return InlineKeyboardMarkup(inline_keyboard=[]) 

    buttons = [
        [
            InlineKeyboardButton(text=button_text, callback_data=f"{callback_action}:{receipt_id}")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons) 