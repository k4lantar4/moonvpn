import logging
import asyncio
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from core.config import get_settings
from core.logging import setup_logging
from bot.handlers.language import setup_handlers as setup_language_handlers

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

settings = get_settings()

# --- Command Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcome message when the /start command is issued.
    Also displays a simple reply keyboard.
    """
    user = update.effective_user
    logger.info(f"User {user.id} ({user.username}) started the bot.")

    # Simple Reply Keyboard
    keyboard = [
        [KeyboardButton("🚀 نمایش سرویس‌ها"), KeyboardButton("💼 حساب کاربری من")],
        [KeyboardButton("💰 کیف پول"), KeyboardButton("🧑‍💻 پشتیبانی")],
        [KeyboardButton("🌐 تغییر زبان")]  # Added language button
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

    # Personalized welcome message with Persian charm ✨
    welcome_message = (
        f"سلام {user.first_name} عزیز! 👋 به دنیای پرسرعت MoonVPN خوش اومدی! 🚀\n\n"
        f"من اینجا هستم تا بهترین تجربه اتصال به اینترنت آزاد رو برات فراهم کنم. ✨\n\n"
        f"از دکمه‌های پایین می‌تونی برای شروع استفاده کنی 👇 یا اگه سوالی داشتی، روی /help کلیک کن."
    )

    await update.message.reply_html(
        welcome_message,
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a help message when the /help command is issued.
    Provide more detailed help later.
    """
    logger.info(f"User {update.effective_user.id} requested help.")
    await update.message.reply_text("راهنما در دست ساخت است... 🚧 به زودی اطلاعات بیشتری اینجا قرار می‌گیره!")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message (for testing). Remove later.
    Also handles keyboard button presses if they are sent as text messages.
    """
    user_text = update.message.text
    logger.info(f"Received message from {update.effective_user.id}: {user_text}")

    # Basic handling for reply keyboard buttons
    if user_text == "🚀 نمایش سرویس‌ها":
        await update.message.reply_text("در حال دریافت لیست سرویس‌ها... ⏳")
        # TODO: Implement plan listing logic
    elif user_text == "💼 حساب کاربری من":
        await update.message.reply_text("بخش حساب کاربری به زودی فعال می‌شه! 🛠️")
        # TODO: Implement account logic
    elif user_text == "💰 کیف پول":
        await update.message.reply_text("مدیریت کیف پول شما به زودی اینجا خواهد بود! 💳")
        # TODO: Implement wallet logic
    elif user_text == "🧑‍💻 پشتیبانی":
        await update.message.reply_text("برای ارتباط با پشتیبانی، می‌تونی از آیدی @MoonVPNSupport استفاده کنی. 😊")
        # TODO: Implement better support flow
    elif user_text == "🌐 تغییر زبان":
        # Trigger the language command
        await update.message.reply_text("/language")
    else:
        # Default echo for other messages (remove in production)
        await update.message.reply_text(f"پیام شما دریافت شد: {user_text}")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log Errors caused by Updates.
    """
    logger.error(f"Update {update} caused error {context.error}", exc_info=context.error)


def main() -> None:
    """Start the bot.
    Uses Polling for development, switch to Webhook for production.
    """
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.error("Telegram Bot Token not found in environment variables!")
        return

    # Create the Application and pass it your bot's token.
    application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()

    # --- Register Handlers ---
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # Setup language handlers
    setup_language_handlers(application)

    # Add a message handler to echo text messages and handle keyboard buttons
    # Ensure it doesn't clash with commands
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Error handler
    application.add_error_handler(error_handler)

    # Add more handlers here (CallbackQueryHandler, ConversationHandler, etc.)

    # --- Start the Bot ---
    if settings.TELEGRAM_WEBHOOK_URL:
        # Use Webhook in production
        logger.info(f"Starting bot in Webhook mode. URL: {settings.TELEGRAM_WEBHOOK_URL}")
        # Ensure TELEGRAM_WEBHOOK_SECRET is set if needed
        # await application.bot.set_webhook(
        #     url=settings.TELEGRAM_WEBHOOK_URL,
        #     secret_token=settings.TELEGRAM_WEBHOOK_SECRET
        # )
        # Needs an accompanying webserver (like FastAPI) to handle updates at the webhook URL
        # The Application object itself doesn't run a server for webhooks
        logger.warning("Webhook setup requires a running webserver endpoint. Running with polling for now.")
        application.run_polling()
    else:
        # Use Polling for development
        logger.info("Starting bot in Polling mode.")
        application.run_polling()

if __name__ == "__main__":
    main()
