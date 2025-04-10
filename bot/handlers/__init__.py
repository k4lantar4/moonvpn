"""Register routers here."""

from bot.handlers.common import common_router
from bot.handlers.admin import register_all_admin_handlers
from bot.handlers.user import register_all_user_handlers

def register_all_handlers(dp):
    """Register all router groups."""
    # Include common router
    dp.include_router(common_router)
    
    # Register admin handlers
    register_all_admin_handlers(dp)
    
    # Register user handlers
    register_all_user_handlers(dp)
    
    # Add more router group registrations if needed
