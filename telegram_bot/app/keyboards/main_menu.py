from telegram import ReplyKeyboardMarkup, KeyboardButton

# Define button labels
BTN_BUY_SERVICE = "🛒 خرید سرویس"
BTN_MY_ACCOUNTS = "📱 اشتراک‌های من"
BTN_WALLET = "👛 کیف پول"
BTN_SUPPORT = "🆘 پشتیبانی"
BTN_REFERRAL = "🔗 معرفی دوستان"
BTN_FREE_TRIAL = "🎁 تست رایگان"
BTN_ABOUT = "ℹ️ درباره ما"

def get_main_menu_keyboard(include_contact_button: bool = False) -> ReplyKeyboardMarkup:
    """
    Generate the main menu keyboard.
    
    Args:
        include_contact_button: Whether to include a contact sharing button
        
    Returns:
        A ReplyKeyboardMarkup for the main menu
    """
    # Define the keyboard layout
    keyboard = [
        [BTN_BUY_SERVICE, BTN_MY_ACCOUNTS],
        [BTN_WALLET, BTN_SUPPORT],
        [BTN_REFERRAL, BTN_ABOUT]
    ]
    
    # Add contact button if requested
    if include_contact_button:
        contact_button = KeyboardButton(text="📞 اشتراک شماره تماس", request_contact=True)
        keyboard.append([contact_button])
    
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=False
    )