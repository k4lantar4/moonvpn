from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ContextTypes, CommandHandler, MessageHandler, 
    CallbackQueryHandler, ConversationHandler, filters
)
from telegram.constants import ParseMode

from app.api.api_client import (
    get_user_subscriptions, get_subscription_details,
    get_subscription_qrcode, get_subscription_traffic,
    freeze_subscription, unfreeze_subscription,
    add_subscription_note, toggle_subscription_auto_renew,
    change_subscription_protocol_location
)
from app.keyboards.main_menu import BTN_MY_ACCOUNTS
from app.utils.logger import get_logger

# Set up logging
logger = get_logger(__name__)

# Conversation states
(
    SHOWING_ACCOUNTS, ACCOUNT_DETAILS, ACCOUNT_ACTIONS,
    FREEZE_ACCOUNT, ADD_NOTE, CHANGE_PROTOCOL
) = range(6)

# Callback data patterns
SUBSCRIPTION_PREFIX = "sub_"
ACTION_PREFIX = "action_"
BACK_TO_LIST = "back_to_list"
BACK_TO_DETAILS = "back_to_details"
SHOW_QR = "show_qr"
SHOW_TRAFFIC = "show_traffic"
FREEZE = "freeze"
UNFREEZE = "unfreeze"
ADD_NOTE = "add_note"
TOGGLE_AUTO_RENEW = "toggle_auto_renew"
CHANGE_PROTOCOL_LOCATION = "change_protocol_location"

async def accounts_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Display a list of the user's VPN accounts/subscriptions."""
    user_id = update.effective_user.id
    
    # Fetch user's subscriptions
    subscriptions = await get_user_subscriptions(user_id)
    
    if not subscriptions:
        await update.effective_message.reply_text(
            "🔍 شما در حال حاضر هیچ اشتراک فعالی ندارید.\n"
            "برای خرید اشتراک جدید، از منوی 'خرید سرویس' استفاده کنید."
        )
        return ConversationHandler.END
    
    # Create keyboard with subscription buttons
    keyboard = []
    for sub in subscriptions:
        # Format button text with subscription name and status
        status_emoji = "✅" if sub.get("is_active", False) else "❌"
        button_text = f"{status_emoji} {sub.get('name', 'اشتراک')} - {sub.get('remaining_days', 0)} روز"
        
        # Add button to keyboard
        keyboard.append([
            InlineKeyboardButton(
                button_text, 
                callback_data=f"{SUBSCRIPTION_PREFIX}{sub.get('id')}"
            )
        ])
    
    # Add back button
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="cancel")])
    
    await update.effective_message.reply_text(
        "📱 اشتراک‌های شما:\n"
        "لطفاً یک اشتراک را برای مشاهده جزئیات و مدیریت آن انتخاب کنید.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return SHOWING_ACCOUNTS

async def show_account_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show details for a selected subscription."""
    query = update.callback_query
    await query.answer()
    
    # Extract subscription ID from callback data
    subscription_id = query.data.replace(SUBSCRIPTION_PREFIX, "")
    context.user_data["current_subscription_id"] = subscription_id
    
    # Fetch subscription details
    subscription = await get_subscription_details(subscription_id)
    
    if not subscription:
        await query.edit_message_text("⚠️ اطلاعات اشتراک یافت نشد. لطفاً دوباره تلاش کنید.")
        return ConversationHandler.END
    
    # Store subscription info in context for future use
    context.user_data["current_subscription"] = subscription
    
    # Format subscription details
    status = "فعال ✅" if subscription.get("is_active", False) else "غیرفعال ❌"
    auto_renew = "فعال ✅" if subscription.get("auto_renew", False) else "غیرفعال ❌"
    
    details_text = (
        f"🔹 <b>نام اشتراک:</b> {subscription.get('name', 'نامشخص')}\n"
        f"🔹 <b>وضعیت:</b> {status}\n"
        f"🔹 <b>تاریخ انقضا:</b> {subscription.get('expiry_date', 'نامشخص')}\n"
        f"🔹 <b>روزهای باقیمانده:</b> {subscription.get('remaining_days', 0)}\n"
        f"🔹 <b>تمدید خودکار:</b> {auto_renew}\n"
        f"🔹 <b>پروتکل:</b> {subscription.get('protocol', 'نامشخص')}\n"
        f"🔹 <b>لوکیشن:</b> {subscription.get('location', 'نامشخص')}\n"
    )
    
    # Add subscription note if it exists
    if subscription.get("note"):
        details_text += f"\n📝 <b>یادداشت:</b>\n{subscription.get('note')}\n"
    
    # Create action buttons
    keyboard = [
        [
            InlineKeyboardButton("📊 آمار مصرف", callback_data=SHOW_TRAFFIC),
            InlineKeyboardButton("🔄 QR کد", callback_data=SHOW_QR)
        ]
    ]
    
    # Add management buttons based on subscription status
    if subscription.get("is_active", False):
        keyboard.append([
            InlineKeyboardButton("❄️ فریز اشتراک", callback_data=f"{ACTION_PREFIX}{FREEZE}")
        ])
    else:
        keyboard.append([
            InlineKeyboardButton("♨️ لغو فریز", callback_data=f"{ACTION_PREFIX}{UNFREEZE}")
        ])
    
    keyboard.extend([
        [
            InlineKeyboardButton("📝 افزودن یادداشت", callback_data=f"{ACTION_PREFIX}{ADD_NOTE}"),
            InlineKeyboardButton(
                "🔄 تغییر تمدید خودکار", 
                callback_data=f"{ACTION_PREFIX}{TOGGLE_AUTO_RENEW}"
            )
        ],
        [
            InlineKeyboardButton(
                "🔄 تغییر پروتکل/لوکیشن", 
                callback_data=f"{ACTION_PREFIX}{CHANGE_PROTOCOL_LOCATION}"
            )
        ],
        [InlineKeyboardButton("🔙 بازگشت به لیست", callback_data=BACK_TO_LIST)]
    ])
    
    await query.edit_message_text(
        details_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML
    )
    
    return ACCOUNT_DETAILS

async def show_qrcode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show QR code for the subscription."""
    query = update.callback_query
    await query.answer()
    
    subscription_id = context.user_data.get("current_subscription_id")
    
    # Fetch QR code data
    qr_data = await get_subscription_qrcode(subscription_id)
    
    if not qr_data or not qr_data.get("qrcode"):
        await query.edit_message_text(
            "⚠️ دریافت QR کد با خطا مواجه شد. لطفاً دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت", callback_data=BACK_TO_DETAILS)
            ]])
        )
        return ACCOUNT_DETAILS
    
    # Get subscription name
    subscription = context.user_data.get("current_subscription", {})
    subscription_name = subscription.get("name", "اشتراک")
    
    await query.edit_message_text(
        f"🔄 QR کد برای اشتراک <b>{subscription_name}</b>:\n\n"
        f"<code>{qr_data.get('qrcode')}</code>\n\n"
        "این کد را می‌توانید در اپلیکیشن خود وارد کنید.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 بازگشت", callback_data=BACK_TO_DETAILS)
        ]]),
        parse_mode=ParseMode.HTML
    )
    
    return ACCOUNT_DETAILS

async def show_traffic(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show traffic usage statistics for the subscription."""
    query = update.callback_query
    await query.answer()
    
    subscription_id = context.user_data.get("current_subscription_id")
    
    # Fetch traffic data
    traffic_data = await get_subscription_traffic(subscription_id)
    
    if not traffic_data:
        await query.edit_message_text(
            "⚠️ دریافت آمار مصرف با خطا مواجه شد. لطفاً دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت", callback_data=BACK_TO_DETAILS)
            ]])
        )
        return ACCOUNT_DETAILS
    
    # Get subscription name
    subscription = context.user_data.get("current_subscription", {})
    subscription_name = subscription.get("name", "اشتراک")
    
    # Calculate usage percentage
    used_gb = traffic_data.get("used_gb", 0)
    total_gb = traffic_data.get("total_gb", 0)
    
    # Avoid division by zero
    percentage = (used_gb / total_gb * 100) if total_gb > 0 else 0
    
    # Create progress bar
    progress_bar = create_progress_bar(percentage)
    
    traffic_text = (
        f"📊 آمار مصرف برای اشتراک <b>{subscription_name}</b>:\n\n"
        f"{progress_bar}\n"
        f"📥 مصرف شده: {used_gb:.2f} GB\n"
        f"💾 حجم کل: {total_gb:.2f} GB\n"
        f"⏳ درصد مصرف: {percentage:.1f}%"
    )
    
    await query.edit_message_text(
        traffic_text,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 بازگشت", callback_data=BACK_TO_DETAILS)
        ]]),
        parse_mode=ParseMode.HTML
    )
    
    return ACCOUNT_DETAILS

def create_progress_bar(percentage: float, length: int = 10) -> str:
    """Create a text-based progress bar."""
    filled_length = int(length * percentage / 100)
    bar = '█' * filled_length + '░' * (length - filled_length)
    return f"[{bar}]"

async def handle_account_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle various account actions."""
    query = update.callback_query
    await query.answer()
    
    action = query.data.replace(ACTION_PREFIX, "")
    
    if action == FREEZE:
        await query.edit_message_text(
            "❄️ لطفاً دلیل فریز کردن اشتراک را بنویسید:\n"
            "(یا 'انصراف' را برای لغو عملیات ارسال کنید)",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 انصراف", callback_data=BACK_TO_DETAILS)
            ]])
        )
        return FREEZE_ACCOUNT
    
    elif action == UNFREEZE:
        # Unfreeze subscription
        subscription_id = context.user_data.get("current_subscription_id")
        result = await unfreeze_subscription(subscription_id)
        
        if result:
            # Update stored subscription data
            context.user_data["current_subscription"] = result
            
            await query.edit_message_text(
                "♨️ اشتراک شما با موفقیت از حالت فریز خارج شد.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data=BACK_TO_DETAILS)
                ]])
            )
        else:
            await query.edit_message_text(
                "⚠️ عملیات لغو فریز با خطا مواجه شد. لطفاً دوباره تلاش کنید.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data=BACK_TO_DETAILS)
                ]])
            )
        
        return ACCOUNT_DETAILS
    
    elif action == ADD_NOTE:
        await query.edit_message_text(
            "📝 لطفاً یادداشت خود را برای این اشتراک وارد کنید:\n"
            "(یا 'انصراف' را برای لغو عملیات ارسال کنید)",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 انصراف", callback_data=BACK_TO_DETAILS)
            ]])
        )
        return ADD_NOTE
    
    elif action == TOGGLE_AUTO_RENEW:
        # Toggle auto-renew setting
        subscription_id = context.user_data.get("current_subscription_id")
        result = await toggle_subscription_auto_renew(subscription_id)
        
        if result:
            # Update stored subscription data
            context.user_data["current_subscription"] = result
            
            # Get the new status
            new_status = "فعال ✅" if result.get("auto_renew", False) else "غیرفعال ❌"
            
            await query.edit_message_text(
                f"🔄 تنظیم تمدید خودکار با موفقیت تغییر کرد.\n"
                f"وضعیت جدید: {new_status}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data=BACK_TO_DETAILS)
                ]])
            )
        else:
            await query.edit_message_text(
                "⚠️ تغییر تنظیم تمدید خودکار با خطا مواجه شد. لطفاً دوباره تلاش کنید.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data=BACK_TO_DETAILS)
                ]])
            )
        
        return ACCOUNT_DETAILS
    
    elif action == CHANGE_PROTOCOL_LOCATION:
        # Get available protocols and locations
        await query.edit_message_text(
            "🔄 لطفاً عملیات مورد نظر را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("تغییر پروتکل", callback_data="protocol")],
                [InlineKeyboardButton("تغییر لوکیشن", callback_data="location")],
                [InlineKeyboardButton("🔙 انصراف", callback_data=BACK_TO_DETAILS)]
            ])
        )
        return CHANGE_PROTOCOL
    
    return ACCOUNT_DETAILS

async def handle_freeze_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process the freeze reason and freeze the subscription."""
    user_message = update.message.text
    
    # Check if user wants to cancel
    if user_message.lower() == "انصراف":
        await update.message.reply_text(
            "❌ عملیات فریز کردن لغو شد.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت به جزئیات", callback_data=BACK_TO_DETAILS)
            ]])
        )
        return ACCOUNT_DETAILS
    
    # Process the freeze with the provided reason
    subscription_id = context.user_data.get("current_subscription_id")
    freeze_reason = user_message
    
    # Call API to freeze subscription
    result = await freeze_subscription(subscription_id, reason=freeze_reason)
    
    if result:
        # Update stored subscription data
        context.user_data["current_subscription"] = result
        
        await update.message.reply_text(
            "❄️ اشتراک شما با موفقیت فریز شد.\n"
            "می‌توانید هر زمان که بخواهید آن را از حالت فریز خارج کنید.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت به جزئیات", callback_data=BACK_TO_DETAILS)
            ]])
        )
    else:
        await update.message.reply_text(
            "⚠️ عملیات فریز با خطا مواجه شد. لطفاً دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت به جزئیات", callback_data=BACK_TO_DETAILS)
            ]])
        )
    
    return ACCOUNT_DETAILS

async def handle_note_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process the note input and add it to the subscription."""
    user_message = update.message.text
    
    # Check if user wants to cancel
    if user_message.lower() == "انصراف":
        await update.message.reply_text(
            "❌ عملیات افزودن یادداشت لغو شد.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت به جزئیات", callback_data=BACK_TO_DETAILS)
            ]])
        )
        return ACCOUNT_DETAILS
    
    # Process the note
    subscription_id = context.user_data.get("current_subscription_id")
    note = user_message
    
    # Call API to add note
    result = await add_subscription_note(subscription_id, note)
    
    if result:
        # Update stored subscription data
        context.user_data["current_subscription"] = result
        
        await update.message.reply_text(
            "📝 یادداشت با موفقیت به اشتراک شما اضافه شد.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت به جزئیات", callback_data=BACK_TO_DETAILS)
            ]])
        )
    else:
        await update.message.reply_text(
            "⚠️ افزودن یادداشت با خطا مواجه شد. لطفاً دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت به جزئیات", callback_data=BACK_TO_DETAILS)
            ]])
        )
    
    return ACCOUNT_DETAILS

async def handle_protocol_location_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle selection of protocol or location change."""
    query = update.callback_query
    await query.answer()
    
    selection = query.data
    
    if selection == BACK_TO_DETAILS:
        return await show_account_details(update, context)
    
    if selection == "protocol":
        # Display protocol options
        keyboard = [
            [InlineKeyboardButton("VLESS", callback_data="change_protocol_vless")],
            [InlineKeyboardButton("VMess", callback_data="change_protocol_vmess")],
            [InlineKeyboardButton("Trojan", callback_data="change_protocol_trojan")],
            [InlineKeyboardButton("Shadowsocks", callback_data="change_protocol_shadowsocks")],
            [InlineKeyboardButton("🔙 انصراف", callback_data=BACK_TO_DETAILS)]
        ]
        
        await query.edit_message_text(
            "🔄 لطفاً پروتکل جدید را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif selection == "location":
        # Display location options
        keyboard = [
            [InlineKeyboardButton("آلمان 🇩🇪", callback_data="change_location_germany")],
            [InlineKeyboardButton("هلند 🇳🇱", callback_data="change_location_netherlands")],
            [InlineKeyboardButton("فرانسه 🇫🇷", callback_data="change_location_france")],
            [InlineKeyboardButton("آمریکا 🇺🇸", callback_data="change_location_usa")],
            [InlineKeyboardButton("🔙 انصراف", callback_data=BACK_TO_DETAILS)]
        ]
        
        await query.edit_message_text(
            "🔄 لطفاً لوکیشن جدید را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif selection.startswith("change_protocol_"):
        # Handle protocol change
        protocol = selection.replace("change_protocol_", "")
        subscription_id = context.user_data.get("current_subscription_id")
        
        result = await change_subscription_protocol_location(
            subscription_id, protocol=protocol
        )
        
        if result:
            # Update stored subscription data
            context.user_data["current_subscription"] = result
            
            await query.edit_message_text(
                f"✅ پروتکل اشتراک با موفقیت به {protocol} تغییر یافت.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت به جزئیات", callback_data=BACK_TO_DETAILS)
                ]])
            )
        else:
            await query.edit_message_text(
                "⚠️ تغییر پروتکل با خطا مواجه شد. لطفاً دوباره تلاش کنید.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت به جزئیات", callback_data=BACK_TO_DETAILS)
                ]])
            )
    
    elif selection.startswith("change_location_"):
        # Handle location change
        location = selection.replace("change_location_", "")
        subscription_id = context.user_data.get("current_subscription_id")
        
        result = await change_subscription_protocol_location(
            subscription_id, location=location
        )
        
        if result:
            # Update stored subscription data
            context.user_data["current_subscription"] = result
            
            await query.edit_message_text(
                f"✅ لوکیشن اشتراک با موفقیت به {location} تغییر یافت.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت به جزئیات", callback_data=BACK_TO_DETAILS)
                ]])
            )
        else:
            await query.edit_message_text(
                "⚠️ تغییر لوکیشن با خطا مواجه شد. لطفاً دوباره تلاش کنید.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت به جزئیات", callback_data=BACK_TO_DETAILS)
                ]])
            )
    
    return ACCOUNT_DETAILS

async def back_to_accounts_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Return to the accounts list view."""
    query = update.callback_query
    await query.answer()
    
    # Clear current subscription data
    if "current_subscription_id" in context.user_data:
        del context.user_data["current_subscription_id"]
    if "current_subscription" in context.user_data:
        del context.user_data["current_subscription"]
    
    # Return to accounts list
    return await accounts_list(update, context)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the conversation and return to the main menu."""
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text("❌ عملیات لغو شد. به منوی اصلی بازگشتید.")
    else:
        await update.message.reply_text("❌ عملیات لغو شد. به منوی اصلی بازگشتید.")
    
    # Clear user data
    context.user_data.clear()
    
    return ConversationHandler.END

def get_my_accounts_handler():
    """Return the ConversationHandler for the my accounts feature."""
    return ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex(f"^{BTN_MY_ACCOUNTS}$"), accounts_list),
            CommandHandler("accounts", accounts_list)
        ],
        states={
            SHOWING_ACCOUNTS: [
                CallbackQueryHandler(show_account_details, pattern=f"^{SUBSCRIPTION_PREFIX}"),
                CallbackQueryHandler(cancel, pattern="^cancel$")
            ],
            ACCOUNT_DETAILS: [
                CallbackQueryHandler(show_qrcode, pattern=f"^{SHOW_QR}$"),
                CallbackQueryHandler(show_traffic, pattern=f"^{SHOW_TRAFFIC}$"),
                CallbackQueryHandler(handle_account_action, pattern=f"^{ACTION_PREFIX}"),
                CallbackQueryHandler(back_to_accounts_list, pattern=f"^{BACK_TO_LIST}$"),
                CallbackQueryHandler(cancel, pattern="^cancel$")
            ],
            FREEZE_ACCOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_freeze_input),
                CallbackQueryHandler(show_account_details, pattern=f"^{BACK_TO_DETAILS}$")
            ],
            ADD_NOTE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_note_input),
                CallbackQueryHandler(show_account_details, pattern=f"^{BACK_TO_DETAILS}$")
            ],
            CHANGE_PROTOCOL: [
                CallbackQueryHandler(handle_protocol_location_selection)
            ],
            ACCOUNT_ACTIONS: [
                CallbackQueryHandler(show_account_details, pattern=f"^{BACK_TO_DETAILS}$")
            ]
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            MessageHandler(filters.Regex("^انصراف$"), cancel)
        ],
        name="my_accounts_conversation",
        persistent=False
    ) 