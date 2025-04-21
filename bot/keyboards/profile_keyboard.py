"""
Profile command keyboard layouts
"""

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_profile_keyboard() -> InlineKeyboardMarkup:
    """Generate inline keyboard for profile command"""
    kb = InlineKeyboardBuilder()
    
    # Add profile-related buttons
    kb.button(text="🔄 Refresh", callback_data="refresh_profile")
    kb.button(text="⚙️ Settings", callback_data="profile_settings")
    kb.button(text="📊 Account Details", callback_data="account_details")
    kb.button(text="💳 Wallet", callback_data="wallet_menu")
    
    # Adjust layout - 2 buttons per row
    kb.adjust(2)
    
    return kb.as_markup() 