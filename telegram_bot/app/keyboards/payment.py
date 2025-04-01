from typing import List, Dict, Any

from telegram import InlineKeyboardButton

# Callback data prefix for payment methods
PAYMENT_METHOD_CALLBACK_PREFIX = "payment_method_"

def generate_payment_method_keyboard(payment_methods: List[Dict[str, Any]]) -> List[List[InlineKeyboardButton]]:
    """
    Generates an inline keyboard for payment method selection.
    
    Args:
        payment_methods: List of payment method objects from the API
        
    Returns:
        List of inline keyboard button rows
    """
    keyboard = []
    
    # If we don't have payment methods, create a fallback
    if not payment_methods:
        # Add a default card-to-card option
        keyboard.append([
            InlineKeyboardButton(
                "💳 کارت به کارت",
                callback_data=f"{PAYMENT_METHOD_CALLBACK_PREFIX}card_to_card"
            )
        ])
        return keyboard
    
    # Process each payment method from the API
    for method in payment_methods:
        method_id = method.get("id") or method.get("code")
        name = method.get("name", "روش پرداخت")
        
        if not method_id:
            continue
            
        # Choose emoji based on payment type
        emoji = "💳"  # Default
        if "card" in str(method_id).lower():
            emoji = "💳"
        elif "online" in str(method_id).lower() or "gateway" in str(method_id).lower():
            emoji = "🔄"
        elif "wallet" in str(method_id).lower():
            emoji = "👛"
        elif "crypto" in str(method_id).lower():
            emoji = "🪙"
            
        button = InlineKeyboardButton(
            f"{emoji} {name}",
            callback_data=f"{PAYMENT_METHOD_CALLBACK_PREFIX}{method_id}"
        )
        
        keyboard.append([button])
    
    # If no valid methods were found, add the fallback
    if not keyboard:
        keyboard.append([
            InlineKeyboardButton(
                "💳 کارت به کارت",
                callback_data=f"{PAYMENT_METHOD_CALLBACK_PREFIX}card_to_card"
            )
        ])
    
    return keyboard 