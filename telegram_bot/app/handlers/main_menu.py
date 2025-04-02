import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, MessageHandler, CommandHandler, filters

from app.keyboards.main_menu import main_menu_keyboard, BTN_BUY_SERVICE, BTN_WALLET, BTN_MY_ORDERS
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

async def handle_my_orders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the 'My Orders' button press. Fetches and displays user's orders."""
    chat_id = update.effective_chat.id
    user = update.effective_user
    if not chat_id or not user:
        logger.warning("handle_my_orders called without chat_id or user")
        return

    logger.info(f"User {user.id} requested to view their orders.")

    # Send a waiting message
    waiting_message = await context.bot.send_message(chat_id, "⏳ در حال دریافت سفارش‌های شما...")

    orders = await api_client.get_user_orders(user.id)

    # Delete the waiting message
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=waiting_message.message_id)
    except Exception as e:
        logger.warning(f"Could not delete waiting message: {e}")

    if orders is None:
        await context.bot.send_message(chat_id, "❌ خطایی در دریافت لیست سفارش‌ها رخ داد. لطفاً بعدا تلاش کنید.")
        return

    if not orders:
        await context.bot.send_message(chat_id, "ℹ️ شما هنوز هیچ سفارشی ثبت نکرده‌اید.")
        return

    # Sort orders by created_at (newest first)
    orders.sort(key=lambda x: x.get('created_at', ''), reverse=True)

    # Show the most recent 5 orders
    recent_orders = orders[:5]
    
    # Group orders by status for better presentation
    orders_message = "📋 سفارش‌های اخیر شما:\n\n"
    
    for order in recent_orders:
        order_id = order.get('id', 'نامشخص')
        order_external_id = order.get('order_id', 'نامشخص')  # The UUID shown to users
        created_at = order.get('created_at', 'نامشخص')
        status = order.get('status', 'نامشخص')
        amount = order.get('final_amount', 0)
        payment_method = order.get('payment_method', 'نامشخص')
        
        # Format amount with commas
        try:
            formatted_amount = f"{int(amount):,} تومان"
        except (ValueError, TypeError):
            formatted_amount = f"{amount} تومان"
        
        # Format date to Persian-friendly format - Simple version
        try:
            # Just extracting date part for simplicity
            date_part = created_at.split('T')[0] if 'T' in created_at else created_at
        except:
            date_part = created_at
        
        # Translate status to Persian
        status_persian = {
            'pending': "در انتظار پرداخت ⏳",
            'paid': "پرداخت شده ✓",
            'confirmed': "تأیید شده ✅",
            'rejected': "رد شده ❌",
            'expired': "منقضی شده ⏰",
            'canceled': "لغو شده 🚫",
            'failed': "ناموفق ⚠️",
            'verification_pending': "در انتظار تأیید پرداخت 🔍"
        }.get(status, f"نامشخص ({status})")
        
        # Translate payment method to Persian
        payment_method_persian = {
            'card_to_card': "کارت به کارت 💳",
            'wallet': "کیف پول 💰",
            'zarinpal': "زرین‌پال 🌐",
            'crypto': "ارز دیجیتال 💎",
            'manual': "پرداخت دستی 👨‍💻"
        }.get(payment_method, f"نامشخص ({payment_method})")
        
        # Check if this is a Zarinpal payment that needs action
        zarinpal_action = ""
        if payment_method == 'zarinpal' and status == 'pending':
            # If this is a pending Zarinpal payment, we might want to show a "Pay Now" button
            # We'll add the order ID to context for callbacks
            zarinpal_action = f"\n💠 این سفارش در انتظار پرداخت آنلاین است. لطفاً با فشردن 'پرداخت مجدد' اقدام کنید."
        
        orders_message += f"🔹 سفارش #{order_external_id[:8]}...\n"
        orders_message += f"   📅 تاریخ: {date_part}\n"
        orders_message += f"   💰 مبلغ: {formatted_amount}\n"
        orders_message += f"   💳 روش پرداخت: {payment_method_persian}\n"
        orders_message += f"   🔄 وضعیت: {status_persian}{zarinpal_action}\n\n"
    
    # Add a button for Zarinpal pending payments if needed
    keyboard = []
    for order in recent_orders:
        if order.get('payment_method') == 'zarinpal' and order.get('status') == 'pending':
            order_id = order.get('id')
            keyboard.append([
                InlineKeyboardButton(
                    text=f"🔄 پرداخت مجدد سفارش #{order.get('order_id', '')[:8]}...",
                    callback_data=f"retry_zarinpal_{order_id}"
                )
            ])
    
    if keyboard:
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(chat_id, orders_message, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await context.bot.send_message(chat_id, orders_message, parse_mode='Markdown')

# Main menu handler
main_menu_handler = [
    MessageHandler(filters.Text([BTN_BUY_SERVICE]), handle_buy_service),
    MessageHandler(filters.Text([BTN_WALLET]), handle_wallet),
    MessageHandler(filters.Text([BTN_MY_ORDERS]), handle_my_orders),
    # Add more message handlers for other buttons as they are implemented
    CommandHandler("menu", show_main_menu)  # Also accessible via /menu command
] 