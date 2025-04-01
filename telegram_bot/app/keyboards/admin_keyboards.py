from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Function to create the main admin keyboard
def get_admin_main_keyboard() -> InlineKeyboardMarkup:
    """Creates the main inline keyboard for the admin menu."""
    keyboard = [
        [
            InlineKeyboardButton("👤 مدیریت کاربران", callback_data='admin_manage_users'),
            InlineKeyboardButton("📦 مدیریت پلن‌ها", callback_data='admin_manage_plans'),
        ],
        [
            InlineKeyboardButton("💳 مدیریت کارت‌ها", callback_data='admin_manage_cards'),
            InlineKeyboardButton("📊 گزارشات", callback_data='admin_reports'),
        ],
        [
            InlineKeyboardButton("⚙️ تنظیمات", callback_data='admin_settings'),
        ],
        # Add more buttons here as needed
    ]
    return InlineKeyboardMarkup(keyboard)

# Function to create the bank card management keyboard
def get_admin_card_management_keyboard() -> InlineKeyboardMarkup:
    """Creates the inline keyboard for bank card management."""
    keyboard = [
        [
            InlineKeyboardButton("➕ افزودن کارت جدید", callback_data='admin_add_card'),
            InlineKeyboardButton("📋 لیست کارت‌ها", callback_data='admin_list_cards'),
        ],
        [
            InlineKeyboardButton("🔄 فعال/غیرفعال کردن کارت", callback_data='admin_toggle_card'),
            InlineKeyboardButton("🔢 تغییر اولویت کارت", callback_data='admin_change_priority'),
        ],
        [
            InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data='admin_back_to_main'),
        ],
    ]
    return InlineKeyboardMarkup(keyboard) 