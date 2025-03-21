import logging
from typing import List

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, CommandHandler

from core.database.models.user import User
from bot.constants import CallbackPatterns

logger = logging.getLogger(__name__)

# Menu image URL - You can host this on your server or use a file_id after uploading once
MENU_IMAGE = "https://example.com/path/to/vpn_header.jpg"  # Replace with actual image URL or file_id

async def main_menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display the main menu when the /menu command is used."""
    user = update.effective_user
    
    # Check if user is admin
    db_user = User.get_by_telegram_id(user.id)
    is_admin = db_user.is_admin if db_user else False
    
    # Get the main menu keyboard
    keyboard = get_main_menu_keyboard(is_admin)
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Menu message
    menu_text = (
        "🌙 <b>منوی اصلی MoonVPN</b>\n\n"
        "به پیشرفته‌ترین سیستم VPN با پروتکل V2RAY خوش آمدید.\n"
        "از منوی زیر گزینه مورد نظر خود را انتخاب کنید."
    )
    
    # Try to send menu with image
    try:
        await update.message.reply_photo(
            photo=MENU_IMAGE,
            caption=menu_text,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error sending menu with image: {e}")
        # Fallback to text-only menu
        await update.message.reply_text(
            menu_text,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the main menu in response to a callback query."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    # Check if user is admin
    db_user = User.get_by_telegram_id(user.id)
    is_admin = db_user.is_admin if db_user else False
    
    # Get the main menu keyboard
    keyboard = get_main_menu_keyboard(is_admin)
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Menu message
    menu_text = (
        "🌙 <b>منوی اصلی MoonVPN</b>\n\n"
        "به پیشرفته‌ترین سیستم VPN با پروتکل V2RAY خوش آمدید.\n"
        "از منوی زیر گزینه مورد نظر خود را انتخاب کنید."
    )
    
    # Try to edit message with image
    try:
        # Check if original message has image
        if query.message.photo:
            await query.edit_message_caption(
                caption=menu_text,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
        else:
            # Send new message with image
            await query.message.reply_photo(
                photo=MENU_IMAGE,
                caption=menu_text,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
            # Delete old message
            await query.message.delete()
    except Exception as e:
        logger.error(f"Error updating menu: {e}")
        # Fallback to text-only update
        try:
            await query.edit_message_text(
                text=menu_text,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
        except Exception as e2:
            logger.error(f"Failed to update menu text: {e2}")

def get_main_menu_keyboard(is_admin: bool = False) -> List[List[InlineKeyboardButton]]:
    """Create the main menu keyboard buttons."""
    keyboard = [
        [
            InlineKeyboardButton("🔐 اشتراک های من", callback_data=CallbackPatterns.MY_ACCOUNTS),
            InlineKeyboardButton("🛒 خرید اشتراک جدید", callback_data=CallbackPatterns.BUY_ACCOUNT)
        ],
        [
            InlineKeyboardButton("💰 افزایش موجودی", callback_data=CallbackPatterns.INCREASE_CREDIT),
            InlineKeyboardButton("👤 حساب کاربری", callback_data=CallbackPatterns.USER_SETTINGS)
        ],
        [
            InlineKeyboardButton("🔄 تست رایگان", callback_data=CallbackPatterns.FREE_TEST),
            InlineKeyboardButton("🌐 پروکسی رایگان", callback_data=CallbackPatterns.FREE_PROXY)
        ],
        [
            InlineKeyboardButton("💸 کسب درآمد", callback_data=CallbackPatterns.EARN_MONEY),
            InlineKeyboardButton("🎯 وضعیت سرویس", callback_data=CallbackPatterns.ACCOUNT_STATUS)
        ],
        [
            InlineKeyboardButton("❓ راهنما", callback_data=CallbackPatterns.HELP_COMMAND),
            InlineKeyboardButton("👨‍💻 پشتیبانی", callback_data=CallbackPatterns.SUPPORT)
        ]
    ]
    
    # Add admin button if user is admin
    if is_admin:
        keyboard.append([InlineKeyboardButton("⚙️ پنل مدیریت", callback_data=CallbackPatterns.ADMIN_DASHBOARD)])
    
    return keyboard

async def handle_temp_feature(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle temporary feature callbacks."""
    query = update.callback_query
    await query.answer("این قابلیت به زودی اضافه خواهد شد!")

def get_main_menu_handlers():
    """Return handlers related to the main menu."""
    return [
        CommandHandler("menu", main_menu_command),
        CallbackQueryHandler(show_main_menu, pattern=f"^{CallbackPatterns.MAIN_MENU}$"),
        CallbackQueryHandler(handle_temp_feature, pattern=f"^{CallbackPatterns.FREE_TEST}$"),
        CallbackQueryHandler(handle_temp_feature, pattern=f"^{CallbackPatterns.FREE_PROXY}$"),
    ] 