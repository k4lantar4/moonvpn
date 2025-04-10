"""User handlers."""

from bot.handlers.user.main import register_user_handlers
from bot.handlers.user.wallet import register_wallet_handlers
from bot.handlers.user.payment import register_payment_handlers

# Import other user handlers as needed

def register_all_user_handlers(dp):
    """Register all user handlers."""
    register_user_handlers(dp)
    register_wallet_handlers(dp)
    register_payment_handlers(dp)
    # Register other user handlers as needed
