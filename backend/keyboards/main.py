from telegram import ReplyKeyboardMarkup

def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Get main menu keyboard."""
    keyboard = [
        ['🛒 خرید اکانت', '👤 حساب کاربری'],
        ['💰 شارژ کیف پول', '📊 وضعیت سرویس'],
        ['🎫 پشتیبانی', '📝 راهنما']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True) 