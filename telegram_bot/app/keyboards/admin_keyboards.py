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
            InlineKeyboardButton("⚙️ تنظیمات", callback_data='admin_settings'),
            InlineKeyboardButton("📊 گزارشات", callback_data='admin_reports'),
        ],
        # Add more buttons here as needed
    ]
    return InlineKeyboardMarkup(keyboard) 