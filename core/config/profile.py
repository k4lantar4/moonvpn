"""
Profile management handler for the V2Ray Telegram bot.

This module implements handlers for user profile management including:
- Viewing profile information
- Updating personal details
- Managing notification preferences
- Viewing account history
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    CommandHandler,
)
from telegram.constants import ParseMode

from api_client import (
    get_user_profile,
    update_user_profile,
    get_user_accounts,
    get_user_payments,
)
from core.utils.helpers import require_auth
from bot.constants import (
    # Conversation states
    SELECTING_FEATURE,
    SELECTING_ACTION,
    ENTERING_DETAILS,
    TYPING_NAME,
    TYPING_EMAIL,
    TYPING_PHONE,
    END,
    
    # Callback data patterns
    PROFILE_CB,
    VIEW_PROFILE_CB,
    EDIT_PROFILE_CB,
    TRANSACTIONS_CB,
    EDIT_NAME,
    EDIT_EMAIL,
    EDIT_PHONE,
    EDIT_PASSWORD,
    ACCOUNTS_HISTORY,
    PAYMENTS_HISTORY,
    NOTIFICATIONS_CB,
    BACK_CB,
)
from .start import start_command, back_to_main

from django.utils import timezone
from django.db.models import Sum
from django.utils.translation import gettext as _

from core.utils.formatting import format_bytes, format_currency
from keyboards.profile import (
    get_profile_keyboard,
    get_wallet_keyboard,
    get_subscription_keyboard,
    get_referral_keyboard,
)
from subscriptions.models import UserSubscription, UserWallet, WalletTransaction

import pyotp
import qrcode
from io import BytesIO

logger = logging.getLogger(__name__)

# Conversation states
PROFILE_MENU, WALLET_MENU, SUBSCRIPTION_MENU, REFERRAL_MENU, SETTINGS_MENU = range(5)
ADDING_FUNDS, TRANSFER_AMOUNT, TRANSFER_USER, BUYING_PLAN = range(5, 9)
ENTERING_2FA_CODE = 10

# Callback data
PROFILE_CB = "profile"
EDIT_NAME_CB = "edit_name"
EDIT_EMAIL_CB = "edit_email"
EDIT_PHONE_CB = "edit_phone"
BACK_TO_MENU_CB = "back_to_menu"
WALLET_CB = "wallet"
SUBSCRIPTIONS_CB = "subscriptions"
REFERRALS_CB = "referrals"
SETTINGS_CB = "settings"
MAIN_MENU_CB = "main_menu"
ADD_FUNDS_CB = "add_funds"
TRANSFER_CB = "transfer"
WALLET_STATS_CB = "wallet_stats"
WALLET_HISTORY_CB = "wallet_history"
BUY_PLAN_CB = "buy_plan"
RENEW_PLAN_CB = "renew_plan"
USAGE_STATS_CB = "usage_stats"
SUB_HISTORY_CB = "sub_history"
REF_STATS_CB = "ref_stats"
REF_HISTORY_CB = "ref_history"
REF_REWARDS_CB = "ref_rewards"
REF_SHARE_CB = "ref_share"

# Profile image URL
PROFILE_IMAGE = "https://example.com/path/to/profile_image.jpg"  # Replace with actual image URL or file_id

# States for the profile conversation
(
    PROFILE_VIEWING,
    EDITING_NAME,
    EDITING_EMAIL,
    EDITING_PHONE,
    SETTING_PASSWORD,
) = range(5)

@require_auth
async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show user profile information."""
    user = update.effective_user
    message = update.message or update.callback_query.message
    
    # Get user data from database
    db_user = User.get_by_telegram_id(user.id)
    
    if not db_user:
        # Create user if not exists
        db_user = User.create(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        logger.info(f"Created new user profile for: {user.id} - @{user.username}")
    
    # Extract user data
    user_data = {
        "telegram_id": db_user.telegram_id,
        "username": db_user.username or "-",
        "first_name": db_user.first_name or "-",
        "last_name": db_user.last_name or "-",
        "phone": db_user.phone or "-",
        "email": db_user.email or "-",
        "join_date": db_user.created_at.strftime("%Y-%m-%d") if hasattr(db_user, 'created_at') else "-",
        "is_admin": "✅" if db_user.is_admin else "❌"
    }
    
    # Create profile text
    profile_text = (
        f"👤 <b>پروفایل کاربری</b>\n\n"
        f"🆔 شناسه تلگرام: <code>{user_data['telegram_id']}</code>\n"
        f"👤 نام کاربری: @{user_data['username']}\n"
        f"📝 نام: {user_data['first_name']}\n"
        f"📝 نام خانوادگی: {user_data['last_name']}\n"
        f"📧 ایمیل: {user_data['email']}\n"
        f"📱 شماره تماس: {user_data['phone']}\n"
        f"📅 تاریخ عضویت: {user_data['join_date']}\n"
        f"👨‍💼 مدیر: {user_data['is_admin']}\n\n"
        f"برای ویرایش هر یک از اطلاعات، گزینه مربوطه را انتخاب کنید:"
    )
    
    # Create keyboard
    keyboard = [
        [
            InlineKeyboardButton("📝 ویرایش نام", callback_data=f"{CallbackPatterns.SETTINGS}_edit_name"),
            InlineKeyboardButton("📧 ویرایش ایمیل", callback_data=f"{CallbackPatterns.SETTINGS}_edit_email")
        ],
        [
            InlineKeyboardButton("📱 ویرایش شماره تماس", callback_data=f"{CallbackPatterns.SETTINGS}_edit_phone"),
            InlineKeyboardButton("🔐 تغییر رمز عبور", callback_data=f"{CallbackPatterns.SETTINGS}_edit_password")
        ],
        [
            InlineKeyboardButton("🔄 به‌روزرسانی اطلاعات", callback_data=f"{CallbackPatterns.SETTINGS}_refresh"),
            InlineKeyboardButton("📊 آمار حساب", callback_data=f"{CallbackPatterns.SETTINGS}_stats")
        ],
        [InlineKeyboardButton("🔙 بازگشت به تنظیمات", callback_data=CallbackPatterns.SETTINGS)]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send or edit message
    try:
        if update.callback_query:
            await update.callback_query.answer()
            
            if hasattr(update.callback_query.message, 'photo'):
                await update.callback_query.edit_message_caption(
                    caption=profile_text,
                    reply_markup=reply_markup,
                    parse_mode="HTML"
                )
            else:
                await update.callback_query.edit_message_text(
                    text=profile_text,
                    reply_markup=reply_markup,
                    parse_mode="HTML"
                )
        else:
            try:
                await message.reply_photo(
                    photo=PROFILE_IMAGE,
                    caption=profile_text,
                    reply_markup=reply_markup,
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.error(f"Error sending profile with image: {e}")
                await message.reply_text(
                    text=profile_text,
                    reply_markup=reply_markup,
                    parse_mode="HTML"
                )
    except Exception as e:
        logger.error(f"Error in profile command: {e}")
    
    return PROFILE_VIEWING

async def profile_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle callbacks from profile page."""
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    action = callback_data.split("_")[1] if "_" in callback_data else ""
    
    if action == "edit_name":
        await query.edit_message_text(
            "📝 <b>ویرایش نام</b>\n\n"
            "لطفا نام جدید خود را وارد کنید:",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 لغو و بازگشت", callback_data=f"{CallbackPatterns.SETTINGS}_profile")
            ]]),
            parse_mode="HTML"
        )
        return EDITING_NAME
    
    elif action == "edit_email":
        await query.edit_message_text(
            "📧 <b>ویرایش ایمیل</b>\n\n"
            "لطفا ایمیل جدید خود را وارد کنید:",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 لغو و بازگشت", callback_data=f"{CallbackPatterns.SETTINGS}_profile")
            ]]),
            parse_mode="HTML"
        )
        return EDITING_EMAIL
    
    elif action == "edit_phone":
        await query.edit_message_text(
            "📱 <b>ویرایش شماره تماس</b>\n\n"
            "لطفا شماره تماس جدید خود را وارد کنید:\n"
            "مثال: 09123456789",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 لغو و بازگشت", callback_data=f"{CallbackPatterns.SETTINGS}_profile")
            ]]),
            parse_mode="HTML"
        )
        return EDITING_PHONE
    
    elif action == "edit_password":
        await query.edit_message_text(
            "🔐 <b>تغییر رمز عبور</b>\n\n"
            "لطفا رمز عبور جدید خود را وارد کنید:\n"
            "(حداقل 8 کاراکتر شامل حروف و اعداد)",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 لغو و بازگشت", callback_data=f"{CallbackPatterns.SETTINGS}_profile")
            ]]),
            parse_mode="HTML"
        )
        return SETTING_PASSWORD
    
    elif action == "refresh":
        # Refresh profile information
        return await profile_command(update, context)
    
    elif action == "stats":
        # Show account statistics
        return await show_account_stats(update, context)
    
    elif action == "profile":
        # Show profile
        return await profile_command(update, context)
    
    # Default - return to profile viewing
    return await profile_command(update, context)

async def save_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Save the new name provided by the user."""
    user = update.effective_user
    message = update.message.text
    
    # Validate input
    if len(message) < 2 or len(message) > 40:
        await update.message.reply_text(
            "❌ نام باید بین 2 تا 40 کاراکتر باشد. لطفا مجدد تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت به پروفایل", callback_data=f"{CallbackPatterns.SETTINGS}_profile")
            ]])
        )
        return EDITING_NAME
    
    # Split name and last name
    name_parts = message.split(maxsplit=1)
    first_name = name_parts[0]
    last_name = name_parts[1] if len(name_parts) > 1 else ""
    
    # Update user in database
    db_user = User.get_by_telegram_id(user.id)
    if db_user:
        db_user.update(first_name=first_name, last_name=last_name)
    
    # Confirm and return to profile
    await update.message.reply_text(
        "✅ نام شما با موفقیت بروزرسانی شد.\n\n"
        "در حال بازگشت به پروفایل..."
    )
    
    # Return to profile after a short delay
    return await profile_command(update, context)

async def save_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Save the new email provided by the user."""
    user = update.effective_user
    message = update.message.text
    
    # Simple email validation
    if '@' not in message or '.' not in message or len(message) < 5:
        await update.message.reply_text(
            "❌ لطفا یک ایمیل معتبر وارد کنید.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت به پروفایل", callback_data=f"{CallbackPatterns.SETTINGS}_profile")
            ]])
        )
        return EDITING_EMAIL
    
    # Update user in database
    db_user = User.get_by_telegram_id(user.id)
    if db_user:
        db_user.update(email=message)
    
    # Confirm and return to profile
    await update.message.reply_text(
        "✅ ایمیل شما با موفقیت بروزرسانی شد.\n\n"
        "در حال بازگشت به پروفایل..."
    )
    
    # Return to profile
    return await profile_command(update, context)

async def save_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Save the new phone number provided by the user."""
    user = update.effective_user
    message = update.message.text
    
    # Simple phone validation - assuming Persian phone numbers
    if not message.isdigit() or len(message) != 11 or not message.startswith("09"):
        await update.message.reply_text(
            "❌ لطفا یک شماره تلفن معتبر ایرانی وارد کنید (مثلا: 09123456789).",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت به پروفایل", callback_data=f"{CallbackPatterns.SETTINGS}_profile")
            ]])
        )
        return EDITING_PHONE
    
    # Update user in database
    db_user = User.get_by_telegram_id(user.id)
    if db_user:
        db_user.update(phone=message)
    
    # Confirm and return to profile
    await update.message.reply_text(
        "✅ شماره تلفن شما با موفقیت بروزرسانی شد.\n\n"
        "در حال بازگشت به پروفایل..."
    )
    
    # Return to profile
    return await profile_command(update, context)

async def save_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Save the new password provided by the user."""
    user = update.effective_user
    message = update.message.text
    
    # Simple password validation
    if len(message) < 8:
        await update.message.reply_text(
            "❌ رمز عبور باید حداقل 8 کاراکتر باشد.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت به پروفایل", callback_data=f"{CallbackPatterns.SETTINGS}_profile")
            ]])
        )
        return SETTING_PASSWORD
    
    has_digit = any(char.isdigit() for char in message)
    has_letter = any(char.isalpha() for char in message)
    
    if not (has_digit and has_letter):
        await update.message.reply_text(
            "❌ رمز عبور باید شامل حداقل یک حرف و یک عدد باشد.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت به پروفایل", callback_data=f"{CallbackPatterns.SETTINGS}_profile")
            ]])
        )
        return SETTING_PASSWORD
    
    # Update user in database (in real implementation, you'd hash the password)
    db_user = User.get_by_telegram_id(user.id)
    if db_user:
        # In real implementation: db_user.update(password_hash=hash_password(message))
        # For demo purposes:
        db_user.update(password="*********")  # Placeholder
    
    # Confirm and return to profile
    await update.message.reply_text(
        "✅ رمز عبور شما با موفقیت بروزرسانی شد.\n\n"
        "در حال بازگشت به پروفایل..."
    )
    
    # Return to profile
    return await profile_command(update, context)

async def show_account_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show account usage statistics."""
    query = update.callback_query
    user = update.effective_user
    
    # Get user data and account statistics
    # In a real implementation, get actual statistics from database
    account_stats = {
        "active_accounts": 2,
        "total_accounts": 5,
        "total_traffic": 120,  # in GB
        "total_traffic_used": 45,  # in GB
        "total_payments": 350000,  # in currency (e.g., Toman)
        "referred_users": 3,
        "earnings": 75000,  # in currency
        "last_login": "2023-07-15 14:30",
    }
    
    # Create statistics message
    stats_text = (
        f"📊 <b>آمار حساب کاربری</b>\n\n"
        f"🔐 <b>اکانت‌ها:</b>\n"
        f"• اکانت‌های فعال: {account_stats['active_accounts']}/{account_stats['total_accounts']}\n"
        f"• ترافیک کل: {account_stats['total_traffic']} GB\n"
        f"• ترافیک مصرفی: {account_stats['total_traffic_used']} GB "
        f"({account_stats['total_traffic_used']/account_stats['total_traffic']*100:.1f}%)\n\n"
        f"💰 <b>مالی:</b>\n"
        f"• پرداخت‌های کل: {account_stats['total_payments']:,} تومان\n"
        f"• کاربران معرفی شده: {account_stats['referred_users']} نفر\n"
        f"• درآمد از معرفی: {account_stats['earnings']:,} تومان\n\n"
        f"🕒 <b>فعالیت:</b>\n"
        f"• آخرین ورود: {account_stats['last_login']}\n"
    )
    
    # Create keyboard
    keyboard = [
        [
            InlineKeyboardButton("📜 مشاهده سابقه پرداخت‌ها", callback_data=f"{CallbackPatterns.PAYMENT}_history"),
            InlineKeyboardButton("📈 نمودار مصرف", callback_data=f"{CallbackPatterns.CHECK_TRAFFIC}")
        ],
        [InlineKeyboardButton("🔙 بازگشت به پروفایل", callback_data=f"{CallbackPatterns.SETTINGS}_profile")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Edit message
    await query.edit_message_text(
        text=stats_text,
        reply_markup=reply_markup,
        parse_mode="HTML"
    )
    
    return PROFILE_VIEWING

def get_profile_handlers() -> List:
    """Return all handlers related to the profile feature."""
    
    profile_conversation = ConversationHandler(
        entry_points=[
            CommandHandler("profile", profile_command),
            CallbackQueryHandler(profile_callback, pattern=f"^{CallbackPatterns.SETTINGS}_profile$")
        ],
        states={
            PROFILE_VIEWING: [
                CallbackQueryHandler(profile_callback, pattern=f"^{CallbackPatterns.SETTINGS}_")
            ],
            EDITING_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, save_name),
                CallbackQueryHandler(profile_callback, pattern=f"^{CallbackPatterns.SETTINGS}_profile$")
            ],
            EDITING_EMAIL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, save_email),
                CallbackQueryHandler(profile_callback, pattern=f"^{CallbackPatterns.SETTINGS}_profile$")
            ],
            EDITING_PHONE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, save_phone),
                CallbackQueryHandler(profile_callback, pattern=f"^{CallbackPatterns.SETTINGS}_profile$")
            ],
            SETTING_PASSWORD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, save_password),
                CallbackQueryHandler(profile_callback, pattern=f"^{CallbackPatterns.SETTINGS}_profile$")
            ],
        },
        fallbacks=[
            CallbackQueryHandler(lambda u, c: States.SETTINGS_MAIN, pattern=f"^{CallbackPatterns.SETTINGS}$"),
            CommandHandler("start", lambda u, c: ConversationHandler.END)
        ],
        name="profile_conversation",
        persistent=False
    )
    
    return [profile_conversation]

async def wallet_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show wallet menu."""
    query = update.callback_query
    await query.answer()
    
    user = context.user_data["db_user"]
    wallet = user.wallet
    
    # Get recent transactions
    recent_transactions = wallet.transactions.all()[:5]
    
    message = _(
        "💰 *Your Wallet*\n\n"
        "Current Balance: {balance}\n"
        "Points: {points}\n"
        "Referral Earnings: {referral_earnings}\n\n"
        "Recent Transactions:\n"
    ).format(
        balance=format_currency(wallet.balance),
        points=wallet.points,
        referral_earnings=format_currency(wallet.total_referral_earnings)
    )
    
    for tx in recent_transactions:
        message += _(
            "• {type}: {amount} ({status})\n"
        ).format(
            type=tx.get_transaction_type_display(),
            amount=format_currency(tx.amount),
            status=tx.get_status_display()
        )
    
    keyboard = get_wallet_keyboard()
    
    await query.edit_message_text(
        message,
        reply_markup=keyboard,
        parse_mode=ParseMode.MARKDOWN
    )
    
    return WALLET_MENU

async def subscription_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show subscription menu."""
    query = update.callback_query
    await query.answer()
    
    user = context.user_data["db_user"]
    
    # Get all user subscriptions
    subscriptions = user.subscriptions.all().order_by("-created_at")[:5]
    
    message = _("📱 *Your Subscriptions*\n\n")
    
    for sub in subscriptions:
        message += _(
            "*{plan}*\n"
            "Status: {status}\n"
            "Traffic: {used}/{total} GB\n"
            "Valid until: {expires}\n\n"
        ).format(
            plan=sub.plan.name,
            status=sub.get_status_display(),
            used=format_bytes(sub.traffic_used_bytes, "gb"),
            total=sub.plan.traffic_limit_gb,
            expires=sub.end_date.strftime("%Y-%m-%d") if sub.end_date else "N/A"
        )
    
    keyboard = get_subscription_keyboard()
    
    await query.edit_message_text(
        message,
        reply_markup=keyboard,
        parse_mode=ParseMode.MARKDOWN
    )
    
    return SUBSCRIPTION_MENU

async def referral_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show referral menu."""
    query = update.callback_query
    await query.answer()
    
    user = context.user_data["db_user"]
    wallet = user.wallet
    
    # Get referral statistics
    referral_count = user.referrals.count()
    total_earnings = wallet.total_referral_earnings
    
    message = _(
        "👥 *Referral Program*\n\n"
        "Your Referral Code: `{code}`\n"
        "Total Referrals: {count}\n"
        "Total Earnings: {earnings}\n\n"
        "Share your referral code with friends and earn rewards when they subscribe!\n\n"
        "🔗 Referral Link:\n"
        "`https://t.me/{bot_username}?start={code}`"
    ).format(
        code=wallet.referral_code,
        count=referral_count,
        earnings=format_currency(total_earnings),
        bot_username=context.bot.username
    )
    
    keyboard = get_referral_keyboard()
    
    await query.edit_message_text(
        message,
        reply_markup=keyboard,
        parse_mode=ParseMode.MARKDOWN
    )
    
    return REFERRAL_MENU

async def back_to_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Return to profile menu."""
    query = update.callback_query
    await query.answer()
    
    user = context.user_data["db_user"]
    active_sub = user.subscriptions.filter(status="active").first()
    wallet = user.wallet
    
    message = _(
        "👤 *Your Profile*\n\n"
        "🆔 User ID: `{user_id}`\n"
        "📧 Email: {email}\n"
        "📅 Joined: {joined}\n\n"
        "💰 Wallet Balance: {balance}\n"
        "⭐️ Points: {points}\n"
        "👥 Referrals: {referral_count}\n\n"
    ).format(
        user_id=user.id,
        email=user.email or "Not set",
        joined=user.date_joined.strftime("%Y-%m-%d"),
        balance=format_currency(wallet.balance),
        points=wallet.points,
        referral_count=user.referrals.count()
    )
    
    if active_sub:
        message += _(
            "📱 Active Subscription:\n"
            "   • Plan: {plan}\n"
            "   • Expires: {expires}\n"
            "   • Traffic: {used}/{total} GB\n"
            "   • Connections: {connections}/{max_connections}\n"
        ).format(
            plan=active_sub.plan.name,
            expires=active_sub.end_date.strftime("%Y-%m-%d"),
            used=format_bytes(active_sub.traffic_used_bytes, "gb"),
            total=active_sub.plan.traffic_limit_gb,
            connections=active_sub.connections_count,
            max_connections=active_sub.plan.max_connections
        )
    else:
        message += _("\n❌ No active subscription")
    
    keyboard = get_profile_keyboard()
    
    await query.edit_message_text(
        message,
        reply_markup=keyboard,
        parse_mode=ParseMode.MARKDOWN
    )
    
    return PROFILE_MENU

async def add_funds(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle add funds request."""
    query = update.callback_query
    await query.answer()
    
    message = _(
        "💳 *Add Funds to Wallet*\n\n"
        "Please select the amount you want to add:\n\n"
        "• Minimum: 100,000 Toman\n"
        "• Maximum: 10,000,000 Toman\n\n"
        "Enter the amount in Toman:"
    )
    
    # Create inline keyboard with preset amounts
    keyboard = [
        [
            InlineKeyboardButton("100,000 تومان", callback_data="amount_100000"),
            InlineKeyboardButton("200,000 تومان", callback_data="amount_200000")
        ],
        [
            InlineKeyboardButton("500,000 تومان", callback_data="amount_500000"),
            InlineKeyboardButton("1,000,000 تومان", callback_data="amount_1000000")
        ],
        [
            InlineKeyboardButton(_("⬅️ Back"), callback_data="back")
        ]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )
    
    return ADDING_FUNDS

async def process_add_funds(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process the add funds amount."""
    query = update.callback_query
    if query:
        await query.answer()
        amount = int(query.data.split("_")[1])
    else:
        try:
            amount = int(update.message.text.replace(",", ""))
        except ValueError:
            await update.message.reply_text(
                _("❌ Please enter a valid number without any letters or special characters.")
            )
            return ADDING_FUNDS
    
    # Validate amount
    if amount < 100000:
        message = _("❌ Minimum amount is 100,000 Toman")
        if query:
            await query.edit_message_text(message)
        else:
            await update.message.reply_text(message)
        return ADDING_FUNDS
        
    if amount > 10000000:
        message = _("❌ Maximum amount is 10,000,000 Toman")
        if query:
            await query.edit_message_text(message)
        else:
            await update.message.reply_text(message)
        return ADDING_FUNDS
    
    # Create payment link
    user = context.user_data["db_user"]
    wallet = user.wallet
    
    # Create transaction
    transaction = WalletTransaction.objects.create(
        wallet=wallet,
        transaction_type="deposit",
        amount=amount,
        status="pending",
        description=_("Wallet deposit via payment gateway")
    )
    
    # TODO: Integrate with payment gateway
    payment_link = f"https://pay.example.com/{transaction.id}"
    
    message = _(
        "💳 *Payment Details*\n\n"
        "Amount: {amount}\n"
        "Transaction ID: `{tx_id}`\n\n"
        "Click the button below to proceed with payment:"
    ).format(
        amount=format_currency(amount, "IRR"),
        tx_id=transaction.id
    )
    
    keyboard = [
        [
            InlineKeyboardButton(_("💳 Pay Now"), url=payment_link)
        ],
        [
            InlineKeyboardButton(_("⬅️ Back to Wallet"), callback_data="wallet")
        ]
    ]
    
    if query:
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await update.message.reply_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
    
    return WALLET_MENU

async def transfer_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show transfer menu."""
    query = update.callback_query
    await query.answer()
    
    message = _(
        "🔄 *Transfer Funds*\n\n"
        "Enter the amount you want to transfer (in Toman):\n\n"
        "• Minimum: 10,000 Toman\n"
        "• Maximum: Your wallet balance\n"
        "• Fee: 0%"
    )
    
    keyboard = [
        [
            InlineKeyboardButton(_("⬅️ Back"), callback_data="back")
        ]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )
    
    return TRANSFER_AMOUNT

async def process_transfer_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process the transfer amount."""
    try:
        amount = int(update.message.text.replace(",", ""))
    except ValueError:
        await update.message.reply_text(
            _("❌ Please enter a valid number without any letters or special characters.")
        )
        return TRANSFER_AMOUNT
    
    user = context.user_data["db_user"]
    wallet = user.wallet
    
    # Validate amount
    if amount < 10000:
        await update.message.reply_text(_("❌ Minimum transfer amount is 10,000 Toman"))
        return TRANSFER_AMOUNT
        
    if amount > wallet.balance:
        await update.message.reply_text(_("❌ Insufficient balance"))
        return TRANSFER_AMOUNT
    
    # Store amount in context
    context.user_data["transfer_amount"] = amount
    
    message = _(
        "👤 *Enter Recipient*\n\n"
        "Please enter the Telegram ID or username of the recipient:"
    )
    
    keyboard = [
        [
            InlineKeyboardButton(_("⬅️ Back"), callback_data="back")
        ]
    ]
    
    await update.message.reply_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )
    
    return TRANSFER_USER

async def process_transfer_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process the transfer recipient."""
    recipient_id = update.message.text.strip()
    
    # TODO: Validate and get recipient user
    recipient = None
    
    if not recipient:
        await update.message.reply_text(_("❌ User not found"))
        return TRANSFER_USER
    
    amount = context.user_data["transfer_amount"]
    sender = context.user_data["db_user"]
    
    try:
        # Create transactions
        with transaction.atomic():
            # Debit sender
            WalletTransaction.objects.create(
                wallet=sender.wallet,
                transaction_type="withdrawal",
                amount=-amount,
                status="completed",
                description=_("Transfer to {recipient}").format(recipient=recipient.username)
            )
            sender.wallet.balance -= amount
            sender.wallet.save()
            
            # Credit recipient
            WalletTransaction.objects.create(
                wallet=recipient.wallet,
                transaction_type="deposit",
                amount=amount,
                status="completed",
                description=_("Transfer from {sender}").format(sender=sender.username)
            )
            recipient.wallet.balance += amount
            recipient.wallet.save()
            
        message = _(
            "✅ *Transfer Successful*\n\n"
            "Amount: {amount}\n"
            "To: {recipient}\n\n"
            "Your new balance: {balance}"
        ).format(
            amount=format_currency(amount, "IRR"),
            recipient=recipient.username,
            balance=format_currency(sender.wallet.balance, "IRR")
        )
        
    except Exception as e:
        logger.error(f"Transfer failed: {e}")
        message = _("❌ Transfer failed. Please try again later.")
    
    keyboard = [
        [
            InlineKeyboardButton(_("⬅️ Back to Wallet"), callback_data="wallet")
        ]
    ]
    
    await update.message.reply_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )
    
    # Clear transfer data
    if "transfer_amount" in context.user_data:
        del context.user_data["transfer_amount"]
    
    return WALLET_MENU

async def wallet_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show wallet statistics."""
    query = update.callback_query
    await query.answer()
    
    user = context.user_data["db_user"]
    wallet = user.wallet
    
    # Get transaction stats
    today = timezone.now().date()
    thirty_days_ago = today - timezone.timedelta(days=30)
    
    transactions = wallet.transactions.filter(
        created_at__date__gte=thirty_days_ago
    )
    
    deposits = transactions.filter(transaction_type="deposit")
    withdrawals = transactions.filter(transaction_type="withdrawal")
    
    total_deposits = deposits.aggregate(total=Sum("amount"))["total"] or 0
    total_withdrawals = abs(withdrawals.aggregate(total=Sum("amount"))["total"] or 0)
    
    message = _(
        "📊 *Wallet Statistics*\n\n"
        "*Last 30 Days:*\n"
        "• Total Deposits: {deposits}\n"
        "• Total Withdrawals: {withdrawals}\n"
        "• Number of Transactions: {tx_count}\n\n"
        "*Current Status:*\n"
        "• Balance: {balance}\n"
        "• Points: {points}\n"
        "• Referral Earnings: {ref_earnings}"
    ).format(
        deposits=format_currency(total_deposits, "IRR"),
        withdrawals=format_currency(total_withdrawals, "IRR"),
        tx_count=transactions.count(),
        balance=format_currency(wallet.balance, "IRR"),
        points=format_number(wallet.points),
        ref_earnings=format_currency(wallet.total_referral_earnings, "IRR")
    )
    
    keyboard = [
        [
            InlineKeyboardButton(_("📜 View History"), callback_data="wallet_history")
        ],
        [
            InlineKeyboardButton(_("⬅️ Back"), callback_data="back")
        ]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )
    
    return WALLET_MENU

async def wallet_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show wallet transaction history."""
    query = update.callback_query
    await query.answer()
    
    user = context.user_data["db_user"]
    wallet = user.wallet
    
    # Get paginated transactions
    page = context.user_data.get("wallet_history_page", 1)
    per_page = 5
    
    transactions = wallet.transactions.all()
    total_pages = (transactions.count() + per_page - 1) // per_page
    
    start = (page - 1) * per_page
    end = start + per_page
    page_transactions = transactions[start:end]
    
    message = _(
        "📜 *Transaction History*\n\n"
        "Page {page} of {total_pages}\n\n"
    ).format(page=page, total_pages=total_pages)
    
    for tx in page_transactions:
        message += _(
            "*{date}*\n"
            "Type: {type}\n"
            "Amount: {amount}\n"
            "Status: {status}\n"
            "Description: {desc}\n\n"
        ).format(
            date=tx.created_at.strftime("%Y-%m-%d %H:%M"),
            type=tx.get_transaction_type_display(),
            amount=format_currency(tx.amount, "IRR"),
            status=tx.get_status_display(),
            desc=tx.description or "-"
        )
    
    # Create pagination keyboard
    keyboard = []
    
    if total_pages > 1:
        row = []
        if page > 1:
            row.append(InlineKeyboardButton("◀️", callback_data=f"wallet_history_{page-1}"))
        row.append(InlineKeyboardButton(f"{page}/{total_pages}", callback_data="noop"))
        if page < total_pages:
            row.append(InlineKeyboardButton("▶️", callback_data=f"wallet_history_{page+1}"))
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton(_("⬅️ Back"), callback_data="back")])
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )
    
    return WALLET_MENU

async def settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show settings menu."""
    query = update.callback_query
    await query.answer()
    
    user = context.user_data["db_user"]
    
    # Get user settings
    notification_settings = user.notification_settings
    language = user.language or "en"
    auto_renew = user.auto_renew
    
    message = _(
        "⚙️ *Settings*\n\n"
        "*Language:* {language}\n"
        "*Notifications:*\n"
        "• Account Expiry: {expiry}\n"
        "• Traffic Usage: {traffic}\n"
        "• Payments: {payments}\n"
        "• System Updates: {system}\n\n"
        "*Auto-Renewal:* {auto_renew}\n"
        "*Two-Factor Auth:* {2fa}\n"
    ).format(
        language=_("Persian") if language == "fa" else _("English"),
        expiry="✅" if notification_settings.get("expiry", True) else "❌",
        traffic="✅" if notification_settings.get("traffic", True) else "❌",
        payments="✅" if notification_settings.get("payments", True) else "❌",
        system="✅" if notification_settings.get("system", True) else "❌",
        auto_renew="✅" if auto_renew else "❌",
        _2fa="✅" if user.two_factor_enabled else "❌"
    )
    
    keyboard = [
        [
            InlineKeyboardButton(_("🌐 Language"), callback_data="language"),
            InlineKeyboardButton(_("🔔 Notifications"), callback_data="notifications")
        ],
        [
            InlineKeyboardButton(_("🔄 Auto-Renewal"), callback_data="auto_renew"),
            InlineKeyboardButton(_("🔐 Security"), callback_data="security")
        ],
        [
            InlineKeyboardButton(_("⬅️ Back"), callback_data="back")
        ]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )
    
    return SETTINGS_MENU

async def toggle_auto_renew(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Toggle auto-renewal setting."""
    query = update.callback_query
    await query.answer()
    
    user = context.user_data["db_user"]
    user.auto_renew = not user.auto_renew
    user.save()
    
    # Return to settings menu
    return await settings_menu(update, context)

async def security_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show security settings menu."""
    query = update.callback_query
    await query.answer()
    
    user = context.user_data["db_user"]
    
    message = _(
        "🔐 *Security Settings*\n\n"
        "*Two-Factor Authentication:* {2fa}\n"
        "*Active Sessions:* {sessions}\n"
        "*Last Login:* {last_login}\n"
    ).format(
        _2fa="✅" if user.two_factor_enabled else "❌",
        sessions=user.active_sessions.count(),
        last_login=user.last_login.strftime("%Y-%m-%d %H:%M") if user.last_login else "N/A"
    )
    
    keyboard = [
        [
            InlineKeyboardButton(
                _("Enable 2FA") if not user.two_factor_enabled else _("Disable 2FA"),
                callback_data="toggle_2fa"
            )
        ],
        [
            InlineKeyboardButton(_("🔄 Active Sessions"), callback_data="sessions"),
            InlineKeyboardButton(_("📱 Devices"), callback_data="devices")
        ],
        [
            InlineKeyboardButton(_("⬅️ Back"), callback_data="back")
        ]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )
    
    return SETTINGS_MENU

async def view_sessions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show active sessions."""
    query = update.callback_query
    await query.answer()
    
    user = context.user_data["db_user"]
    
    # Get paginated sessions
    page = context.user_data.get("sessions_page", 1)
    per_page = 5
    
    sessions = user.active_sessions.all().order_by("-last_activity")
    total_pages = (sessions.count() + per_page - 1) // per_page
    
    start = (page - 1) * per_page
    end = start + per_page
    page_sessions = sessions[start:end]
    
    message = _(
        "🔄 *Active Sessions*\n\n"
        "Page {page} of {total_pages}\n\n"
    ).format(page=page, total_pages=total_pages)
    
    for session in page_sessions:
        message += _(
            "*{device}*\n"
            "IP: {ip}\n"
            "Location: {location}\n"
            "Last Activity: {last_activity}\n"
            "Status: {status}\n\n"
        ).format(
            device=session.device_info or _("Unknown Device"),
            ip=session.ip_address,
            location=session.location or _("Unknown"),
            last_activity=session.last_activity.strftime("%Y-%m-%d %H:%M"),
            status=_("Current Session") if session.is_current else _("Active")
        )
    
    # Create pagination keyboard
    keyboard = []
    
    if total_pages > 1:
        row = []
        if page > 1:
            row.append(InlineKeyboardButton("◀️", callback_data=f"sessions_{page-1}"))
        row.append(InlineKeyboardButton(f"{page}/{total_pages}", callback_data="noop"))
        if page < total_pages:
            row.append(InlineKeyboardButton("▶️", callback_data=f"sessions_{page+1}"))
        keyboard.append(row)
    
    # Add action buttons
    keyboard.append([
        InlineKeyboardButton(_("🚫 Revoke All"), callback_data="revoke_all"),
        InlineKeyboardButton(_("⬅️ Back"), callback_data="back")
    ])
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )
    
    return SETTINGS_MENU

async def view_devices(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show registered devices."""
    query = update.callback_query
    await query.answer()
    
    user = context.user_data["db_user"]
    
    # Get paginated devices
    page = context.user_data.get("devices_page", 1)
    per_page = 5
    
    devices = user.registered_devices.all().order_by("-last_used")
    total_pages = (devices.count() + per_page - 1) // per_page
    
    start = (page - 1) * per_page
    end = start + per_page
    page_devices = devices[start:end]
    
    message = _(
        "📱 *Registered Devices*\n\n"
        "Page {page} of {total_pages}\n\n"
    ).format(page=page, total_pages=total_pages)
    
    for device in page_devices:
        message += _(
            "*{name}*\n"
            "Type: {type}\n"
            "Last Used: {last_used}\n"
            "Status: {status}\n\n"
        ).format(
            name=device.name or _("Unnamed Device"),
            type=device.get_type_display(),
            last_used=device.last_used.strftime("%Y-%m-%d %H:%M"),
            status=_("Active") if device.is_active else _("Inactive")
        )
    
    # Create pagination keyboard
    keyboard = []
    
    if total_pages > 1:
        row = []
        if page > 1:
            row.append(InlineKeyboardButton("◀️", callback_data=f"devices_{page-1}"))
        row.append(InlineKeyboardButton(f"{page}/{total_pages}", callback_data="noop"))
        if page < total_pages:
            row.append(InlineKeyboardButton("▶️", callback_data=f"devices_{page+1}"))
        keyboard.append(row)
    
    # Add action buttons
    keyboard.append([
        InlineKeyboardButton(_("➕ Add Device"), callback_data="add_device"),
        InlineKeyboardButton(_("⬅️ Back"), callback_data="back")
    ])
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )
    
    return SETTINGS_MENU

async def revoke_all_sessions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Revoke all active sessions except current one."""
    query = update.callback_query
    await query.answer()
    
    user = context.user_data["db_user"]
    
    # Get current session
    current_session = user.active_sessions.filter(is_current=True).first()
    
    # Revoke all other sessions
    user.active_sessions.exclude(id=current_session.id).delete()
    
    await query.answer(_("✅ All other sessions have been revoked"), show_alert=True)
    
    # Return to sessions view
    return await view_sessions(update, context)

async def toggle_2fa(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Toggle two-factor authentication."""
    query = update.callback_query
    await query.answer()
    
    user = context.user_data["db_user"]
    
    if user.two_factor_enabled:
        # Disable 2FA
        user.two_factor_enabled = False
        user.two_factor_secret = None
        user.save()
        
        await query.answer(_("✅ Two-factor authentication has been disabled"), show_alert=True)
        return await security_settings(update, context)
    else:
        # Enable 2FA - Show QR code and setup instructions
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        
        # Generate QR code
        provisioning_uri = totp.provisioning_uri(
            user.email or str(user.telegram_id),
            issuer_name="MoonVPN"
        )
        
        message = _(
            "🔐 *Enable Two-Factor Authentication*\n\n"
            "1. Install Google Authenticator or a similar app\n"
            "2. Scan the QR code or enter the code manually\n"
            "3. Enter the 6-digit code to verify\n\n"
            "*Manual Entry Code:*\n"
            "`{secret}`\n\n"
            "Please enter the 6-digit code from your authenticator app:"
        ).format(secret=secret)
        
        # Store secret temporarily
        context.user_data["temp_2fa_secret"] = secret
        
        keyboard = [
            [
                InlineKeyboardButton(_("❌ Cancel"), callback_data="back")
            ]
        ]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Send QR code as a separate message
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        bio = BytesIO()
        img.save(bio, "PNG")
        bio.seek(0)
        
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=bio,
            caption=_("Scan this QR code with your authenticator app")
        )
        
        return ENTERING_2FA_CODE

async def verify_2fa_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Verify the 2FA code entered by the user."""
    if not update.message or not update.message.text:
        return ENTERING_2FA_CODE
    
    code = update.message.text.strip()
    user = context.user_data["db_user"]
    secret = context.user_data.get("temp_2fa_secret")
    
    if not secret:
        await update.message.reply_text(_("❌ Setup process expired. Please try again."))
        return await security_settings(update, context)
    
    # Verify code
    totp = pyotp.TOTP(secret)
    if totp.verify(code):
        # Enable 2FA
        user.two_factor_enabled = True
        user.two_factor_secret = secret
        user.save()
        
        # Clear temporary data
        del context.user_data["temp_2fa_secret"]
        
        await update.message.reply_text(_("✅ Two-factor authentication has been enabled"))
        return await security_settings(update, context)
    else:
        await update.message.reply_text(
            _("❌ Invalid code. Please try again or click Cancel to abort.")
        )
        return ENTERING_2FA_CODE

async def buy_plan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle buy plan callback."""
    query = update.callback_query
    await query.answer()
    
    # This is a placeholder function
    await query.message.reply_text(_("This feature is not implemented yet."))
    return SUBSCRIPTION_MENU

async def renew_plan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle renew plan callback."""
    query = update.callback_query
    await query.answer()
    
    # This is a placeholder function
    await query.message.reply_text(_("This feature is not implemented yet."))
    return SUBSCRIPTION_MENU

async def usage_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle usage stats callback."""
    query = update.callback_query
    await query.answer()
    
    # This is a placeholder function
    await query.message.reply_text(_("This feature is not implemented yet."))
    return SUBSCRIPTION_MENU

async def sub_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle subscription history callback."""
    query = update.callback_query
    await query.answer()
    
    # This is a placeholder function
    await query.message.reply_text(_("This feature is not implemented yet."))
    return SUBSCRIPTION_MENU

async def ref_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle referral stats callback."""
    query = update.callback_query
    await query.answer()
    
    # This is a placeholder function
    await query.message.reply_text(_("This feature is not implemented yet."))
    return REFERRAL_MENU

async def ref_share(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle referral share callback."""
    query = update.callback_query
    await query.answer()
    
    # This is a placeholder function
    await query.message.reply_text(_("This feature is not implemented yet."))
    return REFERRAL_MENU

async def ref_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle referral history callback."""
    query = update.callback_query
    await query.answer()
    
    # This is a placeholder function
    await query.message.reply_text(_("This feature is not implemented yet."))
    return REFERRAL_MENU

async def ref_rewards(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle referral rewards callback."""
    query = update.callback_query
    await query.answer()
    
    # This is a placeholder function
    await query.message.reply_text(_("This feature is not implemented yet."))
    return REFERRAL_MENU

def get_profile_handler() -> ConversationHandler:
    """Return the handler for profile functionality."""
    return ConversationHandler(
        entry_points=[CommandHandler("profile", profile_command)],
        states={
            PROFILE_MENU: [
                CallbackQueryHandler(wallet_menu, pattern=f"^{WALLET_CB}$"),
                CallbackQueryHandler(subscription_menu, pattern=f"^{SUBSCRIPTIONS_CB}$"),
                CallbackQueryHandler(referral_menu, pattern=f"^{REFERRALS_CB}$"),
                CallbackQueryHandler(settings_menu, pattern=f"^{SETTINGS_CB}$"),
                CallbackQueryHandler(back_to_main, pattern=f"^{MAIN_MENU_CB}$"),
            ],
            WALLET_MENU: [
                CallbackQueryHandler(add_funds, pattern=f"^{ADD_FUNDS_CB}$"),
                CallbackQueryHandler(transfer_menu, pattern=f"^{TRANSFER_CB}$"),
                CallbackQueryHandler(wallet_stats, pattern=f"^{WALLET_STATS_CB}$"),
                CallbackQueryHandler(wallet_history, pattern=f"^{WALLET_HISTORY_CB}$"),
                CallbackQueryHandler(back_to_profile, pattern=f"^{BACK_CB}$"),
            ],
            SETTINGS_MENU: [
                CallbackQueryHandler(toggle_auto_renew, pattern="^auto_renew$"),
                CallbackQueryHandler(security_settings, pattern="^security$"),
                CallbackQueryHandler(toggle_2fa, pattern="^toggle_2fa$"),
                CallbackQueryHandler(view_sessions, pattern="^sessions$"),
                CallbackQueryHandler(view_devices, pattern="^devices$"),
                CallbackQueryHandler(revoke_all_sessions, pattern="^revoke_all$"),
                CallbackQueryHandler(back_to_profile, pattern=f"^{BACK_CB}$"),
            ],
            ENTERING_2FA_CODE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, verify_2fa_code),
                CallbackQueryHandler(security_settings, pattern=f"^{BACK_CB}$"),
            ],
            ADDING_FUNDS: [
                CallbackQueryHandler(process_add_funds, pattern="^amount_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_add_funds),
                CallbackQueryHandler(wallet_menu, pattern=f"^{BACK_CB}$"),
            ],
            TRANSFER_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_transfer_amount),
                CallbackQueryHandler(wallet_menu, pattern=f"^{BACK_CB}$"),
            ],
            TRANSFER_USER: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_transfer_user),
                CallbackQueryHandler(wallet_menu, pattern=f"^{BACK_CB}$"),
            ],
            SUBSCRIPTION_MENU: [
                CallbackQueryHandler(buy_plan, pattern=f"^{BUY_PLAN_CB}$"),
                CallbackQueryHandler(renew_plan, pattern=f"^{RENEW_PLAN_CB}$"),
                CallbackQueryHandler(usage_stats, pattern=f"^{USAGE_STATS_CB}$"),
                CallbackQueryHandler(sub_history, pattern=f"^{SUB_HISTORY_CB}$"),
                CallbackQueryHandler(back_to_profile, pattern=f"^{BACK_CB}$"),
            ],
            REFERRAL_MENU: [
                CallbackQueryHandler(ref_stats, pattern=f"^{REF_STATS_CB}$"),
                CallbackQueryHandler(ref_history, pattern=f"^{REF_HISTORY_CB}$"),
                CallbackQueryHandler(ref_rewards, pattern=f"^{REF_REWARDS_CB}$"),
                CallbackQueryHandler(ref_share, pattern=f"^{REF_SHARE_CB}$"),
                CallbackQueryHandler(back_to_profile, pattern=f"^{BACK_CB}$"),
            ],
        },
        fallbacks=[
            CommandHandler("profile", profile_command),
            CommandHandler("start", start_command),
        ],
    ) 