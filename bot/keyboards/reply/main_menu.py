from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_menu_keyboard(role: str = 'USER') -> ReplyKeyboardMarkup:
    """
    Creates the main menu keyboard based on user role.
    
    Args:
        role (str): User role ('USER', 'ADMIN', etc.)
        
    Returns:
        ReplyKeyboardMarkup: The appropriate keyboard for the user role
    """
    if role == 'ADMIN':
        # Admin keyboard with additional options
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text="🛒 خرید پلن"),
                    KeyboardButton(text="👤 حساب کاربری")
                ],
                [
                    KeyboardButton(text="💰 کیف پول"),
                    KeyboardButton(text="🆘 پشتیبانی")
                ],
                [
                    KeyboardButton(text="⚙️ پنل مدیریت")
                ]
            ],
            resize_keyboard=True,
            input_field_placeholder="یک گزینه انتخاب کنید..."
        )
    else:
        # Regular user keyboard
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text="🛒 خرید پلن"),
                    KeyboardButton(text="👤 حساب کاربری")
                ],
                [
                    KeyboardButton(text="💰 کیف پول"),
                    KeyboardButton(text="🆘 پشتیبانی")
                ]
            ],
            resize_keyboard=True,
            input_field_placeholder="یک گزینه انتخاب کنید..."
        )
    
    return keyboard

def get_back_button() -> ReplyKeyboardMarkup:
    """Creates a keyboard with just a back button"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔙 بازگشت")]
        ],
        resize_keyboard=True
    ) 