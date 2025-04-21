"""
ماژول دستورات تلگرام - مدیریت دستورات مختلف ربات
"""

# مدیریت import های مربوط به دستورات ربات
from .start import router as start_router
from .plans import register_plans_command
from .admin import register_admin_commands
from .wallet import register_wallet_command
from .buy import register_buy_command
from .profile import register_profile_command

__all__ = [
    "start_router",
    "register_buy_command",
    "register_admin_commands",
    "register_wallet_command",
    "register_plans_command",
    "register_profile_command"
]
