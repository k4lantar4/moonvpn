import logging
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ChatMemberStatus
from telegram.error import BadRequest

from app.core.config import REQUIRED_CHANNEL_ID
from app.utils import api_client
# Import main menu keyboard/handler later when created
from app.handlers.main_menu import show_main_menu
# from app.keyboards.main_menu import main_menu_keyboard # We use show_main_menu which uses the keyboard

# Enable logging
logger = logging.getLogger(__name__)

# Define states for conversation if needed later, but not strictly required for this simple flow
ASKING_CONTACT = 1

async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int | None:
    """Handles the /start command. Checks if user exists, otherwise prompts for contact."""
    user = update.effective_user
    if not user:
        logger.warning("Received /start from an invalid user.")
        return None # Or ConversationHandler.END if using ConversationHandler

    logger.info(f"User {user.id} ({user.username or 'No username'}) started the bot.")

    # Check if user exists in our system via API
    existing_user = await api_client.get_user_by_telegram_id(user.id)

    if existing_user:
        logger.info(f"Existing user {user.id} started. Showing main menu.")
        # User already registered, show main menu
        await show_main_menu(update, context)
        # await update.message.reply_text(
        #     f"سلام {user.first_name}! خوش آمدید. 👋",
        #     # reply_markup=main_menu_keyboard() # Add keyboard later
        # )
        return None # Or ConversationHandler.END if using ConversationHandler
    else:
        logger.info(f"New user {user.id} started. Asking for contact and channel join.")
        # New user, explain requirements and ask for contact
        share_button = KeyboardButton(text="📱 اشتراک گذاری شماره تلفن", request_contact=True)
        keyboard = ReplyKeyboardMarkup([[share_button]], resize_keyboard=True, one_time_keyboard=True)

        await update.message.reply_text(
            f"سلام {user.first_name}! 👋\n"
            f"برای استفاده از MoonVPN، لطفاً ابتدا در کانال ما عضو شوید:\n"
            f"@moonvpn1_channel (ID: {REQUIRED_CHANNEL_ID})\n\n" # TODO: Make channel link dynamic/configurable?
            "و سپس شماره تلفن خود را (که با +98 شروع می‌شود) با دکمه زیر به اشتراک بگذارید.",
            reply_markup=keyboard,
        )
        # If using ConversationHandler, return the next state
        # return ASKING_CONTACT
        return None # Not using ConversationHandler for this simple flow yet


async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int | None:
    """Handles the user sharing their contact information."""
    user = update.effective_user
    contact = update.message.contact
    chat_id = update.effective_chat.id

    if not user or not contact:
        logger.warning("Received invalid contact message.")
        return None # Or ConversationHandler.END

    # --- Security Check: Ensure the contact shared belongs to the user sending the message ---
    if contact.user_id != user.id:
        logger.warning(f"Contact user_id {contact.user_id} does not match message sender user_id {user.id}. Ignoring.")
        await context.bot.send_message(chat_id, "خطا: اطلاعات تماس ارسال شده نامعتبر است.", reply_markup=ReplyKeyboardRemove())
        return None # Or ConversationHandler.END

    logger.info(f"User {user.id} shared contact. Phone: {contact.phone_number}")

    # --- Check 1: Phone Number Prefix (+98) ---
    phone_number = contact.phone_number
    if not phone_number.startswith('+98') and not phone_number.startswith('98'):
        logger.warning(f"User {user.id} phone number '{phone_number}' does not start with +98.")
        await context.bot.send_message(
            chat_id,
            "⚠️ شماره تلفن شما باید با +98 شروع شود. لطفاً دوباره تلاش کنید.",
            reply_markup=ReplyKeyboardRemove()
        )
        # Ask again? Or just end? Ending for now.
        return None # Or ConversationHandler.END

    # Ensure phone number has the + prefix for consistency if API expects it
    if not phone_number.startswith('+'):
        phone_number = '+' + phone_number

    # --- Check 2: Channel Membership ---
    try:
        chat_member = await context.bot.get_chat_member(chat_id=REQUIRED_CHANNEL_ID, user_id=user.id)
        logger.info(f"User {user.id} channel membership status: {chat_member.status}")

        allowed_statuses = [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]
        if chat_member.status not in allowed_statuses:
            logger.warning(f"User {user.id} is not a member of channel {REQUIRED_CHANNEL_ID}.")
            await context.bot.send_message(
                chat_id,
                f"⚠️ شما هنوز عضو کانال @moonvpn1_channel نشده‌اید.\n"
                f"لطفاً ابتدا عضو شوید و سپس دوباره شماره خود را به اشتراک بگذارید.",
                reply_markup=ReplyKeyboardRemove()
                # TODO: Maybe add an inline button linking to the channel?
            )
            return None # Or ConversationHandler.END

    except BadRequest as e:
        # Handle cases where the bot might not be in the channel or other permission issues
        logger.error(f"Error checking channel membership for user {user.id} in channel {REQUIRED_CHANNEL_ID}: {e}")
        if "chat not found" in str(e).lower() or "user not found" in str(e).lower(): # More specific error checks may be needed
             await context.bot.send_message(
                 chat_id,
                 "خطا در بررسی عضویت کانال. لطفاً مطمئن شوید ربات در کانال عضو است.",
                 reply_markup=ReplyKeyboardRemove()
             )
        else:
            await context.bot.send_message(
                chat_id,
                "خطا در بررسی عضویت کانال. لطفاً دقایقی دیگر دوباره امتحان کنید.",
                reply_markup=ReplyKeyboardRemove()
            )
        return None # Or ConversationHandler.END
    except Exception as e:
        logger.error(f"Unexpected error checking channel membership for user {user.id}: {e}")
        await context.bot.send_message(chat_id, "خطای غیرمنتظره‌ای رخ داد. لطفاً بعدا تلاش کنید.", reply_markup=ReplyKeyboardRemove())
        return None # Or ConversationHandler.END


    # --- All Checks Passed: Register User via API ---
    logger.info(f"Checks passed for user {user.id}. Attempting registration.")
    registered_user = await api_client.register_user(
        telegram_id=user.id,
        first_name=user.first_name,
        username=user.username,
        phone_number=phone_number # Send the validated phone number
    )

    if registered_user:
        logger.info(f"User {user.id} successfully registered via API.")
        await context.bot.send_message(
            chat_id,
            "✅ ثبت نام شما با موفقیت انجام شد! 🎉\nبه MoonVPN خوش آمدید.",
            reply_markup=ReplyKeyboardRemove()
        )
        # Now show the main menu
        await show_main_menu(update, context)
    else:
        logger.error(f"Failed to register user {user.id} via API.")
        await context.bot.send_message(
            chat_id,
            "❌ متاسفانه در حال حاضر امکان ثبت نام وجود ندارد. لطفاً بعدا تلاش کنید.",
            reply_markup=ReplyKeyboardRemove()
        )

    return None # Or ConversationHandler.END

# --- If using ConversationHandler, define the handler like this: ---
# start_conversation_handler = ConversationHandler(
#     entry_points=[CommandHandler("start", handle_start)],
#     states={
#         ASKING_CONTACT: [MessageHandler(filters.CONTACT, handle_contact)],
#         # Add other states and handlers here
#     },
#     fallbacks=[CommandHandler("cancel", handle_cancel)], # Need a cancel handler
# ) 