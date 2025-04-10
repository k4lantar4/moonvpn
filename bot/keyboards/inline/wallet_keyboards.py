from typing import List, Dict, Any
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from .common_keyboards import get_back_button

def get_wallet_keyboard(balance: float) -> InlineKeyboardMarkup:
    """
    Keyboard for the wallet section, showing balance and actions.

    Args:
        balance: User's current wallet balance.

    Returns:
        InlineKeyboardMarkup: Wallet keyboard.
    """
    builder = InlineKeyboardBuilder()

    # Display balance (maybe not as a button, but text above keyboard)
    # builder.button(text=f"موجودی: {balance:,.0f} تومان", callback_data="wallet_balance_info")

    builder.button(text="💳 افزایش موجودی (کارت به کارت)", callback_data="deposit_card")
    # builder.button(text="🟠 افزایش موجودی (زرین پال)", callback_data="deposit_zarinpal")
    builder.button(text="📜 تاریخچه تراکنش ها (بزودی)", callback_data="wallet_history_soon")

    builder.row(get_back_button(callback_data="main_menu"))
    builder.adjust(1)
    return builder.as_markup()

def get_deposit_amounts_keyboard(amounts: List[int], back_callback: str = "wallet") -> InlineKeyboardMarkup:
    """
    Keyboard for selecting predefined deposit amounts.

    Args:
        amounts: List of predefined amounts (e.g., [50000, 100000, 200000]).
        back_callback: Callback data for the back button.

    Returns:
        InlineKeyboardMarkup: Deposit amount selection keyboard.
    """
    builder = InlineKeyboardBuilder()

    for amount in amounts:
        builder.button(
            text=f"{amount:,.0f} تومان",
            callback_data=f"deposit_amount_{amount}"
        )

    builder.button(text="💰 مبلغ دلخواه", callback_data="deposit_custom_amount")
    builder.row(get_back_button(callback_data=back_callback))
    builder.adjust(2) # Adjust layout
    return builder.as_markup() 