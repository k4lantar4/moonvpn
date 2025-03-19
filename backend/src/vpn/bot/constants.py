from typing import Dict, Any

# Menu Types
MENU_MAIN = "main"
MENU_PLANS = "plans"
MENU_PROFILE = "profile"
MENU_WALLET = "wallet"
MENU_SETTINGS = "settings"
MENU_SUPPORT = "support"
MENU_ADMIN = "admin"
MENU_RESELLER = "reseller"

# Callback Actions
ACTION_SELECT = "select"
ACTION_PURCHASE = "purchase"
ACTION_CANCEL = "cancel"
ACTION_PAGE = "page"
ACTION_BACK = "back"

# Message Templates
MESSAGES: Dict[str, Dict[str, str]] = {
    # Common Messages
    "start": {
        "en": (
            "Welcome to MoonVPN! 🌙\n\n"
            "I'm your personal VPN assistant. Here's what I can do for you:\n\n"
            "🔹 Show available plans\n"
            "🔹 Manage your subscriptions\n"
            "🔹 Handle payments\n"
            "🔹 Provide support\n\n"
            "Use the menu below to get started!"
        ),
        "fa": (
            "به MoonVPN خوش آمدید! 🌙\n\n"
            "من دستیار شخصی VPN شما هستم. خدماتی که می‌توانم ارائه دهم:\n\n"
            "🔹 نمایش پلن‌های موجود\n"
            "🔹 مدیریت اشتراک‌ها\n"
            "🔹 مدیریت پرداخت‌ها\n"
            "🔹 پشتیبانی\n\n"
            "از منوی زیر شروع کنید!"
        )
    },
    
    "no_permission": {
        "en": "You don't have permission to use this command.",
        "fa": "شما مجوز استفاده از این دستور را ندارید."
    },
    
    "create_account_first": {
        "en": "Please use /start to create an account first.",
        "fa": "لطفاً ابتدا با دستور /start حساب کاربری ایجاد کنید."
    },
    
    # Plans Messages
    "select_plan": {
        "en": "Please select a plan:",
        "fa": "لطفاً یک پلن را انتخاب کنید:"
    },
    
    "no_plans": {
        "en": "No plans available at the moment. Please try again later.",
        "fa": "در حال حاضر هیچ پلنی موجود نیست. لطفاً بعداً دوباره امتحان کنید."
    },
    
    # Wallet Messages
    "enter_amount": {
        "en": "💰 Please enter the amount you want to deposit:\n\nExample: 100",
        "fa": "💰 لطفاً مبلغ مورد نظر برای شارژ کیف پول را وارد کنید:\n\nمثال: 100000"
    },
    
    "invalid_amount": {
        "en": "Please enter a valid amount.",
        "fa": "لطفاً یک مبلغ معتبر وارد کنید."
    },
    
    # Support Messages
    "support_welcome": {
        "en": (
            "📞 MoonVPN Support\n\n"
            "To contact support, send your message.\n"
            "Our support team will respond as soon as possible."
        ),
        "fa": (
            "📞 پشتیبانی MoonVPN\n\n"
            "برای ارتباط با پشتیبانی، پیام خود را ارسال کنید.\n"
            "تیم پشتیبانی در اسرع وقت به شما پاسخ خواهد داد."
        )
    },
    
    # Settings Messages
    "invalid_email": {
        "en": "Please enter a valid email address.",
        "fa": "لطفاً یک آدرس ایمیل معتبر وارد کنید."
    },
    
    "email_updated": {
        "en": "✅ Your email has been updated successfully.",
        "fa": "✅ ایمیل شما با موفقیت به‌روزرسانی شد."
    },
    
    "invalid_phone": {
        "en": "Please enter a valid phone number.",
        "fa": "لطفاً یک شماره تماس معتبر وارد کنید."
    },
    
    "phone_updated": {
        "en": "✅ Your phone number has been updated successfully.",
        "fa": "✅ شماره تماس شما با موفقیت به‌روزرسانی شد."
    },
    
    # Error Messages
    "general_error": {
        "en": "An error occurred. Please try again later.",
        "fa": "خطایی رخ داد. لطفاً بعداً دوباره امتحان کنید."
    },
    
    "payment_error": {
        "en": "Sorry, payment creation failed. Please try again later.",
        "fa": "متأسفانه ایجاد پرداخت با خطا مواجه شد. لطفاً بعداً دوباره امتحان کنید."
    },
    
    "invalid_action": {
        "en": "Invalid action. Please try again.",
        "fa": "عملیات نامعتبر. لطفاً دوباره امتحان کنید."
    },
    
    "unknown_command": {
        "en": "I don't understand that command. Use /help to see available commands.",
        "fa": "این دستور را نمی‌شناسم. برای دیدن دستورات موجود از /help استفاده کنید."
    },
    
    # Support messages
    'support_menu_fa': (
        "📞 پشتیبانی MoonVPN\n\n"
        "برای ارتباط با پشتیبانی، پیام خود را ارسال کنید.\n"
        "تیم پشتیبانی در اسرع وقت به شما پاسخ خواهد داد.\n\n"
    ),
    'support_menu_en': (
        "📞 MoonVPN Support\n\n"
        "To contact support, send your message.\n"
        "Our support team will respond as soon as possible.\n\n"
    ),
    'active_tickets_fa': "🎫 تیکت‌های فعال شما:\n",
    'active_tickets_en': "🎫 Your Active Tickets:\n",
    'no_tickets_fa': "🎫 شما هیچ تیکت فعالی ندارید.\n",
    'no_tickets_en': "🎫 You have no active tickets.\n",
    'ticket_created_fa': (
        "✅ پیام شما با موفقیت ثبت شد.\n"
        "شماره تیکت: {ticket_id}\n\n"
        "تیم پشتیبانی در اسرع وقت به شما پاسخ خواهد داد."
    ),
    'ticket_created_en': (
        "✅ Your message has been received.\n"
        "Ticket #{ticket_id}\n\n"
        "Our support team will respond as soon as possible."
    ),
    'ticket_not_found_fa': "❌ تیکت مورد نظر یافت نشد.",
    'ticket_not_found_en': "❌ Ticket not found.",
    'ticket_details_fa': (
        "🎫 تیکت #{ticket_id}\n\n"
        "📝 موضوع: {subject}\n"
        "📅 تاریخ: {created_at}\n"
        "📊 وضعیت: {status}\n\n"
        "💬 پیام:\n{message}\n\n"
        "{response}"
    ),
    'ticket_details_en': (
        "🎫 Ticket #{ticket_id}\n\n"
        "📝 Subject: {subject}\n"
        "📅 Date: {created_at}\n"
        "📊 Status: {status}\n\n"
        "💬 Message:\n{message}\n\n"
        "{response}"
    ),
    'ticket_response_fa': (
        "📨 پاسخ پشتیبانی:\n"
        "{response}\n"
        "📅 تاریخ پاسخ: {response_date}"
    ),
    'ticket_response_en': (
        "📨 Support Response:\n"
        "{response}\n"
        "📅 Response Date: {response_date}"
    ),
}

def get_message(key: str, language: str = 'en') -> str:
    """Get message by key and language"""
    try:
        return MESSAGES[key][language]
    except KeyError:
        return MESSAGES[key]['en']  # Fallback to English 