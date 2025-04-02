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
            InlineKeyboardButton("👮‍♂️ مدیریت مدیران پرداخت", callback_data='admin_payment_admins'),
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

# Function to create the reports management keyboard
def get_admin_reports_keyboard() -> InlineKeyboardMarkup:
    """Creates the inline keyboard for admin reports section."""
    keyboard = [
        [
            InlineKeyboardButton("📈 گزارش عملکرد مدیران پرداخت", callback_data='admin_payment_performance'),
            InlineKeyboardButton("💰 گزارش تراکنش‌ها", callback_data='admin_transaction_report'),
        ],
        [
            InlineKeyboardButton("👥 گزارش کاربران", callback_data='admin_user_report'),
        ],
        [
            InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data='admin_back_to_main'),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)

# Function to create date range selection for reports
def get_report_date_range_keyboard() -> InlineKeyboardMarkup:
    """Creates the inline keyboard for selecting report date range."""
    keyboard = [
        [
            InlineKeyboardButton("📅 امروز", callback_data='report_today'),
            InlineKeyboardButton("📆 هفته اخیر", callback_data='report_week'),
        ],
        [
            InlineKeyboardButton("🗓️ ماه اخیر", callback_data='report_month'),
            InlineKeyboardButton("📊 همه زمان‌ها", callback_data='report_all_time'),
        ],
        [
            InlineKeyboardButton("🔙 بازگشت به گزارشات", callback_data='admin_back_to_reports'),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)

# Function to create payment admin management keyboard
def get_payment_admin_management_keyboard() -> InlineKeyboardMarkup:
    """Creates the inline keyboard for payment admin management."""
    keyboard = [
        [
            InlineKeyboardButton("➕ افزودن مدیر پرداخت", callback_data='admin_add_payment_admin'),
            InlineKeyboardButton("📋 لیست مدیران پرداخت", callback_data='admin_list_payment_admins'),
        ],
        [
            InlineKeyboardButton("🔄 تغییر کارت‌های مدیر", callback_data='admin_update_admin_cards'),
            InlineKeyboardButton("❌ حذف مدیر پرداخت", callback_data='admin_remove_payment_admin'),
        ],
        [
            InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data='admin_back_to_main'),
        ],
    ]
    return InlineKeyboardMarkup(keyboard) 