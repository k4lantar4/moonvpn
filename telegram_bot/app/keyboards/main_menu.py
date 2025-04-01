from telegram import KeyboardButton, ReplyKeyboardMarkup

# Define button texts (using constants for easier maintenance/translation)
BTN_BUY_SERVICE = "🛍 خرید سرویس"
BTN_MY_ACCOUNT = "👤 حساب کاربری من"
BTN_WALLET = "💳 کیف پول"
BTN_SUPPORT = "💬 پشتیبانی"
BTN_REFERRAL = "🔗 معرفی دوستان" # Affiliate/Referral
BTN_FREE_TRIAL = "🎁 تست رایگان" # Or integrate into Buy Service?


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Creates the main menu ReplyKeyboardMarkup."""
    keyboard = [
        [KeyboardButton(BTN_BUY_SERVICE)],
        [KeyboardButton(BTN_MY_ACCOUNT), KeyboardButton(BTN_WALLET)],
        # [KeyboardButton(BTN_FREE_TRIAL)], # Decide if Free Trial is separate button
        [KeyboardButton(BTN_REFERRAL), KeyboardButton(BTN_SUPPORT)],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False) # one_time=False keeps menu open 