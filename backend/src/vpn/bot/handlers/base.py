from typing import List, Optional, Any
from telegram import Update, CallbackQuery
from telegram.ext import ContextTypes
from ...models import User

class BaseHandler:
    """Base class for all handlers"""
    
    @staticmethod
    async def get_user(update: Update) -> Optional[User]:
        """Get user from update"""
        if not update.effective_user:
            return None
            
        try:
            return User.objects.get(telegram_id=str(update.effective_user.id))
        except User.DoesNotExist:
            return None
    
    @staticmethod
    async def validate_user(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        require_admin: bool = False,
        require_reseller: bool = False
    ) -> Optional[User]:
        """Validate user and permissions"""
        user = await BaseHandler.get_user(update)
        
        if not user:
            if update.effective_message:
                await update.effective_message.reply_text(
                    "Please use /start to create an account first."
                )
            return None
            
        if require_admin and not user.is_admin:
            if update.effective_message:
                await update.effective_message.reply_text(
                    "You don't have permission to use this command."
                )
            return None
            
        if require_reseller and not user.is_reseller:
            if update.effective_message:
                await update.effective_message.reply_text(
                    "You don't have permission to use this command."
                )
            return None
            
        return user
    
    @staticmethod
    async def send_error(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        error: str,
        language: str = 'en'
    ) -> None:
        """Send error message"""
        if not update.effective_message:
            return
            
        await update.effective_message.reply_text(
            error if language == 'en' else error  # Add Persian translation
        )
    
    @staticmethod
    async def answer_callback_error(
        query: CallbackQuery,
        error: str,
        language: str = 'en'
    ) -> None:
        """Answer callback query with error"""
        await query.answer(
            error if language == 'en' else error  # Add Persian translation
        ) 