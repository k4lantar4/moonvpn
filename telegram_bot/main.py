import logging
import os
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler

from config import TELEGRAM_BOT_TOKEN, initialize_config
from handlers.start_handler import start
from handlers.auth_handler import get_auth_conversation_handler
from handlers.profile_handler import get_profile_conversation_handler
from handlers.subscription_handler import get_subscription_conversation_handler
from handlers.order_handler import get_order_conversation_handler
from handlers.plan_handler import get_plan_conversation_handler
from handlers.seller_handler import get_seller_conversation_handler
from handlers.affiliate_handler import get_affiliate_conversation_handler
from handlers.help_handler import help_command
from handlers.callback_handler import handle_callback
from handlers.payment_handler import get_payment_conversation_handler

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)


def main():
    # Initialize configuration
    initialize_config()
    
    # Create the Application and pass it your bot's token
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Add conversation handlers
    application.add_handler(get_auth_conversation_handler())
    application.add_handler(get_profile_conversation_handler())
    application.add_handler(get_subscription_conversation_handler())
    application.add_handler(get_order_conversation_handler())
    application.add_handler(get_plan_conversation_handler())
    application.add_handler(get_payment_conversation_handler())
    application.add_handler(get_seller_conversation_handler())
    application.add_handler(get_affiliate_conversation_handler())
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    
    # Add callback query handler for inline buttons
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    # Start the Bot
    application.run_polling()
    
    logger.info("Bot started")


if __name__ == '__main__':
    main() 