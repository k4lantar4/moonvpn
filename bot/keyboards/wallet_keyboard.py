"""
Wallet management keyboard layouts
"""

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_wallet_keyboard() -> InlineKeyboardMarkup:
    """Generate inline keyboard for wallet menu"""
    kb = InlineKeyboardBuilder()
    
    # Add wallet operation buttons
    kb.button(text="💰 Top Up", callback_data="top_up")
    kb.button(text="💸 Withdraw", callback_data="withdraw")
    kb.button(text="📊 Transaction History", callback_data="transactions")
    kb.button(text="🔙 Back", callback_data="start")
    
    # Adjust layout - 2 buttons per row
    kb.adjust(2)
    
    return kb.as_markup()

def get_withdrawal_keyboard() -> InlineKeyboardMarkup:
    """Generate inline keyboard for withdrawal methods"""
    kb = InlineKeyboardBuilder()
    
    # Add withdrawal method buttons
    kb.button(text="🏦 Bank Transfer", callback_data="withdraw_bank")
    kb.button(text="💳 Crypto", callback_data="withdraw_crypto")
    kb.button(text="🔙 Back to Wallet", callback_data="wallet_menu")
    
    # Adjust layout - 1 button per row
    kb.adjust(1)
    
    return kb.as_markup() 