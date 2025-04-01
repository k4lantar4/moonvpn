import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from app.keyboards.main_menu import main_menu_keyboard, BTN_BUY_SERVICE
from app.utils import api_client

# Enable logging
logger = logging.getLogger(__name__)

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends the main menu message and keyboard to the user."""
    user = update.effective_user
    chat_id = update.effective_chat.id
    if not user or not chat_id:
        logger.warning("show_main_menu called without user or chat_id")
        return

    # Use first_name if available, otherwise provide a default greeting
    first_name = user.first_name if user.first_name else "کاربر"

    message_text = f"سلام {first_name}! 👋\n"
    message_text += "منوی اصلی:\n"
    message_text += f"- {BTN_BUY_SERVICE}: مشاهده و خرید سرویس‌های موجود.\n"
    message_text += "- 👤 حساب کاربری من: مدیریت اشتراک‌ها و اطلاعات کاربری.\n"
    message_text += "- 💳 کیف پول: مشاهده موجودی و شارژ حساب.\n"
    message_text += "- 🔗 معرفی دوستان: دریافت لینک دعوت و مشاهده درآمد.\n"
    message_text += "- 💬 پشتیبانی: ارتباط با تیم پشتیبانی.\n"

    await context.bot.send_message(
        chat_id=chat_id,
        text=message_text,
        reply_markup=main_menu_keyboard()
    )

async def handle_buy_service(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the 'Buy Service' button press. Fetches and displays active plans."""
    chat_id = update.effective_chat.id
    user = update.effective_user
    if not chat_id or not user:
        logger.warning("handle_buy_service called without chat_id or user")
        return

    logger.info(f"User {user.id} requested to buy service.")

    # Send a waiting message
    waiting_message = await context.bot.send_message(chat_id, "⏳ در حال دریافت لیست سرویس‌ها...")

    active_plans = await api_client.get_active_plans()

    # Delete the waiting message
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=waiting_message.message_id)
    except Exception as e:
        logger.warning(f"Could not delete waiting message: {e}")

    if active_plans is None:
        await context.bot.send_message(chat_id, "❌ خطایی در دریافت لیست سرویس‌ها رخ داد. لطفاً بعدا تلاش کنید.")
        return

    if not active_plans:
        await context.bot.send_message(chat_id, "ℹ️ در حال حاضر هیچ سرویس فعالی برای خرید وجود ندارد.")
        return

    # --- Display Plans using Inline Keyboard ---
    keyboard = []
    plan_message = "👇 سرویس‌های موجود:\n\n"

    for plan in active_plans:
        # Assuming plan object has keys: id, name, price, duration_days, data_limit_gb
        plan_id = plan.get('id')
        name = plan.get('name', 'نامشخص')
        price = plan.get('price', 0)
        duration = plan.get('duration_days', '?')
        data_limit = plan.get('data_limit_gb', '?')

        if not plan_id:
            logger.warning(f"Skipping plan with missing ID: {plan}")
            continue

        # Format plan details for the message
        plan_message += f"🔹 **{name}**\n"
        plan_message += f"   - 📅 مدت: {duration} روز\n"
        plan_message += f"   - 📊 حجم: {data_limit} گیگابایت\n"
        # Format price with commas
        try:
            formatted_price = f"{int(price):,} تومان"
        except (ValueError, TypeError):
            formatted_price = f"{price} تومان"
        plan_message += f"   - 💰 قیمت: {formatted_price}\n\n"

        # Create an inline button for each plan
        # The callback_data should uniquely identify the plan, e.g., "buy_plan_{plan_id}"
        button = InlineKeyboardButton(
            text=f"🛒 خرید {name} ({formatted_price})",
            callback_data=f"buy_plan_{plan_id}"
        )
        keyboard.append([button])

    if not keyboard: # If all plans were skipped due to missing ID or other issues
         await context.bot.send_message(chat_id, "ℹ️ سرویس‌های معتبری برای نمایش یافت نشد.")
         return

    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id, plan_message, reply_markup=reply_markup, parse_mode='Markdown')

# --- Handler for Wallet Button ---
async def handle_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the 'Wallet' button press. Fetches and displays user's wallet balance."""
    chat_id = update.effective_chat.id
    user = update.effective_user
    if not chat_id or not user:
        logger.warning("handle_wallet called without chat_id or user")
        return

    logger.info(f"User {user.id} requested wallet balance.")

    # Assume api_client.get_user_info(user_id) fetches user data including wallet
    # Let's assume it returns a dict like {'id': ..., 'telegram_id': ..., 'wallet_balance': 15000.0, ...}
    # Or None if user not found or API error

    user_info = await api_client.get_user_info(user.id) # Using telegram_id

    if user_info is None:
        await context.bot.send_message(chat_id, "❌ خطایی در دریافت اطلاعات کیف پول رخ داد. لطفاً دوباره امتحان کنید.")
        return

    wallet_balance = user_info.get('wallet_balance', 0.0) # Default to 0.0 if key missing

    try:
        # Format balance with commas and handle potential non-numeric types gracefully
        formatted_balance = f"{float(wallet_balance):,.0f} تومان" # Using .0f to remove decimals if integer
    except (ValueError, TypeError):
        logger.warning(f"Could not format wallet balance '{wallet_balance}' for user {user.id}")
        formatted_balance = f"{wallet_balance} تومان" # Fallback to showing as is

    # TODO: Add buttons for "Deposit" / "Transaction History" later
    message_text = f"💰 موجودی کیف پول شما: **{formatted_balance}**"
    await context.bot.send_message(chat_id, message_text, parse_mode='Markdown')

# --- Add handlers for other main menu buttons later ---
# async def handle_my_account(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     pass
# async def handle_support(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     pass
# async def handle_referral(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     pass 