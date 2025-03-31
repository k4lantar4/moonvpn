import logging
import asyncio

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from app.core.config import TELEGRAM_BOT_TOKEN
# Import handlers later
# from app.handlers import start_handler, ...

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log Errors caused by Updates."""
    logger.error("Exception while handling an update:", exc_info=context.error)


def main() -> None:
    """Start the bot."""
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error("Telegram Bot Token not found. Exiting.")
        return

    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # --- Register Handlers ---
    # application.add_handler(CommandHandler("start", start_handler))
    # Add other handlers here (CallbackQueryHandler, MessageHandler, etc.)

    # Register the error handler
    application.add_error_handler(error_handler)

    # Start the Bot
    logger.info("Starting MoonVPN Telegram Bot...")
    application.run_polling()


if __name__ == "__main__":
    # Consider using asyncio.run(main()) if you have async setup needs before run_polling
    main()
