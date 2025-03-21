from typing import List, Optional, Dict, Any
from telegram import Update, CallbackQuery, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from .base import BaseHandler
from ...models import User

class MenuHandler(BaseHandler):
    """Base class for menu handlers"""
    
    MENU_TYPE = "base"  # Override in subclasses
    
    @classmethod
    async def show_menu(
        cls,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        user: User
    ) -> None:
        """Show menu - implement in subclasses"""
        raise NotImplementedError
    
    @classmethod
    async def handle_callback(
        cls,
        query: CallbackQuery,
        context: ContextTypes.DEFAULT_TYPE,
        user: User,
        data: List[str]
    ) -> None:
        """Handle menu callbacks - implement in subclasses"""
        raise NotImplementedError
    
    @staticmethod
    async def update_menu(
        query: CallbackQuery,
        text: str,
        keyboard: Optional[InlineKeyboardMarkup] = None
    ) -> None:
        """Update menu message"""
        try:
            await query.edit_message_text(
                text=text,
                reply_markup=keyboard
            )
        except Exception as e:
            # Handle message not modified error silently
            pass
    
    @staticmethod
    def get_callback_data(*args: str) -> str:
        """Generate callback data string"""
        return ":".join(str(arg) for arg in args)
    
    @staticmethod
    def parse_callback_data(data: str) -> List[str]:
        """Parse callback data string"""
        return data.split(":") 