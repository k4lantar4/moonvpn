from typing import List, Dict, Any

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup

# Callback data prefix for payment methods
PAYMENT_METHOD_PREFIX = "payment_method_"

# Assuming PaymentMethod enum is available here (e.g., copied or shared)
from app.models.order import PaymentMethod 

# Callback data patterns
PAYMENT_METHOD_CALLBACK_PREFIX = "payment_method_"

def generate_payment_method_keyboard(payment_methods: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """
    Generate a keyboard with available payment methods.
    
    Args:
        payment_methods: List of payment method dictionaries from API
        Each dictionary should have 'method' and 'active' keys
        
    Returns:
        Keyboard markup with payment method buttons
    """
    keyboard = []
    row = []

    # Map method values to button text
    method_label_map = {
        PaymentMethod.CARD_TO_CARD.value: "💳 کارت به کارت",
        PaymentMethod.WALLET.value: "💰 کیف پول",
        PaymentMethod.ZARINPAL.value: "🌐 پرداخت آنلاین (زرین‌پال)",
        PaymentMethod.CRYPTO.value: "💎 ارز دیجیتال",
        PaymentMethod.MANUAL.value: "👨‍💻 پرداخت دستی",
    }

    # Define the desired order of buttons
    display_order = [
        PaymentMethod.ZARINPAL.value, 
        PaymentMethod.CARD_TO_CARD.value,
        PaymentMethod.WALLET.value, 
        PaymentMethod.CRYPTO.value,
        PaymentMethod.MANUAL.value,
    ]

    # Convert list of payment method dicts to a simple dict for easier lookup
    active_methods = {item["method"]: item for item in payment_methods if item.get("active", False)}

    # Build keyboard based on display order and active methods
    for method_value in display_order:
        if method_value in active_methods:
            text = method_label_map.get(method_value, f"پرداخت {method_value}")
            callback_data = PAYMENT_METHOD_CALLBACK_PREFIX + method_value
            button = InlineKeyboardButton(text, callback_data=callback_data)
            
            # Add button to row, create new row if necessary (max 1 button per row for better UX)
            row.append(button)
            keyboard.append(row)
            row = []

    return InlineKeyboardMarkup(keyboard)

def get_cancel_keyboard():
    """Return a simple cancel keyboard."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ انصراف", callback_data="cancel_payment")]
    ]) 