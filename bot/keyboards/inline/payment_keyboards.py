from typing import List, Dict, Any, Optional
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from .common_keyboards import get_back_button

def get_payment_methods_keyboard(wallet_sufficient: bool, back_callback: str = "purchase_plan") -> InlineKeyboardMarkup:
    """
    Get keyboard for payment methods.

    Args:
        wallet_sufficient: Whether user has enough balance in wallet.
        back_callback: Callback data for the back button.

    Returns:
        InlineKeyboardMarkup: Keyboard with payment method buttons
    """
    builder = InlineKeyboardBuilder()

    if wallet_sufficient:
        builder.button(text="💰 پرداخت از کیف پول", callback_data="pay_wallet")
    else:
        # Optionally disable or don't show wallet payment if insufficient
        builder.button(text="钱包余额不足", callback_data="pay_wallet_insufficient") # Example: Notify user

    builder.button(text="💳 پرداخت کارت به کارت", callback_data="pay_card")
    # Add other methods like Zarinpal if implemented
    # builder.button(text="🟠 پرداخت زرین پال", callback_data="pay_zarinpal")

    builder.row(get_back_button(callback_data=back_callback))
    builder.adjust(1)
    return builder.as_markup()

def get_card_selection_keyboard(cards: List[Dict[str, Any]], back_callback: str) -> InlineKeyboardMarkup:
    """
    Get keyboard for selecting a bank card for card-to-card payment.

    Args:
        cards: List of available bank card dictionaries.
        back_callback: Callback data for the back button.

    Returns:
        InlineKeyboardMarkup: Keyboard with bank card buttons.
    """
    builder = InlineKeyboardBuilder()
    for card in cards:
        card_id = card.get("id")
        bank_name = card.get("bank_name", "Unknown")
        # Mask card number for display
        card_number_display = card.get("card_number", "")
        if len(card_number_display) > 8:
            card_number_display = f"{card_number_display[:4]}...{card_number_display[-4:]}"

        builder.button(
            text=f"💳 {bank_name} - {card_number_display}",
            callback_data=f"select_card_{card_id}"
        )

    builder.row(get_back_button(callback_data=back_callback))
    builder.adjust(1)
    return builder.as_markup()

def get_payment_verification_keyboard(payment_id: int) -> InlineKeyboardMarkup:
    """
    Keyboard for admins to verify or reject a card-to-card payment.

    Args:
        payment_id: The ID of the payment record.

    Returns:
        InlineKeyboardMarkup: Verification keyboard.
    """
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ تایید پرداخت", callback_data=f"verify_payment_{payment_id}")
    builder.button(text="❌ رد پرداخت", callback_data=f"reject_payment_{payment_id}")
    builder.adjust(2)
    return builder.as_markup() 