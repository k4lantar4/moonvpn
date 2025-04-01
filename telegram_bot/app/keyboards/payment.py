from typing import List, Dict, Any

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup

# Callback data prefix for payment methods
PAYMENT_METHOD_PREFIX = "payment_method_"

def generate_payment_method_keyboard(payment_methods: List[Dict[str, Any]]) -> List[List[InlineKeyboardButton]]:
    """
    Generate a keyboard with available payment methods.
    
    Args:
        payment_methods: List of payment method dictionaries from API
        
    Returns:
        List of lists of InlineKeyboardButton
    """
    keyboard = []
    
    # Add buttons for each payment method
    for method in payment_methods:
        method_id = method.get("id") or method.get("key")
        method_name = method.get("name") or method.get("display_name")
        
        # Special case for card to card payment
        if method_id == "card_to_card":
            callback_data = f"{PAYMENT_METHOD_PREFIX}card_to_card"
            button_text = "💳 پرداخت کارت به کارت"
        elif method_id == "crypto":
            callback_data = f"{PAYMENT_METHOD_PREFIX}crypto"
            button_text = "🪙 پرداخت با ارز دیجیتال"
        else:
            callback_data = f"{PAYMENT_METHOD_PREFIX}{method_id}"
            button_text = f"{method_name}"
        
        keyboard.append([
            InlineKeyboardButton(button_text, callback_data=callback_data)
        ])
    
    # Add cancel button
    keyboard.append([
        InlineKeyboardButton("❌ انصراف", callback_data="cancel_payment")
    ])
    
    return InlineKeyboardMarkup(keyboard)

def get_cancel_keyboard():
    """Return a simple cancel keyboard."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ انصراف", callback_data="cancel_payment")]
    ]) 