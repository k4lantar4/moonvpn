"""
ماژول callbacks - مدیریت پاسخ به دکمه‌های اینلاین
"""

from aiogram import Router
from bot.callbacks.common_callbacks import register_callbacks
from bot.callbacks.wallet_callbacks import register_wallet_callbacks
from bot.callbacks.buy_callbacks import register_buy_callbacks

def setup_callback_handlers(router: Router, session_pool):
    """تنظیم تمام callback handlers روی روتر"""
    register_callbacks(router, session_pool)
    register_wallet_callbacks(router, session_pool)
    register_buy_callbacks(router, session_pool)

"""
Callback handler exports
"""

from .buy_callbacks import register_buy_callbacks
from .wallet_callbacks import register_wallet_callbacks
from .admin_callbacks import register_admin_callbacks
from .common_callbacks import register_callbacks
from .plan_callbacks import register_plan_callbacks
from bot.callbacks.panel_callbacks import register_panel_callbacks
from bot.callbacks.inbound_callbacks import register_inbound_callbacks
from .account_callbacks import register_account_callbacks

__all__ = [
    "register_buy_callbacks",
    "register_wallet_callbacks",
    "register_admin_callbacks",
    "register_callbacks",
    "register_plan_callbacks",
    "register_panel_callbacks",
    "register_inbound_callbacks",
    "register_account_callbacks"
]
