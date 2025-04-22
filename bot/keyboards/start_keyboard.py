"""
Start command inline keyboard layouts.

This module provides keyboard layouts for the start command,
with different buttons based on user roles.
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_start_keyboard(role: str) -> InlineKeyboardMarkup:
    """Generate inline keyboard based on user role.
    
    Args:
        role: User role (user, admin, superadmin, seller)
        
    Returns:
        InlineKeyboardMarkup with appropriate buttons
    """
    kb = InlineKeyboardBuilder()
    
    # Common buttons for all users
    kb.button(text="🛒 خرید سرویس", callback_data="buy_plans")
    kb.button(text="💳 کیف پول", callback_data="wallet_menu")
    kb.button(text="📊 اشتراک‌های من", callback_data="my_accounts")
    kb.button(text="❓ راهنما", callback_data="help_menu")
    kb.button(text="💬 پشتیبانی", callback_data="support_chat")
    
    # Admin-specific buttons
    if role in ["admin", "superadmin"]:
        kb.button(text="⚙️ پنل مدیریت", callback_data="admin_panel")
        kb.button(text="📈 آمار و گزارشات", callback_data="admin_stats")
        kb.button(text="🔄 همگام‌سازی پنل‌ها", callback_data="sync_panels")
        kb.button(text="👥 کاربران", callback_data="admin_users")
        kb.button(text="💰 تراکنش‌ها", callback_data="admin_transactions")
    
    # Seller-specific buttons
    if role == "seller":
        kb.button(text="💼 فروش‌های من", callback_data="seller_sales")
        kb.button(text="🎯 پلن‌های من", callback_data="seller_plans")
        kb.button(text="👥 مشتریان من", callback_data="seller_customers")
        kb.button(text="💰 درآمد من", callback_data="seller_earnings")
    
    # Adjust layout - 2 buttons per row
    kb.adjust(2)
    
    return kb.as_markup() 