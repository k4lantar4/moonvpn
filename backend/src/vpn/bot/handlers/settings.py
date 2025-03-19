from typing import List, Optional
from telegram import Update, CallbackQuery
from telegram.ext import ContextTypes
from ...models import User
from ..keyboards import get_settings_keyboard
from ..constants import (
    MENU_SETTINGS,
    ACTION_SELECT,
    ACTION_BACK,
    get_message
)
from .menu_base import MenuHandler

class SettingsHandler(MenuHandler):
    """Handler for settings menu"""
    
    MENU_TYPE = MENU_SETTINGS
    
    @classmethod
    async def show_menu(
        cls,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        user: User
    ) -> None:
        """Show settings menu"""
        if not update.effective_message:
            return
            
        if user.language == 'fa':
            text = (
                "⚙️ تنظیمات\n\n"
                "از این بخش می‌توانید تنظیمات حساب کاربری خود را مدیریت کنید:\n\n"
                "🌐 زبان فعلی: فارسی\n"
                "🔔 اعلان‌ها: " + ("فعال" if user.notifications_enabled else "غیرفعال") + "\n"
                "📧 ایمیل: " + (user.email or "تنظیم نشده") + "\n"
                "📱 شماره تماس: " + (user.phone or "تنظیم نشده") + "\n\n"
                "برای تغییر هر کدام از موارد، روی آن کلیک کنید."
            )
        else:
            text = (
                "⚙️ Settings\n\n"
                "Here you can manage your account settings:\n\n"
                "🌐 Current Language: English\n"
                "🔔 Notifications: " + ("Enabled" if user.notifications_enabled else "Disabled") + "\n"
                "📧 Email: " + (user.email or "Not set") + "\n"
                "📱 Phone: " + (user.phone or "Not set") + "\n\n"
                "Click on any item to change it."
            )
        
        keyboard = get_settings_keyboard(user.language)
        
        await update.effective_message.reply_text(
            text,
            reply_markup=keyboard
        )
    
    @classmethod
    async def change_language(
        cls,
        query: CallbackQuery,
        context: ContextTypes.DEFAULT_TYPE,
        user: User
    ) -> None:
        """Change user language"""
        # Toggle language
        new_language = 'en' if user.language == 'fa' else 'fa'
        user.language = new_language
        user.save()
        
        # Show success message
        await query.answer(
            "Language changed to English"
            if new_language == 'en' else
            "زبان به فارسی تغییر کرد"
        )
        
        # Update menu
        await cls.show_menu(query, context, user)
    
    @classmethod
    async def toggle_notifications(
        cls,
        query: CallbackQuery,
        context: ContextTypes.DEFAULT_TYPE,
        user: User
    ) -> None:
        """Toggle notifications"""
        # Toggle notifications
        user.notifications_enabled = not user.notifications_enabled
        user.save()
        
        # Show success message
        if user.language == 'fa':
            msg = (
                "اعلان‌ها فعال شد"
                if user.notifications_enabled else
                "اعلان‌ها غیرفعال شد"
            )
        else:
            msg = (
                "Notifications enabled"
                if user.notifications_enabled else
                "Notifications disabled"
            )
        
        await query.answer(msg)
        
        # Update menu
        await cls.show_menu(query, context, user)
    
    @classmethod
    async def request_email(
        cls,
        query: CallbackQuery,
        context: ContextTypes.DEFAULT_TYPE,
        user: User
    ) -> None:
        """Request email from user"""
        if user.language == 'fa':
            text = (
                "📧 تغییر ایمیل\n\n"
                "لطفاً ایمیل جدید خود را وارد کنید.\n"
                "مثال: example@gmail.com\n\n"
                "برای لغو، روی /cancel کلیک کنید."
            )
        else:
            text = (
                "📧 Change Email\n\n"
                "Please enter your new email address.\n"
                "Example: example@gmail.com\n\n"
                "Click /cancel to cancel."
            )
        
        # Set state
        context.user_data['awaiting_email'] = True
        
        await cls.update_menu(query, text)
    
    @classmethod
    async def request_phone(
        cls,
        query: CallbackQuery,
        context: ContextTypes.DEFAULT_TYPE,
        user: User
    ) -> None:
        """Request phone from user"""
        if user.language == 'fa':
            text = (
                "📱 تغییر شماره تماس\n\n"
                "لطفاً شماره تماس جدید خود را وارد کنید.\n"
                "مثال: 09123456789\n\n"
                "برای لغو، روی /cancel کلیک کنید."
            )
        else:
            text = (
                "📱 Change Phone Number\n\n"
                "Please enter your new phone number.\n"
                "Example: +1234567890\n\n"
                "Click /cancel to cancel."
            )
        
        # Set state
        context.user_data['awaiting_phone'] = True
        
        await cls.update_menu(query, text)
    
    @classmethod
    async def handle_callback(
        cls,
        query: CallbackQuery,
        context: ContextTypes.DEFAULT_TYPE,
        user: User,
        data: List[str]
    ) -> None:
        """Handle settings callback queries"""
        action = data[1] if len(data) > 1 else None
        
        if action == "language":
            await cls.change_language(query, context, user)
            
        elif action == "notifications":
            await cls.toggle_notifications(query, context, user)
            
        elif action == "email":
            await cls.request_email(query, context, user)
            
        elif action == "phone":
            await cls.request_phone(query, context, user)
            
        elif action == ACTION_BACK:
            await cls.show_menu(query, context, user)
            
        else:
            await cls.answer_callback_error(
                query,
                "Invalid action",
                user.language
            )
    
    @classmethod
    async def handle_message(
        cls,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        user: User
    ) -> None:
        """Handle settings messages"""
        if not update.message or not update.message.text:
            return
            
        text = update.message.text.strip()
        
        # Handle cancel command
        if text == '/cancel':
            context.user_data.clear()
            await cls.show_menu(update, context, user)
            return
        
        # Handle email input
        if context.user_data.get('awaiting_email'):
            if '@' not in text or '.' not in text:
                await update.message.reply_text(
                    get_message('invalid_email', user.language)
                )
                return
                
            user.email = text
            user.save()
            
            context.user_data.clear()
            await update.message.reply_text(
                get_message('email_updated', user.language)
            )
            await cls.show_menu(update, context, user)
            return
        
        # Handle phone input
        if context.user_data.get('awaiting_phone'):
            # Basic phone validation
            if not text.replace('+', '').isdigit():
                await update.message.reply_text(
                    get_message('invalid_phone', user.language)
                )
                return
                
            user.phone = text
            user.save()
            
            context.user_data.clear()
            await update.message.reply_text(
                get_message('phone_updated', user.language)
            )
            await cls.show_menu(update, context, user)
            return 