"""
MoonVPN Telegram Bot - Help handlers.

This module provides help functionality for the MoonVPN Telegram Bot.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
)

from models import User
from core.utils.i18n import _
import constants

logger = logging.getLogger(__name__)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /help command and display help menu with categories."""
    user = update.effective_user
    db_user = User.get_by_telegram_id(user.id)
    
    # Help message header
    help_text = _(
        "*🌙 راهنمای MoonVPN*\n\n"
        "به بخش راهنمای MoonVPN خوش آمدید.\n"
        "لطفاً موضوع مورد نظر خود را انتخاب کنید:",
        db_user.language
    )
    
    # Create help menu buttons
    keyboard = [
        [
            InlineKeyboardButton(
                text=_("🛒 خرید اکانت", db_user.language),
                callback_data=constants.CALLBACK_HELP_ACCOUNTS
            ),
            InlineKeyboardButton(
                text=_("🔑 اتصال به VPN", db_user.language),
                callback_data=constants.CALLBACK_HELP_CONNECTION
            )
        ],
        [
            InlineKeyboardButton(
                text=_("💰 روش‌های پرداخت", db_user.language),
                callback_data=constants.CALLBACK_HELP_PAYMENT
            ),
            InlineKeyboardButton(
                text=_("❓ عیب‌یابی مشکلات", db_user.language),
                callback_data=constants.CALLBACK_HELP_TROUBLESHOOT
            )
        ],
        [
            InlineKeyboardButton(
                text=_("📱 نرم‌افزارهای VPN", db_user.language),
                callback_data=constants.CALLBACK_HELP_APPS
            ),
            InlineKeyboardButton(
                text=_("📋 دستورات ربات", db_user.language),
                callback_data=constants.CALLBACK_HELP_COMMANDS
            )
        ],
        [
            InlineKeyboardButton(
                text=_("🏠 بازگشت به منوی اصلی", db_user.language),
                callback_data=constants.CALLBACK_MAIN_MENU
            )
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send help menu message
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text=help_text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            text=help_text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

async def help_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display help information about purchasing VPN accounts."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    db_user = User.get_by_telegram_id(user.id)
    
    # Help message for purchasing accounts
    help_text = _(
        "*🛒 راهنمای خرید اکانت VPN*\n\n"
        "برای خرید اکانت VPN در MoonVPN، مراحل زیر را دنبال کنید:\n\n"
        "1️⃣ از منوی اصلی گزینه «🛒 خرید اکانت» را انتخاب کنید.\n"
        "2️⃣ از لیست پکیج‌های موجود، پکیج مورد نظر خود را انتخاب کنید.\n"
        "3️⃣ سرور مورد نظر خود را از لیست سرورهای موجود انتخاب کنید.\n"
        "4️⃣ روش پرداخت را انتخاب کرده و مبلغ را پرداخت کنید.\n"
        "5️⃣ پس از تأیید پرداخت، اکانت شما فعال خواهد شد.\n\n"
        "توجه: برای دریافت بهترین کیفیت، سروری را انتخاب کنید که به موقعیت مکانی شما نزدیک‌تر است.",
        db_user.language
    )
    
    # Return to help menu button
    keyboard = [
        [
            InlineKeyboardButton(
                text=_("🔙 بازگشت به منوی راهنما", db_user.language),
                callback_data=constants.CALLBACK_HELP
            )
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=help_text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def help_account(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display help information about managing accounts."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    db_user = User.get_by_telegram_id(user.id)
    
    # Help message for account management
    help_text = _(
        "*👤 راهنمای مدیریت اکانت‌ها*\n\n"
        "برای مدیریت اکانت‌های VPN خود در MoonVPN، می‌توانید از گزینه‌های زیر استفاده کنید:\n\n"
        "📊 *وضعیت اکانت*: برای مشاهده وضعیت، ترافیک و تاریخ انقضای اکانت‌های خود\n"
        "🔄 *تمدید اکانت*: برای تمدید اکانت‌های منقضی شده یا در حال انقضا\n"
        "🌍 *تغییر لوکیشن*: برای تغییر سرور و لوکیشن اکانت‌های موجود\n"
        "📶 *مصرف ترافیک*: برای مشاهده میزان مصرف ترافیک اکانت‌های شما\n\n"
        "برای دسترسی به این گزینه‌ها، از منوی اصلی یا دستورات مربوطه استفاده کنید.",
        db_user.language
    )
    
    # Return to help menu button
    keyboard = [
        [
            InlineKeyboardButton(
                text=_("🔙 بازگشت به منوی راهنما", db_user.language),
                callback_data=constants.CALLBACK_HELP
            )
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=help_text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def help_connection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display help information about connecting to VPN."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    db_user = User.get_by_telegram_id(user.id)
    
    # Help message for VPN connection
    help_text = _(
        "*🔑 راهنمای اتصال به VPN*\n\n"
        "برای اتصال به VPN در MoonVPN، مراحل زیر را دنبال کنید:\n\n"
        "1️⃣ ابتدا یکی از نرم‌افزارهای زیر را بر اساس سیستم عامل خود نصب کنید:\n"
        "- *اندروید*: V2rayNG یا Nekobox\n"
        "- *iOS*: Shadowrocket یا FairVPN\n"
        "- *ویندوز*: V2rayN یا Nekoray\n"
        "- *مک*: V2rayU یا ClashX\n\n"
        "2️⃣ در ربات، از منوی اصلی گزینه «📊 وضعیت اکانت» را انتخاب کنید.\n"
        "3️⃣ روی اکانت مورد نظر خود کلیک کرده و گزینه «دریافت کانفیگ» را انتخاب کنید.\n"
        "4️⃣ کانفیگ دریافتی را در نرم‌افزار VPN خود وارد کنید.\n"
        "5️⃣ اتصال خود را برقرار کنید.\n\n"
        "برای راهنمایی بیشتر درباره نرم‌افزارها، گزینه «📱 نرم‌افزارهای VPN» را انتخاب کنید.",
        db_user.language
    )
    
    # Return to help menu button
    keyboard = [
        [
            InlineKeyboardButton(
                text=_("📱 نرم‌افزارهای VPN", db_user.language),
                callback_data=constants.CALLBACK_HELP_APPS
            )
        ],
        [
            InlineKeyboardButton(
                text=_("🔙 بازگشت به منوی راهنما", db_user.language),
                callback_data=constants.CALLBACK_HELP
            )
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=help_text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def help_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display help information about payment methods."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    db_user = User.get_by_telegram_id(user.id)
    
    # Help message for payment methods
    help_text = _(
        "*💰 راهنمای روش‌های پرداخت*\n\n"
        "در MoonVPN، می‌توانید از روش‌های پرداخت زیر استفاده کنید:\n\n"
        "💳 *کارت به کارت*:\n"
        "1. مبلغ مورد نظر را به شماره کارت نمایش داده شده واریز کنید.\n"
        "2. اطلاعات پرداخت (شماره کارت، ساعت پرداخت، نام صاحب کارت) را وارد کنید.\n"
        "3. پس از تأیید توسط مدیر، اکانت شما فعال خواهد شد.\n\n"
        "💻 *درگاه پرداخت زرین‌پال* (در صورت فعال بودن):\n"
        "1. گزینه «پرداخت آنلاین» را انتخاب کنید.\n"
        "2. به درگاه پرداخت زرین‌پال هدایت خواهید شد.\n"
        "3. پس از تکمیل پرداخت، به صورت خودکار به ربات بازگردانده می‌شوید.\n"
        "4. اکانت شما به صورت خودکار فعال خواهد شد.\n\n"
        "برای پرداخت، در هنگام خرید اکانت، روش پرداخت مورد نظر خود را انتخاب کنید.",
        db_user.language
    )
    
    # Return to help menu button
    keyboard = [
        [
            InlineKeyboardButton(
                text=_("🔙 بازگشت به منوی راهنما", db_user.language),
                callback_data=constants.CALLBACK_HELP
            )
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=help_text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def help_troubleshoot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display help information for troubleshooting connection issues."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    db_user = User.get_by_telegram_id(user.id)
    
    # Help message for troubleshooting
    help_text = _(
        "*❓ عیب‌یابی مشکلات اتصال*\n\n"
        "اگر در اتصال به VPN مشکل دارید، راه‌حل‌های زیر را امتحان کنید:\n\n"
        "1️⃣ *اتصال برقرار نمی‌شود*:\n"
        "- اطمینان حاصل کنید که اکانت شما فعال است.\n"
        "- کانفیگ جدیدی از ربات دریافت کنید.\n"
        "- اینترنت اصلی خود را بررسی کنید.\n"
        "- سرور دیگری را امتحان کنید (از گزینه تغییر لوکیشن).\n\n"
        "2️⃣ *سرعت پایین است*:\n"
        "- سروری با نزدیک‌ترین لوکیشن به خود انتخاب کنید.\n"
        "- در ساعات شلوغی، ممکن است سرعت کاهش یابد.\n"
        "- پروتکل اتصال را در نرم‌افزار خود تغییر دهید.\n\n"
        "3️⃣ *قطع و وصل شدن مداوم*:\n"
        "- نرم‌افزار VPN خود را به‌روزرسانی کنید.\n"
        "- از اتصال اینترنت پایدار استفاده کنید.\n"
        "- تنظیمات «Keep Alive» را در نرم‌افزار خود فعال کنید.\n\n"
        "اگر مشکل شما حل نشد، با پشتیبانی تماس بگیرید.",
        db_user.language
    )
    
    # Return to help menu button
    keyboard = [
        [
            InlineKeyboardButton(
                text=_("🆘 تماس با پشتیبانی", db_user.language),
                callback_data=constants.CALLBACK_SUPPORT
            )
        ],
        [
            InlineKeyboardButton(
                text=_("🔙 بازگشت به منوی راهنما", db_user.language),
                callback_data=constants.CALLBACK_HELP
            )
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=help_text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def help_commands(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display help information about bot commands."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    db_user = User.get_by_telegram_id(user.id)
    
    # Help message for bot commands
    help_text = _(
        "*📋 دستورات ربات MoonVPN*\n\n"
        "دستورات اصلی ربات MoonVPN به شرح زیر است:\n\n"
        "/start - شروع ربات و نمایش منوی اصلی\n"
        "/buy - خرید اکانت جدید\n"
        "/status - مشاهده وضعیت اکانت‌های شما\n"
        "/location - تغییر لوکیشن سرور\n"
        "/traffic - مشاهده مصرف ترافیک\n"
        "/settings - تنظیمات کاربری\n"
        "/help - نمایش راهنمای ربات\n"
        "/support - تماس با پشتیبانی\n\n"
        "شما می‌توانید به جای استفاده از این دستورات، از دکمه‌های موجود در منوی اصلی نیز استفاده کنید.",
        db_user.language
    )
    
    # Return to help menu button
    keyboard = [
        [
            InlineKeyboardButton(
                text=_("🔙 بازگشت به منوی راهنما", db_user.language),
                callback_data=constants.CALLBACK_HELP
            )
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=help_text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def help_apps(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display help information about VPN applications."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    db_user = User.get_by_telegram_id(user.id)
    
    # Help message for VPN applications
    help_text = _(
        "*📱 راهنمای نرم‌افزارهای VPN*\n\n"
        "برای استفاده از سرویس MoonVPN، می‌توانید از نرم‌افزارهای زیر استفاده کنید:\n\n"
        "*📱 اندروید:*\n"
        "- V2rayNG: ساده و کم‌حجم\n"
        "- Nekobox: امکانات پیشرفته و رابط کاربری بهتر\n"
        "- Matsuri: پشتیبانی از پروتکل‌های متنوع\n\n"
        "*🍎 iOS:*\n"
        "- Shadowrocket: پرطرفدارترین نرم‌افزار (نیاز به اپل آیدی خارجی)\n"
        "- FairVPN: جایگزین خوب با قابلیت نصب از App Store ایران\n\n"
        "*💻 ویندوز:*\n"
        "- V2rayN: ساده و سبک\n"
        "- Nekoray: رابط گرافیکی بهتر و امکانات بیشتر\n\n"
        "*🖥 مک:*\n"
        "- V2rayU: ساده و کاربردی\n"
        "- ClashX Pro: رابط گرافیکی عالی و قابلیت‌های پیشرفته\n\n"
        "برای دانلود این نرم‌افزارها، می‌توانید از منابع معتبر آنلاین استفاده کنید یا با پشتیبانی تماس بگیرید.",
        db_user.language
    )
    
    # Return to help menu button
    keyboard = [
        [
            InlineKeyboardButton(
                text=_("🔙 بازگشت به منوی راهنما", db_user.language),
                callback_data=constants.CALLBACK_HELP
            )
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=help_text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

def get_help_handler() -> ConversationHandler:
    """Return a conversation handler for help menus."""
    return [
        CallbackQueryHandler(help_command, pattern=f"^{constants.CALLBACK_HELP}$"),
        CallbackQueryHandler(help_purchase, pattern=f"^{constants.CALLBACK_HELP_ACCOUNTS}$"),
        CallbackQueryHandler(help_connection, pattern=f"^{constants.CALLBACK_HELP_CONNECTION}$"),
        CallbackQueryHandler(help_payment, pattern=f"^{constants.CALLBACK_HELP_PAYMENT}$"),
        CallbackQueryHandler(help_troubleshoot, pattern=f"^{constants.CALLBACK_HELP_TROUBLESHOOT}$"),
        CallbackQueryHandler(help_commands, pattern=f"^{constants.CALLBACK_HELP_COMMANDS}$"),
        CallbackQueryHandler(help_apps, pattern=f"^{constants.CALLBACK_HELP_APPS}$"),
    ] 