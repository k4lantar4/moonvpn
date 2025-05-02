"""
وضعیت‌های FSM مربوط به بخش کیف پول
"""

from aiogram.fsm.state import State, StatesGroup

class WalletStates(StatesGroup):
    """حالت‌های مربوط به فرآیند شارژ کیف پول"""
    waiting_for_amount = State() # منتظر ورود مبلغ توسط کاربر
    # TODO: Add other states if needed, e.g., waiting_for_receipt 