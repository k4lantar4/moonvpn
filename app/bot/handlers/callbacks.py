"""
Callback handlers for user profile management in MoonVPN Telegram Bot.
"""

from telegram import Update
from telegram.ext import ContextTypes, CallbackContext
from app.bot.services.profile_service import ProfileService
from app.bot.keyboards.profile_keyboards import (
    get_profile_menu_keyboard,
    get_settings_keyboard,
    get_notification_settings_keyboard,
    get_language_keyboard,
    get_auto_renewal_keyboard,
    get_security_settings_keyboard,
    get_history_navigation_keyboard
)
import logging

logger = logging.getLogger(__name__)
profile_service = ProfileService()

async def handle_profile_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle profile-related callback queries."""
    query = update.callback_query
    await query.answer()
    
    try:
        action, *args = query.data.split(":")
        
        if action == "profile":
            await handle_profile_menu(query, context)
        elif action == "settings":
            await handle_settings_menu(query, context)
        elif action == "notify":
            await handle_notification_settings(query, context)
        elif action == "lang":
            await handle_language_settings(query, context)
        elif action == "renewal":
            await handle_auto_renewal(query, context)
        elif action == "security":
            await handle_security_settings(query, context)
        elif action == "history":
            await handle_history_navigation(query, context)
            
    except Exception as e:
        logger.error(f"Error handling profile callback: {e}")
        await query.edit_message_text(
            "❌ خطا در پردازش درخواست شما. لطفاً دوباره تلاش کنید.",
            reply_markup=get_profile_menu_keyboard()
        )

async def handle_profile_menu(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle main profile menu callbacks."""
    sub_action = query.data.split(":")[1]
    
    if sub_action == "info":
        profile = await profile_service.get_profile(query.from_user.id)
        message = (
            f"👤 اطلاعات پروفایل شما:\n\n"
            f"🆔 شناسه کاربری: {profile.user_id}\n"
            f"📱 شماره موبایل: {profile.phone_number}\n"
            f"📅 تاریخ ثبت نام: {profile.created_at.strftime('%Y-%m-%d')}\n"
            f"🎯 امتیاز: {profile.points}\n\n"
            f"📊 وضعیت اشتراک:\n"
            f"• {'✅ فعال' if profile.active_subscription else '❌ غیرفعال'}\n"
            f"• تاریخ انقضا: {profile.subscription_expiry.strftime('%Y-%m-%d') if profile.subscription_expiry else 'نامشخص'}"
        )
        await query.edit_message_text(message, reply_markup=get_profile_menu_keyboard())
        
    elif sub_action == "settings":
        await query.edit_message_text(
            "⚙️ تنظیمات پروفایل شما:",
            reply_markup=get_settings_keyboard()
        )
        
    elif sub_action == "subscriptions":
        subscriptions = await profile_service.get_subscription_history(query.from_user.id)
        if not subscriptions:
            await query.edit_message_text(
                "📊 شما هنوز هیچ اشتراکی نداشته‌اید.",
                reply_markup=get_profile_menu_keyboard()
            )
            return
            
        message = "📊 تاریخچه اشتراک‌های شما:\n\n"
        for sub in subscriptions[:5]:  # Show last 5 subscriptions
            message += (
                f"• {sub.plan.name} - {sub.created_at.strftime('%Y-%m-%d')}\n"
                f"  مدت: {sub.duration} روز - قیمت: {sub.price} تومان\n"
            )
            
        await query.edit_message_text(
            message,
            reply_markup=get_history_navigation_keyboard(1, (len(subscriptions) + 4) // 5)
        )
        
    elif sub_action == "transactions":
        transactions = await profile_service.get_transaction_history(query.from_user.id)
        if not transactions:
            await query.edit_message_text(
                "💰 شما هنوز هیچ تراکنشی نداشته‌اید.",
                reply_markup=get_profile_menu_keyboard()
            )
            return
            
        message = "💰 تاریخچه تراکنش‌های شما:\n\n"
        for trans in transactions[:5]:  # Show last 5 transactions
            message += (
                f"• {trans.type} - {trans.created_at.strftime('%Y-%m-%d')}\n"
                f"  مبلغ: {trans.amount} تومان - وضعیت: {trans.status}\n"
            )
            
        await query.edit_message_text(
            message,
            reply_markup=get_history_navigation_keyboard(1, (len(transactions) + 4) // 5)
        )
        
    elif sub_action == "points":
        points_history = await profile_service.get_points_history(query.from_user.id)
        if not points_history:
            await query.edit_message_text(
                "🎯 شما هنوز هیچ امتیازی کسب نکرده‌اید.",
                reply_markup=get_profile_menu_keyboard()
            )
            return
            
        message = "🎯 تاریخچه امتیازات شما:\n\n"
        for point in points_history[:5]:  # Show last 5 points records
            message += (
                f"• {point.points} امتیاز - {point.created_at.strftime('%Y-%m-%d')}\n"
                f"  دلیل: {point.reason}\n"
            )
            
        await query.edit_message_text(
            message,
            reply_markup=get_history_navigation_keyboard(1, (len(points_history) + 4) // 5)
        )
        
    elif sub_action == "referral":
        referral_info = await profile_service.get_referral_info(query.from_user.id)
        message = (
            f"👥 اطلاعات سیستم معرفی شما:\n\n"
            f"🔑 کد معرفی شما: {referral_info.referral_code}\n"
            f"👤 تعداد کاربران معرفی شده: {referral_info.referred_count}\n"
            f"💰 مجموع امتیازات کسب شده: {referral_info.total_rewards}\n\n"
            f"💡 برای کسب امتیاز بیشتر، کد معرفی خود را به دوستانتان بدهید!"
        )
        await query.edit_message_text(message, reply_markup=get_profile_menu_keyboard())
        
    elif sub_action == "back":
        await query.edit_message_text(
            "🔙 به منوی اصلی برگشتید.",
            reply_markup=get_profile_menu_keyboard()
        )

async def handle_settings_menu(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle settings menu callbacks."""
    sub_action = query.data.split(":")[1]
    
    if sub_action == "notifications":
        await query.edit_message_text(
            "🔔 تنظیمات اعلان‌های شما:",
            reply_markup=get_notification_settings_keyboard()
        )
        
    elif sub_action == "language":
        await query.edit_message_text(
            "🌐 زبان مورد نظر خود را انتخاب کنید:",
            reply_markup=get_language_keyboard()
        )
        
    elif sub_action == "auto_renewal":
        await query.edit_message_text(
            "🔄 تنظیمات تمدید خودکار اشتراک:",
            reply_markup=get_auto_renewal_keyboard()
        )
        
    elif sub_action == "security":
        await query.edit_message_text(
            "🔒 تنظیمات امنیتی حساب شما:",
            reply_markup=get_security_settings_keyboard()
        )
        
    elif sub_action == "back":
        await query.edit_message_text(
            "🔙 به منوی پروفایل برگشتید.",
            reply_markup=get_profile_menu_keyboard()
        )

async def handle_notification_settings(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle notification settings callbacks."""
    sub_action = query.data.split(":")[1]
    
    if sub_action == "back":
        await query.edit_message_text(
            "🔙 به منوی تنظیمات برگشتید.",
            reply_markup=get_settings_keyboard()
        )
    else:
        # Update notification settings
        await profile_service.update_profile(
            query.from_user.id,
            {f"notify_{sub_action}": True}  # Toggle the specific notification
        )
        await query.answer("✅ تنظیمات اعلان با موفقیت بروزرسانی شد.")

async def handle_language_settings(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle language settings callbacks."""
    sub_action = query.data.split(":")[1]
    
    if sub_action == "back":
        await query.edit_message_text(
            "🔙 به منوی تنظیمات برگشتید.",
            reply_markup=get_settings_keyboard()
        )
    else:
        # Update language preference
        await profile_service.update_profile(
            query.from_user.id,
            {"language": sub_action}
        )
        await query.answer("✅ زبان با موفقیت تغییر کرد.")

async def handle_auto_renewal(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle auto-renewal settings callbacks."""
    sub_action = query.data.split(":")[1]
    
    if sub_action == "back":
        await query.edit_message_text(
            "🔙 به منوی تنظیمات برگشتید.",
            reply_markup=get_settings_keyboard()
        )
    else:
        # Update auto-renewal setting
        await profile_service.update_profile(
            query.from_user.id,
            {"auto_renewal": sub_action == "enable"}
        )
        await query.answer("✅ تنظیمات تمدید خودکار با موفقیت بروزرسانی شد.")

async def handle_security_settings(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle security settings callbacks."""
    sub_action = query.data.split(":")[1]
    
    if sub_action == "back":
        await query.edit_message_text(
            "🔙 به منوی تنظیمات برگشتید.",
            reply_markup=get_settings_keyboard()
        )
    elif sub_action == "password":
        # Start password change flow
        context.user_data["security_action"] = "password"
        await query.edit_message_text(
            "🔑 لطفاً رمز عبور جدید خود را وارد کنید:",
            reply_markup=get_security_settings_keyboard()
        )
    elif sub_action == "phone":
        # Start phone change flow
        context.user_data["security_action"] = "phone"
        await query.edit_message_text(
            "📱 لطفاً شماره موبایل جدید خود را وارد کنید:",
            reply_markup=get_security_settings_keyboard()
        )
    elif sub_action == "2fa":
        # Start 2FA setup flow
        context.user_data["security_action"] = "2fa"
        await query.edit_message_text(
            "🔐 برای فعال‌سازی احراز هویت دو مرحله‌ای، لطفاً مراحل زیر را دنبال کنید:\n\n"
            "1. اپلیکیشن Google Authenticator را نصب کنید\n"
            "2. کد QR را اسکن کنید\n"
            "3. کد 6 رقمی را وارد کنید",
            reply_markup=get_security_settings_keyboard()
        )
    elif sub_action == "devices":
        # Show connected devices
        await query.edit_message_text(
            "📋 دستگاه‌های متصل به حساب شما:\n\n"
            "• دستگاه فعلی\n"
            "• دستگاه قبلی\n\n"
            "برای حذف دستگاه‌ها، روی آن‌ها کلیک کنید.",
            reply_markup=get_security_settings_keyboard()
        )

async def handle_history_navigation(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle history navigation callbacks."""
    sub_action, *args = query.data.split(":")
    
    if sub_action == "back":
        await query.edit_message_text(
            "🔙 به منوی پروفایل برگشتید.",
            reply_markup=get_profile_menu_keyboard()
        )
    else:
        # Handle pagination
        page = int(args[0])
        # Update message with new page content
        # This would require fetching the appropriate history data
        # and formatting it based on the current section
        pass 