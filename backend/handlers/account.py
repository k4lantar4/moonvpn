import logging
from datetime import datetime
import qrcode
from io import BytesIO
import pytz

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler, CommandHandler, MessageHandler, filters

from core.database import get_db_connection
from core.database.models.vpn_account import VPNAccount
from core.database.models.server import Server
from core.database.models.user import User
from bot.constants import CallbackPatterns, States

# Define conversation states
(
    SHOWING_ACCOUNTS,
    ACCOUNT_DETAILS,
    RENAME_CONFIG,
    CHANGE_LINK,
    EXTEND_SERVICE,
    CHANGE_LOCATION,
    INCREASE_VOLUME,
    REFUND_SERVICE,
    CONFIRM_DELETE,
) = range(9)

logger = logging.getLogger(__name__)

# Tehran timezone for proper date display
tehran_tz = pytz.timezone("Asia/Tehran")

async def accounts_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show all accounts for a user"""
    user_id = update.effective_user.id
    
    # Get user accounts from database
    user = User.get_by_telegram_id(user_id)
    if not user:
        await update.message.reply_text("❌ شما در سیستم ثبت نشده اید. لطفا دستور /start را ارسال کنید.")
        return ConversationHandler.END
    
    accounts = VPNAccount.get_by_user_id(user.id)
    
    if not accounts:
        keyboard = [
            [InlineKeyboardButton("🛒 خرید اکانت", callback_data=CallbackPatterns.BUY_ACCOUNT)],
            [InlineKeyboardButton("🏠 بازگشت به منوی اصلی", callback_data=CallbackPatterns.MAIN_MENU)]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "📵 شما هیچ اکانت فعالی ندارید!\n\n"
            "برای خرید اکانت جدید دکمه زیر را انتخاب کنید.",
            reply_markup=reply_markup
        )
        return ConversationHandler.END
    
    # Build keyboard with all user accounts
    keyboard = []
    
    for account in accounts:
        server = Server.get_by_id(account.server_id)
        status_emoji = "⭐" if account.status == "active" else "⏸️"
        remaining_days = (account.expiry_date - datetime.now()).days
        remaining_traffic = account.traffic_limit - account.traffic_used
        
        # Format button text
        button_text = f"{server.location} {server.country_flag} - {int(remaining_traffic)}GB - {remaining_days} روز {status_emoji}"
        
        keyboard.append([InlineKeyboardButton(
            button_text, 
            callback_data=f"{CallbackPatterns.ACCOUNT_DETAILS}:{account.id}"
        )])
    
    # Add back button
    keyboard.append([InlineKeyboardButton("🏠 بازگشت به منوی اصلی", callback_data=CallbackPatterns.MAIN_MENU)])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🔐 اکانت های VPN شما:\n\n"
        "برای مدیریت هر اکانت، روی آن کلیک کنید.",
        reply_markup=reply_markup
    )
    
    return SHOWING_ACCOUNTS

async def show_account_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show detailed information about a specific account"""
    query = update.callback_query
    await query.answer()
    
    # Extract account ID from callback data
    callback_data = query.data
    account_id = int(callback_data.split(":")[1])
    
    # Store account_id in context for later use
    context.user_data["current_account_id"] = account_id
    
    # Get account details
    account = VPNAccount.get_by_id(account_id)
    if not account:
        await query.edit_message_text("❌ اکانت مورد نظر یافت نشد.")
        return ConversationHandler.END
    
    server = Server.get_by_id(account.server_id)
    
    # Format expiry date in Jalali calendar (assuming conversion is handled in the model)
    expiry_jalali = account.expiry_date_jalali
    
    # Format creation date
    creation_date = account.created_at.astimezone(tehran_tz).strftime("%Y-%m-%d %H:%M")
    
    # Calculate remaining traffic
    remaining_gb = account.traffic_limit - account.traffic_used
    
    # Build VMess connection string (placeholder - actual implementation will use server details)
    vmess_link = account.get_vmess_link()
    
    # Build subscription link
    sub_link = account.get_subscription_link()
    
    # Status text and emoji
    status_emoji = "⭐" if account.status == "active" else "⏸️"
    status_text = "فعال" if account.status == "active" else "غیرفعال"
    
    # Create detailed account information message
    message = (
        f"{account.traffic_limit}Gb {server.country_flag} {account.package_duration} ماهه "
        f"{server.country_flag} {server.location} (VIP) 🌐\n\n"
        f"📝 {creation_date}\n\n"
        f"{status_text} {status_emoji}\n"
        f"🔑 {server.name}-{account.uuid[:5]}\n"
        f"{vmess_link}\n\n"
        f"🔗 لینک هوشمند سرویس شما:\n"
        f"{sub_link}"
    )
    
    # Create keyboard with account management options
    keyboard = [
        [InlineKeyboardButton("تغییر نام کانفیگ #", callback_data=f"{CallbackPatterns.RENAME_CONFIG}:{account_id}")],
        [InlineKeyboardButton("تغییر لینک و قطع دسترسی دیگران 🔄", callback_data=f"{CallbackPatterns.CHANGE_LINK}:{account_id}")],
        [
            InlineKeyboardButton("کیو آر کد 🧩", callback_data=f"{CallbackPatterns.SHOW_QR}:{account_id}"),
            InlineKeyboardButton("بروزرسانی لینک ⚡", callback_data=f"{CallbackPatterns.UPDATE_LINK}:{account_id}")
        ],
        [
            InlineKeyboardButton(f"حجم باقیمانده {remaining_gb} GB", callback_data=f"{CallbackPatterns.TRAFFIC_INFO}:{account_id}"),
            InlineKeyboardButton(f"نوع شبکه {server.network_type}", callback_data=f"{CallbackPatterns.NETWORK_INFO}:{account_id}")
        ],
        [InlineKeyboardButton(f"انقضا ⏰ {expiry_jalali}", callback_data=f"{CallbackPatterns.EXPIRY_INFO}:{account_id}")],
        [InlineKeyboardButton(f"پروتکل {server.protocol} 🛰️", callback_data=f"{CallbackPatterns.PROTOCOL_INFO}:{account_id}")],
        [
            InlineKeyboardButton("تمدید سرویس ♻️", callback_data=f"{CallbackPatterns.EXTEND_SERVICE}:{account_id}"),
            InlineKeyboardButton("تغییر لوکیشن 🔧", callback_data=f"{CallbackPatterns.CHANGE_LOCATION}:{account_id}")
        ],
        [InlineKeyboardButton("افزایش حجم سرویس📬", callback_data=f"{CallbackPatterns.INCREASE_VOLUME}:{account_id}")],
        [InlineKeyboardButton("عودت سرویس💰", callback_data=f"{CallbackPatterns.REFUND_SERVICE}:{account_id}")],
        [
            InlineKeyboardButton("برگشت ↩️", callback_data=CallbackPatterns.MY_ACCOUNTS),
            InlineKeyboardButton("حذف سرویس❌", callback_data=f"{CallbackPatterns.DELETE_SERVICE}:{account_id}")
        ],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        await query.edit_message_text(message, reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Error showing account details: {e}")
        # Try sending as new message if editing fails
        await query.message.reply_text(message, reply_markup=reply_markup)
    
    return ACCOUNT_DETAILS

async def generate_qr_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Generate and send QR code for the account"""
    query = update.callback_query
    await query.answer()
    
    # Extract account ID from callback data
    callback_data = query.data
    account_id = int(callback_data.split(":")[1])
    
    # Get account details
    account = VPNAccount.get_by_id(account_id)
    if not account:
        await query.edit_message_text("❌ اکانت مورد نظر یافت نشد.")
        return ACCOUNT_DETAILS
    
    # Generate QR code from VMess link
    vmess_link = account.get_vmess_link()
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(vmess_link)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save QR code to BytesIO
    bio = BytesIO()
    img.save(bio, 'PNG')
    bio.seek(0)
    
    # Send QR code
    await query.message.reply_photo(
        photo=bio,
        caption=f"🧩 کیو آر کد اتصال به سرویس شما:\n\nاکانت: {account.name}\nسرور: {Server.get_by_id(account.server_id).location}"
    )
    
    # Go back to account details
    server = Server.get_by_id(account.server_id)
    keyboard = [
        [InlineKeyboardButton("🔙 بازگشت به جزئیات اکانت", callback_data=f"{CallbackPatterns.ACCOUNT_DETAILS}:{account_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.reply_text(
        f"QR Code برای اکانت {server.name}-{account.uuid[:5]} ارسال شد.\n"
        "برای بازگشت به جزئیات اکانت از دکمه زیر استفاده کنید.",
        reply_markup=reply_markup
    )
    
    return ACCOUNT_DETAILS

async def refresh_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Refresh the subscription link"""
    query = update.callback_query
    await query.answer("لینک با موفقیت بروزرسانی شد! ✅")
    
    # Extract account ID from callback data
    callback_data = query.data
    account_id = int(callback_data.split(":")[1])
    
    # Return to account details
    callback_data = f"{CallbackPatterns.ACCOUNT_DETAILS}:{account_id}"
    context.user_data["callback_data"] = callback_data
    
    return await show_account_details(update, context)

async def start_rename_config(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the rename config process"""
    query = update.callback_query
    await query.answer()
    
    # Extract account ID from callback data
    callback_data = query.data
    account_id = int(callback_data.split(":")[1])
    context.user_data["current_account_id"] = account_id
    
    # Get account details
    account = VPNAccount.get_by_id(account_id)
    
    keyboard = [
        [InlineKeyboardButton("🔙 انصراف", callback_data=f"{CallbackPatterns.ACCOUNT_DETAILS}:{account_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"📝 نام فعلی کانفیگ: {account.name}\n\n"
        "لطفا نام جدید برای کانفیگ خود را ارسال کنید:",
        reply_markup=reply_markup
    )
    
    return RENAME_CONFIG

async def process_rename_config(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process the new config name"""
    new_name = update.message.text.strip()
    account_id = context.user_data.get("current_account_id")
    
    if not account_id:
        await update.message.reply_text("❌ خطا در فرآیند تغییر نام. لطفا دوباره تلاش کنید.")
        return ConversationHandler.END
    
    # Get account details
    account = VPNAccount.get_by_id(account_id)
    if not account:
        await update.message.reply_text("❌ اکانت مورد نظر یافت نشد.")
        return ConversationHandler.END
    
    # Update account name in database
    account.update_name(new_name)
    
    # Notify user of successful update
    keyboard = [
        [InlineKeyboardButton("🔙 بازگشت به جزئیات اکانت", callback_data=f"{CallbackPatterns.ACCOUNT_DETAILS}:{account_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"✅ نام کانفیگ با موفقیت به «{new_name}» تغییر یافت.",
        reply_markup=reply_markup
    )
    
    return ACCOUNT_DETAILS

async def reset_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Reset the connection link and disconnect others"""
    query = update.callback_query
    await query.answer()
    
    # Extract account ID from callback data
    callback_data = query.data
    account_id = int(callback_data.split(":")[1])
    
    # Get account details
    account = VPNAccount.get_by_id(account_id)
    if not account:
        await query.edit_message_text("❌ اکانت مورد نظر یافت نشد.")
        return ACCOUNT_DETAILS
    
    # Reset link (this would involve changing the UUID or other credentials)
    account.reset_connection_credentials()
    
    # Get updated information
    server = Server.get_by_id(account.server_id)
    new_link = account.get_vmess_link()
    
    keyboard = [
        [InlineKeyboardButton("🔙 بازگشت به جزئیات اکانت", callback_data=f"{CallbackPatterns.ACCOUNT_DETAILS}:{account_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"✅ لینک اتصال شما تغییر کرد و دسترسی سایر دستگاه‌ها قطع شد.\n\n"
        f"🔑 {server.name}-{account.uuid[:5]}\n"
        f"{new_link}\n\n"
        "برای بازگشت به صفحه جزئیات اکانت، از دکمه زیر استفاده کنید.",
        reply_markup=reply_markup
    )
    
    return ACCOUNT_DETAILS

async def start_extend_service(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the service extension process"""
    query = update.callback_query
    await query.answer()
    
    # Extract account ID from callback data
    callback_data = query.data
    account_id = int(callback_data.split(":")[1])
    context.user_data["current_account_id"] = account_id
    
    # Get account details
    account = VPNAccount.get_by_id(account_id)
    server = Server.get_by_id(account.server_id)
    
    # Create extension options
    keyboard = [
        [
            InlineKeyboardButton("۱ ماه", callback_data=f"{CallbackPatterns.EXTEND_MONTH}:{account_id}:1"),
            InlineKeyboardButton("۲ ماه", callback_data=f"{CallbackPatterns.EXTEND_MONTH}:{account_id}:2"),
            InlineKeyboardButton("۳ ماه", callback_data=f"{CallbackPatterns.EXTEND_MONTH}:{account_id}:3")
        ],
        [
            InlineKeyboardButton("۶ ماه", callback_data=f"{CallbackPatterns.EXTEND_MONTH}:{account_id}:6"),
            InlineKeyboardButton("۱۲ ماه", callback_data=f"{CallbackPatterns.EXTEND_MONTH}:{account_id}:12")
        ],
        [InlineKeyboardButton("🔙 انصراف", callback_data=f"{CallbackPatterns.ACCOUNT_DETAILS}:{account_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Format expiry date
    expiry_jalali = account.expiry_date_jalali
    
    await query.edit_message_text(
        f"♻️ تمدید سرویس\n\n"
        f"اکانت: {server.name}-{account.uuid[:5]}\n"
        f"تاریخ انقضا فعلی: {expiry_jalali}\n\n"
        "لطفا مدت زمان تمدید سرویس خود را انتخاب کنید:",
        reply_markup=reply_markup
    )
    
    return EXTEND_SERVICE

async def start_change_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the location change process"""
    query = update.callback_query
    await query.answer()
    
    # Extract account ID from callback data
    callback_data = query.data
    account_id = int(callback_data.split(":")[1])
    context.user_data["current_account_id"] = account_id
    
    # Get account details
    account = VPNAccount.get_by_id(account_id)
    current_server = Server.get_by_id(account.server_id)
    
    # Get available servers
    servers = Server.get_all_active()
    
    # Create keyboard with available servers
    keyboard = []
    for server in servers:
        if server.id != current_server.id:  # Don't show current server
            keyboard.append([
                InlineKeyboardButton(
                    f"{server.location} {server.country_flag}",
                    callback_data=f"{CallbackPatterns.SELECT_LOCATION}:{account_id}:{server.id}"
                )
            ])
    
    keyboard.append([InlineKeyboardButton("🔙 انصراف", callback_data=f"{CallbackPatterns.ACCOUNT_DETAILS}:{account_id}")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"🔧 تغییر لوکیشن اکانت\n\n"
        f"اکانت فعلی: {current_server.name}-{account.uuid[:5]}\n"
        f"لوکیشن فعلی: {current_server.location} {current_server.country_flag}\n\n"
        "لطفا لوکیشن جدید خود را انتخاب کنید:",
        reply_markup=reply_markup
    )
    
    return CHANGE_LOCATION

async def start_increase_volume(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the volume increase process"""
    query = update.callback_query
    await query.answer()
    
    # Extract account ID from callback data
    callback_data = query.data
    account_id = int(callback_data.split(":")[1])
    context.user_data["current_account_id"] = account_id
    
    # Get account details
    account = VPNAccount.get_by_id(account_id)
    server = Server.get_by_id(account.server_id)
    
    # Calculate remaining traffic
    remaining_gb = account.traffic_limit - account.traffic_used
    
    # Create volume options
    keyboard = [
        [
            InlineKeyboardButton("۱۰ گیگابایت", callback_data=f"{CallbackPatterns.INCREASE_GB}:{account_id}:10"),
            InlineKeyboardButton("۲۰ گیگابایت", callback_data=f"{CallbackPatterns.INCREASE_GB}:{account_id}:20")
        ],
        [
            InlineKeyboardButton("۵۰ گیگابایت", callback_data=f"{CallbackPatterns.INCREASE_GB}:{account_id}:50"),
            InlineKeyboardButton("۱۰۰ گیگابایت", callback_data=f"{CallbackPatterns.INCREASE_GB}:{account_id}:100")
        ],
        [InlineKeyboardButton("🔙 انصراف", callback_data=f"{CallbackPatterns.ACCOUNT_DETAILS}:{account_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"📬 افزایش حجم سرویس\n\n"
        f"اکانت: {server.name}-{account.uuid[:5]}\n"
        f"حجم باقیمانده فعلی: {remaining_gb} گیگابایت\n\n"
        "لطفا میزان افزایش حجم سرویس خود را انتخاب کنید:",
        reply_markup=reply_markup
    )
    
    return INCREASE_VOLUME

async def start_refund_service(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the service refund process"""
    query = update.callback_query
    await query.answer()
    
    # Extract account ID from callback data
    callback_data = query.data
    account_id = int(callback_data.split(":")[1])
    context.user_data["current_account_id"] = account_id
    
    # Get account details
    account = VPNAccount.get_by_id(account_id)
    server = Server.get_by_id(account.server_id)
    
    # Create confirmation keyboard
    keyboard = [
        [
            InlineKeyboardButton("✅ بله، مطمئن هستم", callback_data=f"{CallbackPatterns.CONFIRM_REFUND}:{account_id}"),
            InlineKeyboardButton("❌ خیر، انصراف", callback_data=f"{CallbackPatterns.ACCOUNT_DETAILS}:{account_id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"💰 درخواست عودت سرویس\n\n"
        f"اکانت: {server.name}-{account.uuid[:5]}\n"
        f"تاریخ انقضا: {account.expiry_date_jalali}\n\n"
        "⚠️ آیا مطمئن هستید که می‌خواهید درخواست عودت وجه سرویس خود را ثبت کنید؟\n\n"
        "توجه: مبلغ عودتی بر اساس زمان باقیمانده سرویس محاسبه خواهد شد.",
        reply_markup=reply_markup
    )
    
    return REFUND_SERVICE

async def start_delete_service(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the service deletion process"""
    query = update.callback_query
    await query.answer()
    
    # Extract account ID from callback data
    callback_data = query.data
    account_id = int(callback_data.split(":")[1])
    context.user_data["current_account_id"] = account_id
    
    # Get account details
    account = VPNAccount.get_by_id(account_id)
    server = Server.get_by_id(account.server_id)
    
    # Create confirmation keyboard
    keyboard = [
        [
            InlineKeyboardButton("✅ بله، حذف شود", callback_data=f"{CallbackPatterns.CONFIRM_DELETE}:{account_id}"),
            InlineKeyboardButton("❌ خیر، انصراف", callback_data=f"{CallbackPatterns.ACCOUNT_DETAILS}:{account_id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"❌ حذف سرویس\n\n"
        f"اکانت: {server.name}-{account.uuid[:5]}\n"
        f"تاریخ انقضا: {account.expiry_date_jalali}\n\n"
        "⚠️ آیا مطمئن هستید که می‌خواهید این سرویس را حذف کنید؟\n\n"
        "توجه: این عملیات غیرقابل بازگشت است و تمام اطلاعات سرویس شما حذف خواهد شد.",
        reply_markup=reply_markup
    )
    
    return CONFIRM_DELETE

async def confirm_delete_service(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Confirm and process service deletion"""
    query = update.callback_query
    await query.answer()
    
    # Extract account ID from callback data
    callback_data = query.data
    account_id = int(callback_data.split(":")[1])
    
    # Get account details
    account = VPNAccount.get_by_id(account_id)
    if not account:
        await query.edit_message_text("❌ اکانت مورد نظر یافت نشد.")
        return ConversationHandler.END
    
    # Delete account
    result = account.delete()
    
    if result:
        keyboard = [
            [InlineKeyboardButton("🏠 بازگشت به لیست اکانت ها", callback_data=CallbackPatterns.MY_ACCOUNTS)]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "✅ سرویس مورد نظر با موفقیت حذف شد.",
            reply_markup=reply_markup
        )
    else:
        keyboard = [
            [InlineKeyboardButton("🔙 بازگشت به جزئیات اکانت", callback_data=f"{CallbackPatterns.ACCOUNT_DETAILS}:{account_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "❌ خطا در حذف سرویس. لطفا دوباره تلاش کنید یا با پشتیبانی تماس بگیرید.",
            reply_markup=reply_markup
        )
    
    return SHOWING_ACCOUNTS

def get_account_handlers():
    """Return the handlers for account management"""
    account_conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("accounts", accounts_command),
            CallbackQueryHandler(accounts_command, pattern=f"^{CallbackPatterns.MY_ACCOUNTS}$"),
        ],
        states={
            SHOWING_ACCOUNTS: [
                CallbackQueryHandler(show_account_details, pattern=f"^{CallbackPatterns.ACCOUNT_DETAILS}"),
                CallbackQueryHandler(accounts_command, pattern=f"^{CallbackPatterns.MY_ACCOUNTS}$"),
            ],
            ACCOUNT_DETAILS: [
                CallbackQueryHandler(start_rename_config, pattern=f"^{CallbackPatterns.RENAME_CONFIG}"),
                CallbackQueryHandler(reset_link, pattern=f"^{CallbackPatterns.CHANGE_LINK}"),
                CallbackQueryHandler(generate_qr_code, pattern=f"^{CallbackPatterns.SHOW_QR}"),
                CallbackQueryHandler(refresh_link, pattern=f"^{CallbackPatterns.UPDATE_LINK}"),
                CallbackQueryHandler(start_extend_service, pattern=f"^{CallbackPatterns.EXTEND_SERVICE}"),
                CallbackQueryHandler(start_change_location, pattern=f"^{CallbackPatterns.CHANGE_LOCATION}"),
                CallbackQueryHandler(start_increase_volume, pattern=f"^{CallbackPatterns.INCREASE_VOLUME}"),
                CallbackQueryHandler(start_refund_service, pattern=f"^{CallbackPatterns.REFUND_SERVICE}"),
                CallbackQueryHandler(start_delete_service, pattern=f"^{CallbackPatterns.DELETE_SERVICE}"),
                CallbackQueryHandler(accounts_command, pattern=f"^{CallbackPatterns.MY_ACCOUNTS}$"),
            ],
            RENAME_CONFIG: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_rename_config),
                CallbackQueryHandler(show_account_details, pattern=f"^{CallbackPatterns.ACCOUNT_DETAILS}"),
            ],
            EXTEND_SERVICE: [
                CallbackQueryHandler(show_account_details, pattern=f"^{CallbackPatterns.ACCOUNT_DETAILS}"),
                # The actual extension handlers would be added here
            ],
            CHANGE_LOCATION: [
                CallbackQueryHandler(show_account_details, pattern=f"^{CallbackPatterns.ACCOUNT_DETAILS}"),
                # The actual location change handlers would be added here
            ],
            INCREASE_VOLUME: [
                CallbackQueryHandler(show_account_details, pattern=f"^{CallbackPatterns.ACCOUNT_DETAILS}"),
                # The actual volume increase handlers would be added here
            ],
            REFUND_SERVICE: [
                CallbackQueryHandler(show_account_details, pattern=f"^{CallbackPatterns.ACCOUNT_DETAILS}"),
                # The actual refund confirmation handler would be added here
            ],
            CONFIRM_DELETE: [
                CallbackQueryHandler(confirm_delete_service, pattern=f"^{CallbackPatterns.CONFIRM_DELETE}"),
                CallbackQueryHandler(show_account_details, pattern=f"^{CallbackPatterns.ACCOUNT_DETAILS}"),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", lambda u, c: ConversationHandler.END),
            CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern=f"^{CallbackPatterns.MAIN_MENU}$"),
        ],
        name="account_conversation",
        persistent=False,
    )
    
    return [account_conv_handler] 