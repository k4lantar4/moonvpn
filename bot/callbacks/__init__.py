"""
ماژول callbacks - مدیریت پاسخ به دکمه‌های اینلاین
"""

from aiogram import Router
from bot.callbacks.common import register_callbacks
from bot.callbacks.wallet_callbacks import register_wallet_callbacks
from bot.callbacks.buy_callbacks import register_buy_callbacks

def setup_callback_handlers(router: Router, session_pool):
    """تنظیم تمام callback handlers روی روتر"""
    register_callbacks(router, session_pool)
    register_wallet_callbacks(router, session_pool)
    register_buy_callbacks(router, session_pool)
