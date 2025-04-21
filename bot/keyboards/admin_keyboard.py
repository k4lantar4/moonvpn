"""
Admin panel keyboard layouts
"""

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_admin_panel_keyboard() -> InlineKeyboardMarkup:
    """Generate inline keyboard for admin panel"""
    kb = InlineKeyboardBuilder()
    
    # Admin panel buttons
    kb.button(text="📊 Statistics", callback_data="admin_stats")
    kb.button(text="🔄 Sync Panels", callback_data="sync_panels")
    kb.button(text="👥 Users", callback_data="admin_users")
    kb.button(text="💰 Plans", callback_data="admin_plans")
    kb.button(text="⚙️ Settings", callback_data="admin_settings")
    kb.button(text="🔙 Back", callback_data="start")
    
    # Adjust layout - 2 buttons per row
    kb.adjust(2)
    
    return kb.as_markup() 