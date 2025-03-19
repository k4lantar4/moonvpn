"""Admin handlers for the bot."""

from typing import Dict, Any, Optional, List
import os
import logging
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from telegram.constants import ParseMode
from django.conf import settings

from .decorators import require_admin
from .start import start_command, back_to_main
from .admin.backup import get_backup_handlers
from .admin.constants import (
    SELECTING_ACTION,
    SELECTING_BACKUP_ACTION,
    CONFIRMING_BACKUP_RESTORE,
    CONFIRMING_BACKUP_DELETE,
    ADMIN_MENU,
    ADMIN_BACKUP,
    BACK_TO_MAIN,
)
from core.utils.helpers import admin_only
from core.utils.helpers import format_number, get_user, human_readable_size
from backend.accounts.services import AccountService
from backend.payments.services import PaymentService

logger = logging.getLogger(__name__)

# Define conversation states
ADMIN_MENU, PENDING_PAYMENTS, SERVER_STATS, BROADCAST_MESSAGE, CONFIRM_BROADCAST, TRAFFIC_STATS, INCOME_REPORTS, DISCOUNT_CODES = range(8)

@admin_only
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Admin command handler"""
    # Create admin menu
    message = (
        "👨‍💼 <b>پنل مدیریت MoonVPN</b>\n\n"
        "از طریق این پنل می‌توانید به مدیریت کاربران، پرداخت‌ها، سرورها و گزارش‌های سیستم دسترسی داشته باشید."
    )
    
    keyboard = [
        [InlineKeyboardButton("💰 پرداخت‌های در انتظار تایید", callback_data="admin_pending_payments")],
        [InlineKeyboardButton("📊 آمار سرورها", callback_data="admin_server_stats")],
        [InlineKeyboardButton("📈 آمار مصرف ترافیک", callback_data="admin_traffic_stats")],
        [InlineKeyboardButton("💹 گزارش درآمد", callback_data="admin_income_reports")],
        [InlineKeyboardButton("🏷️ مدیریت کد تخفیف", callback_data="admin_discount_codes")],
        [InlineKeyboardButton("📨 ارسال پیام به کاربران", callback_data="admin_broadcast")],
        [InlineKeyboardButton("❌ بستن", callback_data="admin_close")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )
    
    return ADMIN_MENU

async def admin_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle admin menu button clicks"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "admin_close":
        await query.message.edit_text(
            "✅ پنل مدیریت بسته شد.",
            parse_mode=ParseMode.HTML
        )
        return ConversationHandler.END
    
    elif query.data == "admin_pending_payments":
        return await pending_payments_handler(update, context)
    
    elif query.data == "admin_server_stats":
        return await server_stats_handler(update, context)
    
    elif query.data == "admin_broadcast":
        return await broadcast_handler(update, context)
    
    elif query.data == "admin_traffic_stats":
        return await traffic_stats_handler(update, context)
    
    elif query.data == "admin_income_reports":
        return await income_reports_handler(update, context)
    
    elif query.data == "admin_discount_codes":
        return await discount_codes_handler(update, context)
    
    # Back to admin menu
    elif query.data == "admin_back_to_menu":
        # Reuse admin command to show menu
        message = (
            "👨‍💼 <b>پنل مدیریت MoonVPN</b>\n\n"
            "از طریق این پنل می‌توانید به مدیریت کاربران، پرداخت‌ها، سرورها و گزارش‌های سیستم دسترسی داشته باشید."
        )
        
        keyboard = [
            [InlineKeyboardButton("💰 پرداخت‌های در انتظار تایید", callback_data="admin_pending_payments")],
            [InlineKeyboardButton("📊 آمار سرورها", callback_data="admin_server_stats")],
            [InlineKeyboardButton("📈 آمار مصرف ترافیک", callback_data="admin_traffic_stats")],
            [InlineKeyboardButton("💹 گزارش درآمد", callback_data="admin_income_reports")],
            [InlineKeyboardButton("🏷️ مدیریت کد تخفیف", callback_data="admin_discount_codes")],
            [InlineKeyboardButton("📨 ارسال پیام به کاربران", callback_data="admin_broadcast")],
            [InlineKeyboardButton("❌ بستن", callback_data="admin_close")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.edit_text(
            message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
        
        return ADMIN_MENU
    
    return ADMIN_MENU

async def pending_payments_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle pending payments menu"""
    query = update.callback_query
    
    try:
        # Get pending payments
        pending_payments = PaymentService.get_pending_payments()
        
        if not pending_payments:
            await query.message.edit_text(
                "💰 <b>پرداخت‌های در انتظار تایید</b>\n\n"
                "در حال حاضر هیچ پرداخت در انتظار تاییدی وجود ندارد.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="admin_back_to_menu")]]),
                parse_mode=ParseMode.HTML
            )
            return ADMIN_MENU
        
        # Show pending payments
        message = "💰 <b>پرداخت‌های در انتظار تایید</b>\n\n"
        
        keyboard = []
        for payment in pending_payments:
            # Format payment info
            payment_id = payment.id
            user_info = f"{payment.user.username or payment.user.full_name or 'کاربر'} (ID: {payment.user.telegram_id})"
            plan_name = payment.plan.name
            amount = format_number(payment.amount)
            date = payment.created_at.strftime("%Y-%m-%d %H:%M")
            
            message += (
                f"🔹 <b>پرداخت #{payment_id}</b>\n"
                f"👤 کاربر: {user_info}\n"
                f"📋 پلن: {plan_name}\n"
                f"💰 مبلغ: {amount} تومان\n"
                f"📅 تاریخ: {date}\n\n"
            )
            
            # Add verify/reject buttons for each payment
            keyboard.append([
                InlineKeyboardButton(f"✅ تایید #{payment_id}", callback_data=f"verify_payment_{payment_id}"),
                InlineKeyboardButton(f"❌ رد #{payment_id}", callback_data=f"reject_payment_{payment_id}")
            ])
        
        # Add back button
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="admin_back_to_menu")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.edit_text(
            message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
        
        return PENDING_PAYMENTS
        
    except Exception as e:
        logger.exception(f"Error in pending_payments_handler: {str(e)}")
        await query.message.edit_text(
            "⚠️ خطایی در دریافت لیست پرداخت‌ها رخ داد.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="admin_back_to_menu")]]),
            parse_mode=ParseMode.HTML
        )
        return ADMIN_MENU

async def pending_payment_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle payment verification or rejection"""
    query = update.callback_query
    await query.answer()
    
    action, payment_id = query.data.split("_")[0], int(query.data.split("_")[2])
    
    try:
        if action == "verify":
            # Verify payment
            success, payment, error = PaymentService.admin_verify_payment(payment_id)
            
            if not success:
                await query.message.reply_text(
                    f"⚠️ <b>خطا در تایید پرداخت:</b>\n{error}",
                    parse_mode=ParseMode.HTML
                )
                return PENDING_PAYMENTS
            
            # Create account for the user
            success, account_data, error = AccountService.create_account_from_payment(payment)
            
            if success and account_data:
                # Notify user
                user_id = payment.user.telegram_id
                subscription_link = account_data.get('subscription_link', '')
                
                # Send a message to the user
                await context.bot.send_message(
                    chat_id=user_id,
                    text=(
                        f"🎉 <b>پرداخت شما تایید شد!</b>\n\n"
                        f"✅ اشتراک شما فعال شد.\n\n"
                        f"📲 <b>لینک اتصال شما:</b>\n"
                        f"<code>{subscription_link}</code>\n\n"
                        f"⏱ مدت زمان: <b>{account_data.get('days_left', 0)} روز</b>\n"
                        f"📦 حجم کل: <b>{human_readable_size(account_data.get('traffic_limit_bytes', 0))}</b>\n\n"
                        f"🔍 برای مشاهده وضعیت اشتراک خود، از دستور /status استفاده کنید."
                    ),
                    parse_mode=ParseMode.HTML
                )
                
                # Send confirmation to admin
                await query.message.reply_text(
                    f"✅ <b>پرداخت #{payment_id} با موفقیت تایید شد.</b>\n"
                    f"اشتراک برای کاربر فعال شد و پیام اطلاع‌رسانی ارسال گردید.",
                    parse_mode=ParseMode.HTML
                )
            else:
                # Notify admin about the error
                await query.message.reply_text(
                    f"⚠️ <b>پرداخت تایید شد اما در ایجاد اشتراک خطا رخ داد:</b>\n{error}\n\n"
                    f"لطفا به صورت دستی اشتراک را برای کاربر فعال کنید.",
                    parse_mode=ParseMode.HTML
                )
                
        elif action == "reject":
            # Reject payment
            success, payment, error = PaymentService.admin_reject_payment(payment_id)
            
            if not success:
                await query.message.reply_text(
                    f"⚠️ <b>خطا در رد پرداخت:</b>\n{error}",
                    parse_mode=ParseMode.HTML
                )
                return PENDING_PAYMENTS
            
            # Notify user
            user_id = payment.user.telegram_id
            
            # Send a message to the user
            await context.bot.send_message(
                chat_id=user_id,
                text=(
                    f"❌ <b>پرداخت شما تایید نشد</b>\n\n"
                    f"متاسفانه پرداخت شما مورد تایید قرار نگرفت.\n"
                    f"دلیل: اطلاعات پرداخت نامعتبر است.\n\n"
                    f"در صورت نیاز به پشتیبانی با ادمین تماس بگیرید."
                ),
                parse_mode=ParseMode.HTML
            )
            
            # Send confirmation to admin
            await query.message.reply_text(
                f"❌ <b>پرداخت #{payment_id} رد شد.</b>\n"
                f"پیام اطلاع‌رسانی به کاربر ارسال گردید.",
                parse_mode=ParseMode.HTML
            )
        
        # Refresh pending payments list
        return await pending_payments_handler(update, context)
        
    except Exception as e:
        logger.exception(f"Error in pending_payment_action: {str(e)}")
        await query.message.reply_text(
            "⚠️ خطایی در پردازش پرداخت رخ داد.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="admin_back_to_menu")]]),
            parse_mode=ParseMode.HTML
        )
        return ADMIN_MENU

async def server_stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show server statistics"""
    query = update.callback_query
    
    try:
        # Get server stats
        success, stats, error = AccountService.get_server_stats()
        
        if not success or not stats:
            await query.message.edit_text(
                f"⚠️ <b>خطا در دریافت آمار سرورها:</b>\n{error or 'خطای نامشخص'}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="admin_back_to_menu")]]),
                parse_mode=ParseMode.HTML
            )
            return ADMIN_MENU
        
        # Format stats message
        message = "📊 <b>آمار سرورها</b>\n\n"
        
        for server in stats:
            name = server.get('name', 'نامشخص')
            status = "🟢 آنلاین" if server.get('is_online', False) else "🔴 آفلاین"
            user_count = server.get('user_count', 0)
            cpu_usage = server.get('cpu_usage', 0)
            memory_usage = server.get('memory_usage', '0')
            disk_usage = server.get('disk_usage', '0')
            traffic_today = server.get('traffic_today', '0')
            
            message += (
                f"🖥️ <b>{name}</b>\n"
                f"وضعیت: {status}\n"
                f"👥 تعداد کاربران: {user_count}\n"
                f"🔄 CPU: {cpu_usage}%\n"
                f"💾 حافظه: {memory_usage}\n"
                f"💿 دیسک: {disk_usage}\n"
                f"📊 ترافیک امروز: {traffic_today}\n\n"
            )
        
        # Add refresh and back buttons
        keyboard = [
            [InlineKeyboardButton("🔄 بروزرسانی", callback_data="admin_server_stats")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_back_to_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.edit_text(
            message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
        
        return SERVER_STATS
        
    except Exception as e:
        logger.exception(f"Error in server_stats_handler: {str(e)}")
        await query.message.edit_text(
            "⚠️ خطایی در دریافت آمار سرورها رخ داد.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="admin_back_to_menu")]]),
            parse_mode=ParseMode.HTML
        )
        return ADMIN_MENU

async def broadcast_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle broadcast message to users"""
    query = update.callback_query
    
    await query.message.edit_text(
        "📨 <b>ارسال پیام به کاربران</b>\n\n"
        "لطفا متن پیامی که می‌خواهید برای تمام کاربران ارسال شود را وارد کنید.\n"
        "پشتیبانی از <b>HTML</b> فعال است.\n\n"
        "برای انصراف از دستور /cancel استفاده کنید.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="admin_back_to_menu")]]),
        parse_mode=ParseMode.HTML
    )
    
    return BROADCAST_MESSAGE

async def broadcast_message_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process broadcast message input"""
    message_text = update.message.text
    
    if message_text.startswith("/cancel"):
        await update.message.reply_text(
            "❌ ارسال پیام به کاربران لغو شد.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت به منو", callback_data="admin_back_to_menu")]]),
            parse_mode=ParseMode.HTML
        )
        return ADMIN_MENU
    
    # Store message in context
    context.user_data['broadcast_message'] = message_text
    
    # Get user count
    total_users = 0  # This should be fetched from the database
    
    # Ask for confirmation
    await update.message.reply_text(
        f"📨 <b>تایید ارسال پیام</b>\n\n"
        f"پیام شما به <b>{total_users}</b> کاربر ارسال خواهد شد.\n\n"
        f"<b>متن پیام:</b>\n"
        f"{message_text}\n\n"
        f"آیا از ارسال این پیام اطمینان دارید؟",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ بله، ارسال شود", callback_data="confirm_broadcast")],
            [InlineKeyboardButton("❌ خیر، انصراف", callback_data="cancel_broadcast")]
        ]),
        parse_mode=ParseMode.HTML
    )
    
    return CONFIRM_BROADCAST

async def confirm_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle broadcast confirmation"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "cancel_broadcast":
        await query.message.edit_text(
            "❌ ارسال پیام به کاربران لغو شد.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت به منو", callback_data="admin_back_to_menu")]]),
            parse_mode=ParseMode.HTML
        )
        return ADMIN_MENU
    
    # Get message from context
    message_text = context.user_data.get('broadcast_message', '')
    
    if not message_text:
        await query.message.edit_text(
            "⚠️ متن پیام یافت نشد. لطفا دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت به منو", callback_data="admin_back_to_menu")]]),
            parse_mode=ParseMode.HTML
        )
        return ADMIN_MENU
    
    # Send message to all users (this is a placeholder)
    # In a real implementation, you would get all users from the database
    # and send the message to each one in batches
    
    # Show sending progress
    progress_message = await query.message.edit_text(
        "📨 <b>در حال ارسال پیام...</b>\n\n"
        "لطفا صبر کنید. این عملیات ممکن است چند دقیقه طول بکشد.",
        parse_mode=ParseMode.HTML
    )
    
    # Here you would implement the actual broadcast mechanism
    # This is just a placeholder
    sent_count = 0
    failed_count = 0
    
    # Update progress message with results
    await progress_message.edit_text(
        f"✅ <b>ارسال پیام به کاربران انجام شد</b>\n\n"
        f"• پیام به <b>{sent_count}</b> کاربر با موفقیت ارسال شد.\n"
        f"• ارسال به <b>{failed_count}</b> کاربر با خطا مواجه شد.\n\n",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت به منو", callback_data="admin_back_to_menu")]]),
        parse_mode=ParseMode.HTML
    )
    
    # Clear broadcast message from context
    if 'broadcast_message' in context.user_data:
        del context.user_data['broadcast_message']
    
    return ADMIN_MENU

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the conversation."""
    await update.message.reply_text(
        "❌ عملیات لغو شد."
    )
    return ConversationHandler.END

async def traffic_stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle traffic statistics menu"""
    query = update.callback_query
    await query.answer()
    
    try:
        # دریافت آمار مصرف ترافیک
        from core.services.server.manager import ServerManager
        server_manager = ServerManager()
        servers = server_manager.get_all_servers()
        
        message = "📈 <b>آمار مصرف ترافیک</b>\n\n"
        
        if not servers:
            message += "⚠️ هیچ سروری یافت نشد."
        else:
            total_traffic_up = 0
            total_traffic_down = 0
            
            # محاسبه و نمایش مصرف ترافیک به تفکیک سرور
            for server in servers:
                server_name = server.get('name', 'نامشخص')
                server_traffic = server_manager.get_server_traffic(server.get('id'))
                
                traffic_up = server_traffic.get('up', 0)
                traffic_down = server_traffic.get('down', 0)
                total_traffic = traffic_up + traffic_down
                
                total_traffic_up += traffic_up
                total_traffic_down += traffic_down
                
                message += (
                    f"🌐 <b>سرور {server_name}</b>\n"
                    f"📤 آپلود: {human_readable_size(traffic_up)}\n"
                    f"📥 دانلود: {human_readable_size(traffic_down)}\n"
                    f"📊 مجموع: {human_readable_size(total_traffic)}\n\n"
                )
            
            # نمایش مجموع کل ترافیک
            total_traffic = total_traffic_up + total_traffic_down
            message += (
                f"🔶 <b>مجموع کل مصرف ترافیک</b>\n"
                f"📤 آپلود: {human_readable_size(total_traffic_up)}\n"
                f"📥 دانلود: {human_readable_size(total_traffic_down)}\n"
                f"📊 مجموع: {human_readable_size(total_traffic)}"
            )
        
        keyboard = [
            [InlineKeyboardButton("🔄 بروزرسانی", callback_data="admin_traffic_stats")],
            [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="admin_back_to_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.edit_text(
            message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
        
        return TRAFFIC_STATS
        
    except Exception as e:
        logger.exception(f"Error in traffic_stats_handler: {str(e)}")
        await query.message.edit_text(
            "⚠️ خطایی در دریافت آمار مصرف ترافیک رخ داد.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="admin_back_to_menu")]]),
            parse_mode=ParseMode.HTML
        )
        return ADMIN_MENU

async def income_reports_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle income reports menu"""
    query = update.callback_query
    await query.answer()
    
    try:
        # گزارش درآمد روزانه، هفتگی و ماهانه
        from bot.services.payment_service import PaymentService
        payment_service = PaymentService()
        
        daily_income = payment_service.get_income_report('daily')
        weekly_income = payment_service.get_income_report('weekly')
        monthly_income = payment_service.get_income_report('monthly')
        
        # نمایش گزارش درآمد
        message = (
            "💹 <b>گزارش درآمد</b>\n\n"
            f"🔹 <b>امروز:</b> {format_number(daily_income)} تومان\n"
            f"🔹 <b>هفته جاری:</b> {format_number(weekly_income)} تومان\n"
            f"🔹 <b>ماه جاری:</b> {format_number(monthly_income)} تومان\n\n"
        )
        
        # دریافت آمار فروش به تفکیک پلن
        plan_sales = payment_service.get_plan_sales('monthly')
        
        if plan_sales:
            message += "<b>آمار فروش به تفکیک پلن (ماه جاری):</b>\n"
            for plan_name, count, amount in plan_sales:
                message += f"🔸 {plan_name}: {count} فروش - {format_number(amount)} تومان\n"
        
        keyboard = [
            [
                InlineKeyboardButton("📅 روزانه", callback_data="admin_income_daily"),
                InlineKeyboardButton("📆 هفتگی", callback_data="admin_income_weekly"),
                InlineKeyboardButton("🗓️ ماهانه", callback_data="admin_income_monthly")
            ],
            [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="admin_back_to_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.edit_text(
            message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
        
        return INCOME_REPORTS
        
    except Exception as e:
        logger.exception(f"Error in income_reports_handler: {str(e)}")
        await query.message.edit_text(
            "⚠️ خطایی در دریافت گزارش درآمد رخ داد.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="admin_back_to_menu")]]),
            parse_mode=ParseMode.HTML
        )
        return ADMIN_MENU

async def discount_codes_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle discount codes menu"""
    query = update.callback_query
    await query.answer()
    
    try:
        # دریافت لیست کدهای تخفیف
        from bot.services.discount_service import DiscountService
        discount_service = DiscountService()
        discount_codes = discount_service.get_all_discount_codes()
        
        message = "🏷️ <b>مدیریت کد تخفیف</b>\n\n"
        
        if not discount_codes:
            message += "هیچ کد تخفیفی ثبت نشده است."
        else:
            for code in discount_codes:
                code_id = code.get('id')
                code_text = code.get('code')
                discount_value = code.get('value')
                discount_type = "درصدی" if code.get('is_percentage') else "مقداری"
                is_active = "✅ فعال" if code.get('is_active') else "❌ غیرفعال"
                expiry_date = code.get('expiry_date', 'نامحدود')
                
                message += (
                    f"🔹 <b>کد:</b> {code_text}\n"
                    f"🔸 <b>مقدار:</b> {discount_value} {'٪' if code.get('is_percentage') else ' تومان'}\n"
                    f"🔸 <b>نوع:</b> {discount_type}\n"
                    f"🔸 <b>وضعیت:</b> {is_active}\n"
                    f"🔸 <b>تاریخ انقضا:</b> {expiry_date}\n\n"
                )
        
        keyboard = [
            [InlineKeyboardButton("➕ افزودن کد تخفیف جدید", callback_data="admin_add_discount")],
            [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="admin_back_to_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.edit_text(
            message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
        
        return DISCOUNT_CODES
        
    except Exception as e:
        logger.exception(f"Error in discount_codes_handler: {str(e)}")
        await query.message.edit_text(
            "⚠️ خطایی در دریافت لیست کدهای تخفیف رخ داد.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="admin_back_to_menu")]]),
            parse_mode=ParseMode.HTML
        )
        return ADMIN_MENU

# Create admin conversation handler
admin_handler = ConversationHandler(
    entry_points=[CommandHandler("admin", admin_command)],
    states={
        ADMIN_MENU: [
            CallbackQueryHandler(admin_menu_handler, pattern=r"^admin_")
        ],
        PENDING_PAYMENTS: [
            CallbackQueryHandler(pending_payment_action, pattern=r"^(verify|reject)_payment_\d+$"),
            CallbackQueryHandler(admin_menu_handler, pattern=r"^admin_back_to_menu$")
        ],
        SERVER_STATS: [
            CallbackQueryHandler(server_stats_handler, pattern=r"^admin_server_stats$"),
            CallbackQueryHandler(admin_menu_handler, pattern=r"^admin_back_to_menu$")
        ],
        BROADCAST_MESSAGE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_message_input),
            CallbackQueryHandler(admin_menu_handler, pattern=r"^admin_back_to_menu$")
        ],
        CONFIRM_BROADCAST: [
            CallbackQueryHandler(confirm_broadcast, pattern=r"^(confirm|cancel)_broadcast$")
        ],
        TRAFFIC_STATS: [
            CallbackQueryHandler(traffic_stats_handler, pattern=r"^admin_traffic_stats$"),
            CallbackQueryHandler(admin_menu_handler, pattern=r"^admin_back_to_menu$")
        ],
        INCOME_REPORTS: [
            CallbackQueryHandler(income_reports_handler, pattern=r"^admin_income_reports$"),
            CallbackQueryHandler(admin_menu_handler, pattern=r"^admin_back_to_menu$")
        ],
        DISCOUNT_CODES: [
            CallbackQueryHandler(discount_codes_handler, pattern=r"^admin_discount_codes$"),
            CallbackQueryHandler(admin_menu_handler, pattern=r"^admin_back_to_menu$")
        ],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

# List of all admin handlers
admin_handlers = [admin_handler]