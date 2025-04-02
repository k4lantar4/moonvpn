from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def build_main_menu_markup() -> InlineKeyboardMarkup:
    """
    Build the main menu keyboard for the bot.
    """
    keyboard = [
        [
            InlineKeyboardButton("🔐 My Profile", callback_data="profile"),
            InlineKeyboardButton("📜 My Subscriptions", callback_data="subscriptions")
        ],
        [
            InlineKeyboardButton("🛒 Order VPN", callback_data="order"),
            InlineKeyboardButton("💰 Payment", callback_data="payment")
        ],
        [
            InlineKeyboardButton("🏆 Become a Seller", callback_data="seller"),
            InlineKeyboardButton("🔗 Affiliate Program", callback_data="affiliate")
        ],
        [
            InlineKeyboardButton("ℹ️ Help", callback_data="help"),
            InlineKeyboardButton("📞 Support", url="https://t.me/MoonVPNsupport")
        ]
    ]
    return InlineKeyboardMarkup(keyboard) 