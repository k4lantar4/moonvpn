import logging
import asyncio
import os # Added for path joining

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# Load .env file from the parent directory of 'app' (telegram_bot directory)
# This ensures it works correctly when main.py is run from the app directory or telegram_bot directory
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path=dotenv_path)

from app.core.config import TELEGRAM_BOT_TOKEN
# --- Import Handlers ---
from app.handlers import (
    start_handler, main_menu_handler, admin_command_handler, 
    admin_card_handler, get_buy_flow_handlers, get_my_accounts_handlers, get_payment_handlers
)
from app.handlers.error import error_handler
from app.handlers.payment_notification_handlers import get_payment_notification_handlers
from app.handlers.payment_proof_handlers import get_payment_proof_handlers
from app.handlers.payment_verification_handlers import get_payment_verification_handlers
from app.handlers.admin_report_handlers import get_admin_report_handlers
from app.handlers.payment_admin_handlers import get_payment_admin_handlers, register_payment_admin_handlers
# Import other handlers later

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# Set higher logging level for httpx to avoid verbose output
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log Errors caused by Updates."""
    logger.error("Exception while handling an update:", exc_info=context.error)

def main() -> None:
    """Start the bot."""
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error("⛔️ ERROR: Telegram Bot Token not found. Make sure it's set in the .env file.")
        print("⛔️ ERROR: Telegram Bot Token not found. Make sure it's set in the .env file in the 'telegram_bot' directory.") # Added print for visibility
        return

    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Register handlers
    application.add_handler(start_handler)
    application.add_handler(main_menu_handler)
    application.add_handler(admin_command_handler)
    application.add_handler(admin_card_handler)

    # Register flow handlers
    for handler in get_buy_flow_handlers():
        application.add_handler(handler)

    # Register my accounts handlers
    for handler in get_my_accounts_handlers():
        application.add_handler(handler)
        
    # Register payment proof handlers
    for handler in get_payment_proof_handlers():
        application.add_handler(handler)
        
    # Register payment verification handlers
    for handler in get_payment_verification_handlers():
        application.add_handler(handler)
        
    # Register payment notification handlers
    for handler in get_payment_notification_handlers():
        application.add_handler(handler)

    # Register admin report handlers
    for handler in get_admin_report_handlers():
        application.add_handler(handler)
        
    # Register payment admin handlers
    register_payment_admin_handlers(application)
    for handler in get_payment_admin_handlers():
        application.add_handler(handler)

    # Register the error handler
    application.add_error_handler(error_handler)

    # Start the Bot
    logger.info("🚀 Starting MoonVPN Telegram Bot...")
    application.run_polling()


if __name__ == "__main__":
    # Consider using asyncio.run(main()) if you have async setup needs before run_polling
    main()
