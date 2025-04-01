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
from app.handlers.start import handle_start, handle_contact
from app.handlers.main_menu import handle_buy_service, handle_wallet
from app.keyboards.main_menu import BTN_BUY_SERVICE, BTN_WALLET
from app.handlers.admin_handlers import admin_command_handler
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

    # --- Register Handlers ---
    # Register the start command handler
    application.add_handler(CommandHandler("start", handle_start))

    # Register the contact handler (triggered when user shares contact)
    # Note: We are not using ConversationHandler yet for simplicity.
    # If complex flows are needed later, ConversationHandler is recommended.
    application.add_handler(MessageHandler(filters.CONTACT, handle_contact))

    # Register handler for the 'Buy Service' button
    # This uses a MessageHandler filtering on the exact button text
    application.add_handler(MessageHandler(filters.Text([BTN_BUY_SERVICE]), handle_buy_service))

    # Register admin handler
    application.add_handler(admin_command_handler)

    # >>> REGISTER WALLET HANDLER
    application.add_handler(MessageHandler(filters.Text([BTN_WALLET]), handle_wallet))

    # Add other handlers here (CallbackQueryHandler, MessageHandler for text, etc.)

    # Register the error handler
    application.add_error_handler(error_handler)

    # Start the Bot
    logger.info("🚀 Starting MoonVPN Telegram Bot...")
    application.run_polling()


if __name__ == "__main__":
    # Consider using asyncio.run(main()) if you have async setup needs before run_polling
    main()
