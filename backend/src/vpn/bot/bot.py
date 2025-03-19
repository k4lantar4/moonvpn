import logging
from typing import Optional, Dict, Any
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
from django.conf import settings
from django.utils import timezone
from ..models import User
from ..services.user_manager import UserManager
from .handlers import (
    PlansHandler,
    ProfileHandler,
    WalletHandler,
    SupportHandler,
    SettingsHandler,
    AdminHandler,
    ResellerHandler
)
from .keyboards import get_main_menu_keyboard
from .constants import get_message

logger = logging.getLogger(__name__)

class MoonVPNBot:
    """Main bot class for MoonVPN Telegram bot"""
    
    def __init__(self):
        """Initialize bot"""
        self.application = Application.builder().token(
            settings.TELEGRAM_BOT_TOKEN
        ).build()
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Set up bot command and message handlers"""
        # Basic commands
        self.application.add_handler(CommandHandler("start", self.start))
        
        # Menu commands
        self.application.add_handler(CommandHandler(
            "plans", PlansHandler.show_menu
        ))
        self.application.add_handler(CommandHandler(
            "profile", ProfileHandler.show_menu
        ))
        self.application.add_handler(CommandHandler(
            "wallet", WalletHandler.show_menu
        ))
        self.application.add_handler(CommandHandler(
            "support", SupportHandler.show_menu
        ))
        self.application.add_handler(CommandHandler(
            "settings", SettingsHandler.show_menu
        ))
        
        # Admin/Reseller commands
        self.application.add_handler(CommandHandler(
            "admin",
            lambda u, c: AdminHandler.show_menu(u, c, require_admin=True)
        ))
        self.application.add_handler(CommandHandler(
            "reseller",
            lambda u, c: ResellerHandler.show_menu(u, c, require_reseller=True)
        ))
        
        # Callback queries
        self.application.add_handler(
            CallbackQueryHandler(self.handle_callback)
        )
        
        # Message handler
        self.application.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                self.handle_message
            )
        )
        
        # Error handler
        self.application.add_error_handler(self.error_handler)
    
    async def start(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /start command"""
        if not update.effective_user:
            return
            
        # Get or create user
        try:
            user = await self.get_or_create_user(update.effective_user)
            if not user:
                await update.message.reply_text(
                    get_message('general_error', 'en')
                )
                return
                
            # Process referral code if provided
            if context.args and len(context.args[0]) == 8:
                referral_code = context.args[0]
                success, error = UserManager.process_referral(
                    user=user,
                    referral_code=referral_code
                )
                if success:
                    await update.message.reply_text(
                        get_message('referral_success', user.language)
                    )
            
            # Send welcome message
            keyboard = get_main_menu_keyboard(user.language)
            await update.message.reply_text(
                get_message('start', user.language),
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Error in start command: {str(e)}")
            await update.message.reply_text(
                get_message('general_error', 'en')
            )
    
    async def handle_callback(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle callback queries"""
        if not update.callback_query or not update.effective_user:
            return
            
        query = update.callback_query
        user = await self.get_user(update.effective_user.id)
        if not user:
            await query.answer(
                get_message('create_account_first', 'en')
            )
            return
        
        # Parse callback data
        try:
            data = query.data.split(':')
            handler_type = data[0]
            
            # Route to appropriate handler
            if handler_type == PlansHandler.MENU_TYPE:
                await PlansHandler.handle_callback(query, context, user, data)
            elif handler_type == ProfileHandler.MENU_TYPE:
                await ProfileHandler.handle_callback(query, context, user, data)
            elif handler_type == WalletHandler.MENU_TYPE:
                await WalletHandler.handle_callback(query, context, user, data)
            elif handler_type == SettingsHandler.MENU_TYPE:
                await SettingsHandler.handle_callback(query, context, user, data)
            elif handler_type == AdminHandler.MENU_TYPE:
                if user.is_admin:
                    await AdminHandler.handle_callback(query, context, user, data)
                else:
                    await query.answer(
                        get_message('no_permission', user.language)
                    )
            elif handler_type == ResellerHandler.MENU_TYPE:
                if user.is_reseller:
                    await ResellerHandler.handle_callback(query, context, user, data)
                else:
                    await query.answer(
                        get_message('no_permission', user.language)
                    )
            else:
                await query.answer(
                    get_message('invalid_action', user.language)
                )
                
        except Exception as e:
            logger.error(f"Error handling callback: {str(e)}")
            await query.answer(
                get_message('general_error', user.language)
            )
    
    async def handle_message(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle text messages"""
        if not update.effective_user or not update.message:
            return
            
        user = await self.get_user(update.effective_user.id)
        if not user:
            await update.message.reply_text(
                get_message('create_account_first', 'en')
            )
            return
        
        # Handle support messages
        if context.user_data.get('awaiting_support'):
            await SupportHandler.handle_message(update, context, user)
            return
            
        # Handle wallet deposit messages
        if context.user_data.get('awaiting_deposit_amount'):
            await WalletHandler.handle_deposit_message(update, context, user)
            return
        
        # Handle other messages
        await update.message.reply_text(
            get_message('unknown_command', user.language)
        )
    
    async def error_handler(
        self,
        update: object,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle errors"""
        logger.error(
            f"Exception while handling an update:",
            exc_info=context.error
        )
        
        if isinstance(update, Update) and update.effective_message:
            await update.effective_message.reply_text(
                get_message('general_error', 'en')
            )
    
    @staticmethod
    async def get_user(telegram_id: int) -> Optional[User]:
        """Get user by Telegram ID"""
        try:
            return User.objects.get(telegram_id=str(telegram_id))
        except User.DoesNotExist:
            return None
    
    @staticmethod
    async def get_or_create_user(
        telegram_user: Any
    ) -> Optional[User]:
        """Get or create user from Telegram user object"""
        try:
            # Try to get existing user
            user = await MoonVPNBot.get_user(telegram_user.id)
            if user:
                return user
            
            # Create new user
            username = (
                telegram_user.username or
                f"user_{telegram_user.id}"
            )
            
            user, error = UserManager.create_user(
                username=username,
                password=None,  # No password for Telegram users
                telegram_id=str(telegram_user.id),
                language=telegram_user.language_code or 'en'
            )
            
            if error:
                logger.error(f"Error creating user: {error}")
                return None
                
            return user
            
        except Exception as e:
            logger.error(f"Error getting/creating user: {str(e)}")
            return None
    
    def run(self):
        """Start the bot"""
        self.application.run_polling() 