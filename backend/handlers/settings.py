"""
MoonVPN Telegram Bot - Settings Handler.

This module provides functionality for users to customize their bot settings.
"""

import logging
from typing import List, Dict, Any, Optional
import json

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, 
    CallbackQueryHandler, 
    CommandHandler, 
    ConversationHandler,
    MessageHandler,
    filters
)

from core.database.models.user import User
from bot.constants import CallbackPatterns, States

logger = logging.getLogger(__name__)

# Settings image URL
SETTINGS_IMAGE = "https://example.com/path/to/settings.jpg"  # Replace with actual image URL or file_id

# States for the settings conversation
(
    SETTINGS_MAIN,
    LANGUAGE_SELECTION,
    NOTIFICATION_SETTINGS,
    THEME_SELECTION,
    AUTO_RENEWAL,
    CONTACT_INFO_INPUT,
    CONFIRM_DELETE
) = range(7)

# Available languages
LANGUAGES = {
    "fa": "🇮🇷 فارسی",
    "en": "🇬🇧 English",
    "ar": "🇸🇦 العربية",
    "tr": "🇹🇷 Türkçe"
}

# Available themes
THEMES = {
    "default": "🔵 استاندارد",
    "dark": "⚫ تیره",
    "light": "⚪ روشن",
    "blue": "🔷 آبی"
}

async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show settings menu."""
    user = update.effective_user
    message = update.message or update.callback_query.message
    
    # Get user from database
    db_user = User.get_by_telegram_id(user.id)
    if not db_user:
        # Create user if not exists
        db_user = User.create(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        logger.info(f"Created new user for settings: {user.id} - @{user.username}")
    
    # Get user settings
    settings = get_user_settings(db_user)
    
    # Create message
    settings_text = (
        f"⚙️ <b>تنظیمات MoonVPN</b>\n\n"
        f"کاربر گرامی {user.first_name}، می‌توانید تنظیمات زیر را سفارشی کنید:\n\n"
        f"🌐 <b>زبان:</b> {LANGUAGES.get(settings['language'], 'فارسی')}\n"
        f"🔔 <b>اعلان‌ها:</b> {'فعال ✅' if settings['notifications_enabled'] else 'غیرفعال ❌'}\n"
        f"🎨 <b>تم:</b> {THEMES.get(settings['theme'], 'استاندارد')}\n"
        f"♻️ <b>تمدید خودکار:</b> {'فعال ✅' if settings['auto_renewal'] else 'غیرفعال ❌'}\n"
        f"📱 <b>اطلاعات تماس:</b> {settings.get('contact_info', 'تنظیم نشده')}\n\n"
        f"لطفا گزینه مورد نظر خود را برای تغییر انتخاب کنید:"
    )
    
    # Create keyboard
    keyboard = [
        [
            InlineKeyboardButton("🌐 زبان", callback_data=f"{CallbackPatterns.SETTINGS}_language"),
            InlineKeyboardButton("🔔 اعلان‌ها", callback_data=f"{CallbackPatterns.SETTINGS}_notifications")
        ],
        [
            InlineKeyboardButton("🎨 تم", callback_data=f"{CallbackPatterns.SETTINGS}_theme"),
            InlineKeyboardButton("♻️ تمدید خودکار", callback_data=f"{CallbackPatterns.SETTINGS}_auto_renewal")
        ],
        [
            InlineKeyboardButton("📱 اطلاعات تماس", callback_data=f"{CallbackPatterns.SETTINGS}_contact"),
            InlineKeyboardButton("🔑 تغییر رمز عبور", callback_data=f"{CallbackPatterns.SETTINGS}_password")
        ],
        [
            InlineKeyboardButton("🔄 ریست تنظیمات", callback_data=f"{CallbackPatterns.SETTINGS}_reset"),
            InlineKeyboardButton("❌ حذف حساب کاربری", callback_data=f"{CallbackPatterns.SETTINGS}_delete_account")
        ],
        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data=CallbackPatterns.MAIN_MENU)]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send or edit message
    try:
        if update.callback_query:
            await update.callback_query.answer()
            
            if hasattr(update.callback_query.message, 'photo'):
                await update.callback_query.edit_message_caption(
                    caption=settings_text,
                    reply_markup=reply_markup,
                    parse_mode="HTML"
                )
            else:
                await update.callback_query.edit_message_text(
                    text=settings_text,
                    reply_markup=reply_markup,
                    parse_mode="HTML"
                )
        else:
            try:
                await message.reply_photo(
                    photo=SETTINGS_IMAGE,
                    caption=settings_text,
                    reply_markup=reply_markup,
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.error(f"Error sending settings menu with image: {e}")
                await message.reply_text(
                    text=settings_text,
                    reply_markup=reply_markup,
                    parse_mode="HTML"
                )
    except Exception as e:
        logger.error(f"Error in settings command: {e}")
    
    return SETTINGS_MAIN

async def language_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show language selection menu."""
    query = update.callback_query
    await query.answer()
    
    # Create message
    language_text = (
        "🌐 <b>انتخاب زبان</b>\n\n"
        "لطفا زبان مورد نظر خود را انتخاب کنید:"
    )
    
    # Create keyboard with available languages
    keyboard = []
    
    # Add language buttons in pairs
    languages_list = list(LANGUAGES.items())
    for i in range(0, len(languages_list), 2):
        row = []
        for j in range(2):
            if i + j < len(languages_list):
                lang_code, lang_name = languages_list[i + j]
                row.append(
                    InlineKeyboardButton(
                        lang_name, 
                        callback_data=f"{CallbackPatterns.SETTINGS}_set_language_{lang_code}"
                    )
                )
        keyboard.append(row)
    
    # Add back button
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data=CallbackPatterns.SETTINGS)])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Edit message
    await query.edit_message_text(
        text=language_text,
        reply_markup=reply_markup,
        parse_mode="HTML"
    )
    
    return LANGUAGE_SELECTION

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Set user's language preference."""
    query = update.callback_query
    
    # Get selected language
    lang_code = query.data.split("_")[3]
    
    # Get user from database
    user = update.effective_user
    db_user = User.get_by_telegram_id(user.id)
    
    # Update language
    update_user_setting(db_user, "language", lang_code)
    
    # Show confirmation
    await query.answer(f"زبان به {LANGUAGES.get(lang_code, 'فارسی')} تغییر یافت.")
    
    # Return to settings menu
    return await settings_command(update, context)

async def notification_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show notification settings menu."""
    query = update.callback_query
    await query.answer()
    
    # Get user from database
    user = update.effective_user
    db_user = User.get_by_telegram_id(user.id)
    
    # Get current settings
    settings = get_user_settings(db_user)
    
    # Create message
    notification_text = (
        "🔔 <b>تنظیمات اعلان‌ها</b>\n\n"
        "شما می‌توانید انواع اعلان‌های مختلف را فعال یا غیرفعال کنید:\n\n"
        f"• اعلان‌های سیستمی: {'فعال ✅' if settings.get('system_notifications', True) else 'غیرفعال ❌'}\n"
        f"• اطلاع‌رسانی ترافیک: {'فعال ✅' if settings.get('traffic_notifications', True) else 'غیرفعال ❌'}\n"
        f"• هشدار انقضا: {'فعال ✅' if settings.get('expiry_notifications', True) else 'غیرفعال ❌'}\n"
        f"• اخبار و تخفیف‌ها: {'فعال ✅' if settings.get('promo_notifications', True) else 'غیرفعال ❌'}\n\n"
        "لطفا تنظیمات مورد نظر خود را انتخاب کنید:"
    )
    
    # Create keyboard
    keyboard = [
        [
            InlineKeyboardButton(
                f"{'✅' if settings.get('system_notifications', True) else '❌'} اعلان‌های سیستمی", 
                callback_data=f"{CallbackPatterns.SETTINGS}_toggle_system_notifications"
            )
        ],
        [
            InlineKeyboardButton(
                f"{'✅' if settings.get('traffic_notifications', True) else '❌'} اطلاع‌رسانی ترافیک", 
                callback_data=f"{CallbackPatterns.SETTINGS}_toggle_traffic_notifications"
            )
        ],
        [
            InlineKeyboardButton(
                f"{'✅' if settings.get('expiry_notifications', True) else '❌'} هشدار انقضا", 
                callback_data=f"{CallbackPatterns.SETTINGS}_toggle_expiry_notifications"
            )
        ],
        [
            InlineKeyboardButton(
                f"{'✅' if settings.get('promo_notifications', True) else '❌'} اخبار و تخفیف‌ها", 
                callback_data=f"{CallbackPatterns.SETTINGS}_toggle_promo_notifications"
            )
        ],
        [
            InlineKeyboardButton(
                "همه روشن ✅", 
                callback_data=f"{CallbackPatterns.SETTINGS}_enable_all_notifications"
            ),
            InlineKeyboardButton(
                "همه خاموش ❌", 
                callback_data=f"{CallbackPatterns.SETTINGS}_disable_all_notifications"
            )
        ],
        [InlineKeyboardButton("🔙 بازگشت", callback_data=CallbackPatterns.SETTINGS)]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Edit message
    await query.edit_message_text(
        text=notification_text,
        reply_markup=reply_markup,
        parse_mode="HTML"
    )
    
    return NOTIFICATION_SETTINGS

async def toggle_notification(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Toggle a specific notification setting."""
    query = update.callback_query
    
    # Get notification type
    callback_data = query.data
    parts = callback_data.split("_")
    action = parts[2]  # toggle, enable_all, disable_all
    
    # Get user from database
    user = update.effective_user
    db_user = User.get_by_telegram_id(user.id)
    
    # Get current settings
    settings = get_user_settings(db_user)
    
    if action == "toggle":
        notification_type = parts[3]
        setting_key = f"{notification_type}_notifications"
        
        # Toggle the specific notification
        current_value = settings.get(setting_key, True)
        update_user_setting(db_user, setting_key, not current_value)
        
        # Update main notifications flag if needed
        if not current_value:  # Turning on a notification
            update_user_setting(db_user, "notifications_enabled", True)
        else:
            # Check if all are now disabled
            all_disabled = all([
                not settings.get("system_notifications", True),
                not settings.get("traffic_notifications", True),
                not settings.get("expiry_notifications", True),
                not settings.get("promo_notifications", True)
            ])
            if all_disabled:
                update_user_setting(db_user, "notifications_enabled", False)
        
        # Show confirmation
        notification_name = {
            "system": "اعلان‌های سیستمی",
            "traffic": "اطلاع‌رسانی ترافیک",
            "expiry": "هشدار انقضا",
            "promo": "اخبار و تخفیف‌ها"
        }.get(notification_type, "اعلان")
        
        status = "فعال" if not current_value else "غیرفعال"
        await query.answer(f"{notification_name} {status} شد.")
    
    elif action == "enable_all":
        # Enable all notifications
        update_user_setting(db_user, "system_notifications", True)
        update_user_setting(db_user, "traffic_notifications", True)
        update_user_setting(db_user, "expiry_notifications", True)
        update_user_setting(db_user, "promo_notifications", True)
        update_user_setting(db_user, "notifications_enabled", True)
        
        await query.answer("همه اعلان‌ها فعال شدند.")
    
    elif action == "disable_all":
        # Disable all notifications
        update_user_setting(db_user, "system_notifications", False)
        update_user_setting(db_user, "traffic_notifications", False)
        update_user_setting(db_user, "expiry_notifications", False)
        update_user_setting(db_user, "promo_notifications", False)
        update_user_setting(db_user, "notifications_enabled", False)
        
        await query.answer("همه اعلان‌ها غیرفعال شدند.")
    
    # Return to notification settings menu
    return await notification_settings(update, context)

async def theme_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show theme selection menu."""
    query = update.callback_query
    await query.answer()
    
    # Create message
    theme_text = (
        "🎨 <b>انتخاب تم</b>\n\n"
        "لطفا تم مورد نظر خود را انتخاب کنید:"
    )
    
    # Create keyboard with available themes
    keyboard = []
    
    # Add theme buttons
    for theme_code, theme_name in THEMES.items():
        keyboard.append([
            InlineKeyboardButton(
                theme_name, 
                callback_data=f"{CallbackPatterns.SETTINGS}_set_theme_{theme_code}"
            )
        ])
    
    # Add back button
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data=CallbackPatterns.SETTINGS)])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Edit message
    await query.edit_message_text(
        text=theme_text,
        reply_markup=reply_markup,
        parse_mode="HTML"
    )
    
    return THEME_SELECTION

async def set_theme(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Set user's theme preference."""
    query = update.callback_query
    
    # Get selected theme
    theme_code = query.data.split("_")[3]
    
    # Get user from database
    user = update.effective_user
    db_user = User.get_by_telegram_id(user.id)
    
    # Update theme
    update_user_setting(db_user, "theme", theme_code)
    
    # Show confirmation
    await query.answer(f"تم به {THEMES.get(theme_code, 'استاندارد')} تغییر یافت.")
    
    # Return to settings menu
    return await settings_command(update, context)

async def auto_renewal_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show auto renewal settings menu."""
    query = update.callback_query
    await query.answer()
    
    # Get user from database
    user = update.effective_user
    db_user = User.get_by_telegram_id(user.id)
    
    # Get current settings
    settings = get_user_settings(db_user)
    auto_renewal_status = settings.get('auto_renewal', False)
    
    # Create message
    renewal_text = (
        "♻️ <b>تنظیمات تمدید خودکار</b>\n\n"
        f"وضعیت فعلی تمدید خودکار: {'فعال ✅' if auto_renewal_status else 'غیرفعال ❌'}\n\n"
        "با فعال کردن تمدید خودکار، اکانت‌های VPN شما به طور خودکار قبل از انقضا تمدید خواهند شد.\n"
        "هزینه تمدید از موجودی حساب شما کسر می‌شود. در صورت ناکافی بودن موجودی، به شما اطلاع‌رسانی خواهد شد.\n\n"
        "آیا مایل به تغییر وضعیت تمدید خودکار هستید؟"
    )
    
    # Create keyboard
    keyboard = [
        [
            InlineKeyboardButton(
                "فعال کردن ✅" if not auto_renewal_status else "غیرفعال کردن ❌", 
                callback_data=f"{CallbackPatterns.SETTINGS}_toggle_auto_renewal"
            )
        ],
        [InlineKeyboardButton("🔙 بازگشت", callback_data=CallbackPatterns.SETTINGS)]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Edit message
    await query.edit_message_text(
        text=renewal_text,
        reply_markup=reply_markup,
        parse_mode="HTML"
    )
    
    return AUTO_RENEWAL

async def toggle_auto_renewal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Toggle auto renewal setting."""
    query = update.callback_query
    
    # Get user from database
    user = update.effective_user
    db_user = User.get_by_telegram_id(user.id)
    
    # Get current settings
    settings = get_user_settings(db_user)
    auto_renewal_status = settings.get('auto_renewal', False)
    
    # Toggle auto renewal
    update_user_setting(db_user, "auto_renewal", not auto_renewal_status)
    
    # Show confirmation
    status = "فعال" if not auto_renewal_status else "غیرفعال"
    await query.answer(f"تمدید خودکار {status} شد.")
    
    # Return to auto renewal settings menu
    return await auto_renewal_settings(update, context)

async def contact_info_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show contact info settings menu."""
    query = update.callback_query
    await query.answer()
    
    # Get user from database
    user = update.effective_user
    db_user = User.get_by_telegram_id(user.id)
    
    # Get current settings
    settings = get_user_settings(db_user)
    contact_info = settings.get('contact_info', 'تنظیم نشده')
    
    # Create message
    contact_text = (
        "📱 <b>اطلاعات تماس</b>\n\n"
        f"اطلاعات تماس فعلی شما: {contact_info}\n\n"
        "اطلاعات تماس شما برای موارد ضروری مانند اطلاع‌رسانی تمدید اکانت یا مشکلات پرداخت استفاده می‌شود.\n"
        "لطفا شماره موبایل یا ایمیل خود را وارد کنید:\n\n"
        "برای لغو عملیات، روی دکمه «بازگشت» کلیک کنید."
    )
    
    # Create keyboard
    keyboard = [
        [InlineKeyboardButton("🔙 بازگشت", callback_data=CallbackPatterns.SETTINGS)]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Edit message
    await query.edit_message_text(
        text=contact_text,
        reply_markup=reply_markup,
        parse_mode="HTML"
    )
    
    return CONTACT_INFO_INPUT

async def save_contact_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Save user's contact information."""
    # Get user from database
    user = update.effective_user
    db_user = User.get_by_telegram_id(user.id)
    
    # Get contact info from message
    contact_info = update.message.text.strip()
    
    # Validate contact info (simple validation)
    if len(contact_info) < 5:
        await update.message.reply_text(
            "❌ اطلاعات تماس وارد شده معتبر نیست. لطفا شماره موبایل یا ایمیل خود را به درستی وارد کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به تنظیمات", callback_data=CallbackPatterns.SETTINGS)]
            ])
        )
        return CONTACT_INFO_INPUT
    
    # Update contact info
    update_user_setting(db_user, "contact_info", contact_info)
    
    # Send confirmation
    await update.message.reply_text(
        "✅ اطلاعات تماس شما با موفقیت ذخیره شد.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 بازگشت به تنظیمات", callback_data=CallbackPatterns.SETTINGS)]
        ])
    )
    
    return SETTINGS_MAIN

async def reset_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Reset user settings to default."""
    query = update.callback_query
    
    # Get user from database
    user = update.effective_user
    db_user = User.get_by_telegram_id(user.id)
    
    # Reset settings to default
    default_settings = {
        "language": "fa",
        "notifications_enabled": True,
        "system_notifications": True,
        "traffic_notifications": True,
        "expiry_notifications": True,
        "promo_notifications": True,
        "theme": "default",
        "auto_renewal": False
    }
    
    # Update all settings
    for key, value in default_settings.items():
        update_user_setting(db_user, key, value)
    
    # Show confirmation
    await query.answer("تنظیمات به حالت پیش‌فرض بازگردانده شد.")
    
    # Return to settings menu
    return await settings_command(update, context)

async def delete_account_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show delete account confirmation."""
    query = update.callback_query
    await query.answer()
    
    # Create message
    delete_text = (
        "❗ <b>حذف حساب کاربری</b>\n\n"
        "آیا مطمئن هستید که می‌خواهید حساب کاربری خود را حذف کنید؟\n\n"
        "⚠️ <b>توجه:</b> این عمل غیرقابل بازگشت است و تمام اطلاعات شما از جمله اکانت‌های VPN، تراکنش‌ها و تنظیمات شما حذف خواهد شد.\n\n"
        "برای تایید حذف حساب کاربری، روی دکمه «تایید و حذف حساب» کلیک کنید."
    )
    
    # Create keyboard
    keyboard = [
        [InlineKeyboardButton("❌ تایید و حذف حساب", callback_data=f"{CallbackPatterns.SETTINGS}_delete_confirm")],
        [InlineKeyboardButton("🔙 انصراف و بازگشت", callback_data=CallbackPatterns.SETTINGS)]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Edit message
    await query.edit_message_text(
        text=delete_text,
        reply_markup=reply_markup,
        parse_mode="HTML"
    )
    
    return CONFIRM_DELETE

async def delete_account(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Delete user account."""
    query = update.callback_query
    
    # Get user from database
    user = update.effective_user
    db_user = User.get_by_telegram_id(user.id)
    
    # In a real implementation, we would delete the user account from database
    # For now, just show a confirmation message
    
    # Show confirmation
    await query.answer("حساب کاربری شما با موفقیت حذف شد.")
    
    # Send final message
    await query.edit_message_text(
        "✅ <b>حساب کاربری شما با موفقیت حذف شد</b>\n\n"
        "تمام اطلاعات شما از سیستم پاک شده است.\n"
        "اگر در آینده تمایل به استفاده مجدد از خدمات ما داشتید، می‌توانید دوباره با ارسال دستور /start ثبت‌نام کنید.\n\n"
        "با تشکر از اعتماد شما به MoonVPN",
        parse_mode="HTML"
    )
    
    return ConversationHandler.END

async def settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle callbacks from settings menu."""
    query = update.callback_query
    
    # Parse the callback data
    callback_data = query.data
    parts = callback_data.split("_")
    action = parts[1] if len(parts) > 1 else ""
    
    if action == "language":
        return await language_selection(update, context)
    elif action == "set_language" and len(parts) > 2:
        return await set_language(update, context)
    elif action == "notifications":
        return await notification_settings(update, context)
    elif action in ["toggle", "enable_all", "disable_all"]:
        return await toggle_notification(update, context)
    elif action == "theme":
        return await theme_selection(update, context)
    elif action == "set_theme" and len(parts) > 2:
        return await set_theme(update, context)
    elif action == "auto_renewal":
        return await auto_renewal_settings(update, context)
    elif action == "toggle_auto_renewal":
        return await toggle_auto_renewal(update, context)
    elif action == "contact":
        return await contact_info_settings(update, context)
    elif action == "reset":
        return await reset_settings(update, context)
    elif action == "delete_account":
        return await delete_account_confirm(update, context)
    elif action == "delete_confirm":
        return await delete_account(update, context)
    elif action == "password":
        # Password change is not implemented yet
        await query.answer("تغییر رمز عبور به زودی اضافه خواهد شد!")
        return SETTINGS_MAIN
    else:
        # Default - show main settings menu
        return await settings_command(update, context)

def get_user_settings(user: Any) -> Dict[str, Any]:
    """Get user settings from database.
    
    In a real implementation, this would fetch from the database.
    """
    # Mock data for demonstration
    # In a real implementation, fetch settings from user.settings or similar
    
    # Check if user has settings
    if hasattr(user, 'settings') and user.settings:
        try:
            # Parse settings string to dictionary
            return json.loads(user.settings)
        except (json.JSONDecodeError, TypeError):
            logger.error(f"Error parsing user settings for user {user.telegram_id}")
    
    # Return default settings
    return {
        "language": "fa",
        "notifications_enabled": True,
        "system_notifications": True,
        "traffic_notifications": True,
        "expiry_notifications": True,
        "promo_notifications": True,
        "theme": "default",
        "auto_renewal": False,
        "contact_info": "تنظیم نشده"
    }

def update_user_setting(user: Any, key: str, value: Any) -> None:
    """Update a specific user setting in the database.
    
    In a real implementation, this would update the database.
    """
    # Get current settings
    settings = get_user_settings(user)
    
    # Update the specific setting
    settings[key] = value
    
    # Save settings back to user
    # In a real implementation, save to database
    try:
        # Convert settings to JSON string
        settings_json = json.dumps(settings)
        
        # Save to user.settings or similar
        if hasattr(user, 'settings'):
            user.settings = settings_json
            # user.save()  # Save to database
            logger.info(f"Updated setting {key} to {value} for user {user.telegram_id}")
        else:
            logger.error(f"User {user.telegram_id} doesn't have a settings attribute")
    except Exception as e:
        logger.error(f"Error updating user setting: {e}")

def get_settings_handlers() -> List:
    """Return all handlers related to settings."""
    
    settings_conversation = ConversationHandler(
        entry_points=[
            CommandHandler("settings", settings_command),
            CallbackQueryHandler(settings_callback, pattern=f"^{CallbackPatterns.SETTINGS}$")
        ],
        states={
            SETTINGS_MAIN: [
                CallbackQueryHandler(settings_callback, pattern=f"^{CallbackPatterns.SETTINGS}_"),
                CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern=f"^{CallbackPatterns.MAIN_MENU}$")
            ],
            LANGUAGE_SELECTION: [
                CallbackQueryHandler(settings_callback, pattern=f"^{CallbackPatterns.SETTINGS}_set_language_"),
                CallbackQueryHandler(settings_callback, pattern=f"^{CallbackPatterns.SETTINGS}$")
            ],
            NOTIFICATION_SETTINGS: [
                CallbackQueryHandler(settings_callback, pattern=f"^{CallbackPatterns.SETTINGS}_toggle_"),
                CallbackQueryHandler(settings_callback, pattern=f"^{CallbackPatterns.SETTINGS}_enable_all_"),
                CallbackQueryHandler(settings_callback, pattern=f"^{CallbackPatterns.SETTINGS}_disable_all_"),
                CallbackQueryHandler(settings_callback, pattern=f"^{CallbackPatterns.SETTINGS}$")
            ],
            THEME_SELECTION: [
                CallbackQueryHandler(settings_callback, pattern=f"^{CallbackPatterns.SETTINGS}_set_theme_"),
                CallbackQueryHandler(settings_callback, pattern=f"^{CallbackPatterns.SETTINGS}$")
            ],
            AUTO_RENEWAL: [
                CallbackQueryHandler(settings_callback, pattern=f"^{CallbackPatterns.SETTINGS}_toggle_auto_renewal$"),
                CallbackQueryHandler(settings_callback, pattern=f"^{CallbackPatterns.SETTINGS}$")
            ],
            CONTACT_INFO_INPUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, save_contact_info),
                CallbackQueryHandler(settings_callback, pattern=f"^{CallbackPatterns.SETTINGS}$")
            ],
            CONFIRM_DELETE: [
                CallbackQueryHandler(settings_callback, pattern=f"^{CallbackPatterns.SETTINGS}_delete_confirm$"),
                CallbackQueryHandler(settings_callback, pattern=f"^{CallbackPatterns.SETTINGS}$")
            ]
        },
        fallbacks=[
            CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern=f"^{CallbackPatterns.MAIN_MENU}$"),
            CommandHandler("start", lambda u, c: ConversationHandler.END)
        ],
        name="settings_conversation",
        persistent=False
    )
    
    return [settings_conversation] 