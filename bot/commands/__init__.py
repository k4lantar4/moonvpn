"""
ماژول دستورات تلگرام - مدیریت دستورات مختلف ربات
"""

# مدیریت import های مربوط به دستورات ربات
from .start import register_start_command
from .plans import register_plans_command
from .admin import register_admin_commands
from .wallet import register_wallet_command
from .buy import register_buy_command
