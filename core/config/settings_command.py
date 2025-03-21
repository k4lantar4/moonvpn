from typing import List, Optional
from telegram import Update, CallbackQuery
from telegram.ext import ContextTypes
from ...models import User
from ..keyboards import (
    get_settings_keyboard,
    get_language_keyboard,
    get_notifications_keyboard
)

async def show_settings(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user: User
) -> None:
    """Show settings menu"""
    if not update.effective_message:
        return
        
    keyboard = get_settings_keyboard(user.language)
    
    await update.effective_message.reply_text(
        "⚙️ Settings"
        if user.language == 'en' else
        "⚙️ تنظیمات",
        reply_markup=keyboard
    )

async def show_language_settings(
    query: CallbackQuery,
    context: ContextTypes.DEFAULT_TYPE,
    user: User
) -> None:
    """Show language settings"""
    keyboard = get_language_keyboard()
    
    await query.edit_message_text(
        "🌐 Select your language:"
        if user.language == 'en' else
        "🌐 زبان خود را انتخاب کنید:",
        reply_markup=keyboard
    )

async def update_language(
    query: CallbackQuery,
    context: ContextTypes.DEFAULT_TYPE,
    user: User,
    language: str
) -> None:
    """Update user language"""
    # Update user language
    user.language = language
    user.save()
    
    # Show success message
    if language == 'fa':
        text = "✅ زبان با موفقیت به فارسی تغییر کرد."
    else:
        text = "✅ Language successfully changed to English."
    
    # Show settings menu with new language
    keyboard = get_settings_keyboard(language)
    
    await query.edit_message_text(
        text=text,
        reply_markup=keyboard
    )

async def show_notifications_settings(
    query: CallbackQuery,
    context: ContextTypes.DEFAULT_TYPE,
    user: User
) -> None:
    """Show notifications settings"""
    keyboard = get_notifications_keyboard(user.language)
    
    if user.language == 'fa':
        text = (
            "🔔 تنظیمات اعلان‌ها\n\n"
            "وضعیت فعلی: "
            f"{'✅ فعال' if user.notifications_enabled else '❌ غیرفعال'}"
        )
    else:
        text = (
            "🔔 Notifications Settings\n\n"
            "Current status: "
            f"{'✅ Enabled' if user.notifications_enabled else '❌ Disabled'}"
        )
    
    await query.edit_message_text(
        text=text,
        reply_markup=keyboard
    )

async def update_notifications(
    query: CallbackQuery,
    context: ContextTypes.DEFAULT_TYPE,
    user: User,
    enabled: bool
) -> None:
    """Update notifications settings"""
    # Update user notifications setting
    user.notifications_enabled = enabled
    user.save()
    
    # Show success message
    if user.language == 'fa':
        text = (
            "✅ اعلان‌ها با موفقیت فعال شد."
            if enabled else
            "✅ اعلان‌ها با موفقیت غیرفعال شد."
        )
    else:
        text = (
            "✅ Notifications successfully enabled."
            if enabled else
            "✅ Notifications successfully disabled."
        )
    
    # Show settings menu
    keyboard = get_settings_keyboard(user.language)
    
    await query.edit_message_text(
        text=text,
        reply_markup=keyboard
    )

async def handle_callback(
    query: CallbackQuery,
    context: ContextTypes.DEFAULT_TYPE,
    user: User,
    data: List[str]
) -> None:
    """Handle settings callback queries"""
    action = data[1] if len(data) > 1 else None
    
    if action == 'main':
        # Show main settings menu
        keyboard = get_settings_keyboard(user.language)
        
        await query.edit_message_text(
            "⚙️ Settings"
            if user.language == 'en' else
            "⚙️ تنظیمات",
            reply_markup=keyboard
        )
        
    elif action == 'language':
        if len(data) > 2:
            # Update language
            await update_language(
                query,
                context,
                user,
                data[2]
            )
        else:
            # Show language settings
            await show_language_settings(
                query,
                context,
                user
            )
            
    elif action == 'notifications':
        if len(data) > 2:
            # Update notifications
            enabled = data[2] == 'on'
            await update_notifications(
                query,
                context,
                user,
                enabled
            )
        else:
            # Show notifications settings
            await show_notifications_settings(
                query,
                context,
                user
            )
            
    else:
        await query.answer(
            "Invalid action"
            if user.language == 'en' else
            "عملیات نامعتبر"
        ) 