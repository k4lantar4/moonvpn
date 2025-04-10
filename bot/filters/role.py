"""Custom filters for checking user roles."""

import logging
from typing import Union, Dict, Any
from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery

from core.config import settings # To get ADMIN_IDS

logger = logging.getLogger(__name__)

class IsAdminFilter(BaseFilter):
    """Checks if the user triggering the event is in the ADMIN_IDS list."""
    is_admin: bool = True

    async def __call__(self, event: Union[Message, CallbackQuery], event_from_user: Any) -> bool:
        """Execute the filter check."""
        if not event_from_user:
            # Should not happen with Message/CallbackQuery, but defensively check
            logger.warning("IsAdminFilter received event without 'from_user'.")
            return False
            
        user_id = event_from_user.id
        
        # Parse ADMIN_IDS from settings
        try:
            admin_ids_list = {int(admin_id.strip()) for admin_id in settings.ADMIN_IDS.split(',') if admin_id.strip()}
        except Exception as e:
            logger.error(f"Failed to parse ADMIN_IDS from settings ('{settings.ADMIN_IDS}'): {e}", exc_info=True)
            admin_ids_list = set()

        is_user_admin = user_id in admin_ids_list
        logger.debug(f"IsAdminFilter check for user {user_id}: {is_user_admin} (Required: {self.is_admin})")

        # Return True if the user's admin status matches the required status
        return is_user_admin == self.is_admin

# Example Usage in handlers:
# from .role import IsAdminFilter
#
# @router.message(Command("adminonly"), IsAdminFilter(is_admin=True))
# async def handle_admin_command(message: Message):
#     ...
#
# @router.message(Command("normalusers"), IsAdminFilter(is_admin=False))
# async def handle_non_admin_command(message: Message):
#     ... 