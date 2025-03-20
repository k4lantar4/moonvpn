"""
Callback handlers for user profile management in MoonVPN Telegram Bot.
"""

from telegram import Update
from telegram.ext import ContextTypes, CallbackContext
from app.bot.services.profile_service import ProfileService
from app.bot.services.usage_service import UsageService
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
from typing import Optional
from app.core.config import settings
from app.bot.utils.logger import setup_logger
from app.bot.services.vpn_service import VPNService
from app.bot.keyboards import (
    get_main_menu_keyboard,
    get_status_keyboard,
    get_usage_export_keyboard
)
from app.bot.services.export_service import ExportService

logger = logging.getLogger(__name__)
profile_service = ProfileService()
vpn_service = VPNService()
usage_service = UsageService()
export_service = ExportService()

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

async def handle_status_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callback queries from status keyboard."""
    query = update.callback_query
    await query.answer()
    
    try:
        action = query.data
        
        if action == "get_config":
            # Get VPN configuration
            config = await vpn_service.get_account_config(query.from_user.id)
            await query.message.reply_text(
                f"🔐 *کانفیگ VPN شما*\n\n"
                f"```\n{config}\n```\n\n"
                "⚠️ لطفاً این کانفیگ را در جای امنی نگهداری کنید.",
                parse_mode='Markdown'
            )
            
        elif action == "renew":
            # Get available renewal plans
            db = next(get_db())
            plans = await vpn_service.get_renewal_plans(db)
            
            if not plans:
                await query.message.reply_text(
                    "❌ در حال حاضر هیچ پلن تمدیدی در دسترس نیست.",
                    parse_mode='Markdown'
                )
                return
            
            await query.message.reply_text(
                "🔄 *تمدید اشتراک*\n\n"
                "لطفاً یک پلن تمدید را انتخاب کنید:",
                parse_mode='Markdown',
                reply_markup=get_renewal_keyboard(plans)
            )
            
        elif action.startswith("renew_plan_"):
            # Handle plan selection for renewal
            plan_id = action.split("_")[2]
            db = next(get_db())
            
            try:
                result = await vpn_service.renew_subscription(
                    user_id=query.from_user.id,
                    plan_id=plan_id,
                    db=db
                )
                
                await query.message.reply_text(
                    result["message"],
                    parse_mode='Markdown',
                    reply_markup=get_status_keyboard({"has_account": True, "status": "active"})
                )
                
            except HTTPException as e:
                await query.message.reply_text(
                    f"❌ خطا در تمدید اشتراک: {e.detail}",
                    parse_mode='Markdown'
                )
                
        elif action == "back_to_status":
            # Return to status view
            status_info = await vpn_service.get_account_status(query.from_user.id)
            await query.message.reply_text(
                status_info["message"],
                parse_mode='Markdown',
                reply_markup=get_status_keyboard(status_info)
            )
            
        elif action == "change_server":
            # Start server change process
            db = next(get_db())
            locations = await vpn_service.get_available_locations(db)
            
            if not locations:
                await query.message.reply_text(
                    "❌ در حال حاضر هیچ سروری در دسترس نیست.",
                    parse_mode='Markdown'
                )
                return
            
            await query.message.reply_text(
                "🌍 *تغییر سرور*\n\n"
                "لطفاً سرور جدید را انتخاب کنید:",
                parse_mode='Markdown',
                reply_markup=get_server_selection_keyboard(locations)
            )
            
        elif action.startswith("select_server_"):
            # Handle server selection
            location_id = action.split("_")[2]
            db = next(get_db())
            
            try:
                # Get user's current account
                account = await vpn_service.vpn_account_service.get_by_user_id(query.from_user.id)
                if not account:
                    raise HTTPException(
                        status_code=404,
                        detail="No active VPN account found"
                    )
                
                # Change server
                updated_account = await vpn_service.change_server(
                    account_id=account.id,
                    new_location_id=location_id,
                    db=db
                )
                
                # Get new server info
                server = await vpn_service.server_service.get_by_id(updated_account.server_id)
                
                await query.message.reply_text(
                    f"✅ *تغییر سرور با موفقیت انجام شد!*\n\n"
                    f"🌍 سرور جدید: {server.location.name}\n"
                    f"⚡️ وضعیت: فعال\n\n"
                    "برای دریافت کانفیگ جدید، از منوی اصلی استفاده کنید.",
                    parse_mode='Markdown',
                    reply_markup=get_status_keyboard({"has_account": True, "status": "active"})
                )
                
            except HTTPException as e:
                await query.message.reply_text(
                    f"❌ خطا در تغییر سرور: {e.detail}",
                    parse_mode='Markdown'
                )
                
        elif action == "usage_details":
            # Show analytics dashboard
            await query.message.reply_text(
                "📊 *داشبورد تحلیل مصرف VPN*\n\n"
                "لطفاً بخش مورد نظر خود را انتخاب کنید:",
                parse_mode='Markdown',
                reply_markup=get_analytics_dashboard_keyboard()
            )
            
        elif action == "analytics_chart":
            try:
                # Get usage history for chart
                history = await usage_service.get_usage_history(query.from_user.id, days=30)
                
                if not history:
                    await query.message.reply_text(
                        "📊 هیچ داده‌ای برای نمایش نمودار موجود نیست.",
                        parse_mode='Markdown'
                    )
                    return
                
                # Generate and send chart
                file_path = await export_service.generate_usage_chart(
                    user_id=query.from_user.id,
                    history=history
                )
                
                await query.message.reply_photo(
                    photo=open(file_path, 'rb'),
                    caption="📈 نمودار مصرف VPN شما در 30 روز گذشته",
                    reply_markup=get_analytics_dashboard_keyboard()
                )
                
            except Exception as e:
                logger.error(f"Error generating analytics chart: {str(e)}")
                await query.message.reply_text(
                    "❌ خطا در ایجاد نمودار. لطفاً دوباره تلاش کنید.",
                    parse_mode='Markdown'
                )
                
        elif action == "analytics_stats":
            try:
                # Get usage statistics
                usage = await usage_service.get_usage_details(query.from_user.id)
                stats = await usage_service.get_usage_stats(query.from_user.id)
                
                message = (
                    "📈 *آمار کلی مصرف VPN*\n\n"
                    f"*مصرف روزانه:*\n"
                    f"• امروز: {usage['daily_usage']:.2f}GB\n"
                    f"• میانگین: {usage['average_daily']:.2f}GB\n"
                    f"• حداکثر: {usage['max_daily']:.2f}GB\n\n"
                    f"*مدت زمان استفاده:*\n"
                    f"• کل: {stats['total_duration']:.1f} ساعت\n"
                    f"• میانگین هر جلسه: {stats['average_session']:.1f} دقیقه\n"
                    f"• حداکثر در روز: {stats['max_daily_duration']:.1f} ساعت\n\n"
                    f"*سرورها:*\n"
                    f"• پرکاربردترین: {stats['most_used_server']}\n"
                    f"• تعداد سرورهای استفاده شده: {stats['server_count']}\n"
                    f"• مصرف در سرور اصلی: {stats['server_usage']:.2f}GB"
                )
                
                await query.message.reply_text(
                    message,
                    parse_mode='Markdown',
                    reply_markup=get_analytics_dashboard_keyboard()
                )
                
            except Exception as e:
                logger.error(f"Error getting analytics stats: {str(e)}")
                await query.message.reply_text(
                    "❌ خطا در دریافت آمار. لطفاً دوباره تلاش کنید.",
                    parse_mode='Markdown'
                )
                
        elif action == "analytics_servers":
            try:
                # Get server usage statistics
                server_stats = await usage_service.get_server_usage_stats(query.from_user.id)
                
                if not server_stats:
                    await query.message.reply_text(
                        "🌍 هیچ اطلاعاتی از استفاده از سرورها موجود نیست.",
                        parse_mode='Markdown'
                    )
                    return
                
                message = "🌍 *آمار استفاده از سرورها*\n\n"
                for server in server_stats:
                    message += (
                        f"*{server['name']}*\n"
                        f"• مصرف کل: {server['total_usage']:.2f}GB\n"
                        f"• مدت زمان: {server['duration']:.1f} ساعت\n"
                        f"• تعداد اتصال: {server['connection_count']}\n\n"
                    )
                
                await query.message.reply_text(
                    message,
                    parse_mode='Markdown',
                    reply_markup=get_analytics_dashboard_keyboard()
                )
                
            except Exception as e:
                logger.error(f"Error getting server analytics: {str(e)}")
                await query.message.reply_text(
                    "❌ خطا در دریافت آمار سرورها. لطفاً دوباره تلاش کنید.",
                    parse_mode='Markdown'
                )
                
        elif action == "analytics_timing":
            try:
                # Get timing statistics
                timing_stats = await usage_service.get_timing_stats(query.from_user.id)
                
                message = (
                    "⏱️ *آمار زمان‌بندی استفاده*\n\n"
                    f"*ساعات پرکاربرد:*\n"
                    f"• صبح (6-12): {timing_stats['morning_usage']:.1f} ساعت\n"
                    f"• بعد از ظهر (12-18): {timing_stats['afternoon_usage']:.1f} ساعت\n"
                    f"• شب (18-24): {timing_stats['evening_usage']:.1f} ساعت\n"
                    f"• نیمه شب (0-6): {timing_stats['night_usage']:.1f} ساعت\n\n"
                    f"*روزهای هفته:*\n"
                    f"• شنبه تا چهارشنبه: {timing_stats['weekday_usage']:.1f} ساعت\n"
                    f"• پنجشنبه و جمعه: {timing_stats['weekend_usage']:.1f} ساعت\n\n"
                    f"*میانگین روزانه:*\n"
                    f"• {timing_stats['average_daily_duration']:.1f} ساعت"
                )
                
                await query.message.reply_text(
                    message,
                    parse_mode='Markdown',
                    reply_markup=get_analytics_dashboard_keyboard()
                )
                
            except Exception as e:
                logger.error(f"Error getting timing analytics: {str(e)}")
                await query.message.reply_text(
                    "❌ خطا در دریافت آمار زمان‌بندی. لطفاً دوباره تلاش کنید.",
                    parse_mode='Markdown'
                )
                
        elif action == "support":
            # Redirect to support
            await query.message.reply_text(
                "💬 *پشتیبانی*\n\n"
                "برای دریافت کمک با پشتیبانی ما تماس بگیرید:\n"
                f"@{settings.SUPPORT_USERNAME}",
                parse_mode='Markdown'
            )
            
        elif action == "main_menu":
            # Return to main menu
            await query.message.reply_text(
                "🔙 بازگشت به منوی اصلی",
                reply_markup=get_main_menu_keyboard()
            )
            
        elif action == "export_analytics":
            # Show export options
            await query.message.reply_text(
                "📊 *گزینه‌های خروجی گزارش مصرف*\n\n"
                "لطفاً فرمت مورد نظر خود را انتخاب کنید:",
                parse_mode='Markdown',
                reply_markup=get_usage_export_keyboard()
            )
            
        elif action.startswith("export_"):
            # Handle export format selection
            export_format = action.split("_")[1]
            
            try:
                # Get usage data
                usage = await usage_service.get_usage_details(query.from_user.id)
                stats = await usage_service.get_usage_stats(query.from_user.id)
                history = await usage_service.get_usage_history(query.from_user.id, days=30)
                
                # Generate export based on format
                if export_format == "pdf":
                    file_path = await export_service.generate_pdf_report(
                        user_id=query.from_user.id,
                        usage=usage,
                        stats=stats,
                        history=history
                    )
                    await query.message.reply_document(
                        document=open(file_path, 'rb'),
                        filename=f"vpn_usage_report_{query.from_user.id}.pdf",
                        caption="📊 گزارش مصرف VPN شما"
                    )
                    
                elif export_format == "chart":
                    file_path = await export_service.generate_usage_chart(
                        user_id=query.from_user.id,
                        history=history
                    )
                    await query.message.reply_photo(
                        photo=open(file_path, 'rb'),
                        caption="📈 نمودار مصرف VPN شما"
                    )
                    
                elif export_format == "text":
                    report_text = await export_service.generate_text_report(
                        usage=usage,
                        stats=stats,
                        history=history
                    )
                    await query.message.reply_text(
                        report_text,
                        parse_mode='Markdown'
                    )
                    
                elif export_format == "csv":
                    file_path = await export_service.generate_csv_report(
                        user_id=query.from_user.id,
                        history=history
                    )
                    await query.message.reply_document(
                        document=open(file_path, 'rb'),
                        filename=f"vpn_usage_report_{query.from_user.id}.csv",
                        caption="📋 گزارش مصرف VPN شما"
                    )
                    
            except ValueError as e:
                await query.message.reply_text(
                    "❌ خطا در دریافت اطلاعات مصرف: حساب VPN فعالی یافت نشد.",
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"Error generating export: {str(e)}")
                await query.message.reply_text(
                    "❌ خطا در ایجاد گزارش. لطفاً دوباره تلاش کنید.",
                    parse_mode='Markdown'
                )
                
    except Exception as e:
        logger.error(f"Error handling status callback: {str(e)}")
        await query.message.reply_text(
            "❌ متأسفانه خطایی رخ داد. لطفاً دوباره تلاش کنید."
        ) 