"""
VPN Traffic monitoring handler for the Telegram bot.

This module implements handlers for:
- Displaying user's traffic usage statistics
- Monitoring bandwidth consumption
- Checking subscription expiry status
- Showing service health metrics
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import math

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from telegram.constants import ParseMode

from django.utils import timezone

# Import models
try:
    from main.models import User, Server, Subscription
    from v2ray.models import Inbound, Client
    from v2ray.api_client import ThreeXUIClient
except ImportError:
    logging.warning("Django models import failed. Using mock objects for testing.")
    # Define mock classes for testing without Django
    class User:
        @staticmethod
        def get_by_telegram_id(telegram_id):
            return {"id": 1, "username": "test_user"}
    
    class Server:
        @staticmethod
        def get_active_servers():
            return [{"id": 1, "name": "Server 1", "location": "Netherlands"}]
    
    class Subscription:
        @staticmethod
        def get_active_for_user(user_id):
            return [{"id": 1, "server_id": 1, "inbound_id": 1, "client_email": "test@example.com"}]
    
    class Inbound:
        @staticmethod
        def get_by_id(inbound_id):
            return {"id": 1, "server_id": 1, "protocol": "vmess"}
    
    class Client:
        @staticmethod
        def get_by_email(email):
            return {"id": 1, "uuid": "test-uuid", "email": "test@example.com", "up": 1024*1024*50, "down": 1024*1024*200}
    
    class ThreeXUIClient:
        def __init__(self, server):
            self.server = server
        
        def get_client_traffic(self, inbound_id, email):
            return {"up": 1024*1024*50, "down": 1024*1024*200, "total": 1024*1024*250}

# Setup logging
logger = logging.getLogger("telegram_bot")

# Conversation states
(
    VIEWING_TRAFFIC,
    VIEWING_DETAILS,
) = range(2)

# Callback data patterns
TRAFFIC_CB = "vpn_traffic"
TRAFFIC_MAIN = f"{TRAFFIC_CB}_main"
TRAFFIC_DETAILS = f"{TRAFFIC_CB}_details"
TRAFFIC_RESET = f"{TRAFFIC_CB}_reset"
TRAFFIC_EXTEND = f"{TRAFFIC_CB}_extend"
TRAFFIC_BACK = f"{TRAFFIC_CB}_back"

def format_size(size_bytes: int) -> str:
    """Format bytes into human readable format."""
    if size_bytes == 0:
        return "0 B"
    
    # Define unit prefixes
    units = ["B", "KB", "MB", "GB", "TB"]
    
    # Calculate appropriate unit
    i = math.floor(math.log(size_bytes, 1024))
    i = min(i, len(units) - 1)  # Cap at the largest unit
    
    # Convert to appropriate unit
    size = size_bytes / (1024 ** i)
    
    # Format with appropriate precision
    if i == 0:  # Bytes
        return f"{int(size)} {units[i]}"
    elif size >= 100:  # Large values: 123.4 MB
        return f"{size:.1f} {units[i]}"
    else:  # Small values: 12.34 MB
        return f"{size:.2f} {units[i]}"

def format_days_left(expiry_time: datetime) -> str:
    """Format days left until expiry with appropriate emoji."""
    if not expiry_time:
        return "♾️ بدون محدودیت"
    
    now = timezone.now()
    
    if expiry_time < now:
        return "🔴 منقضی شده"
    
    days_left = (expiry_time - now).days
    hours_left = ((expiry_time - now).seconds // 3600)
    
    if days_left > 30:
        return f"🟢 {days_left} روز"
    elif days_left > 7:
        return f"🟡 {days_left} روز"
    elif days_left > 0:
        return f"🟠 {days_left} روز و {hours_left} ساعت"
    else:
        return f"🔴 {hours_left} ساعت"

def get_traffic_percentage(used: int, total: int) -> tuple:
    """Get traffic usage percentage and appropriate emoji."""
    if total == 0:  # Unlimited traffic
        percentage = 0
        emoji = "♾️"
    else:
        percentage = min(100, int((used / total) * 100))
        
        # Select emoji based on usage
        if percentage < 50:
            emoji = "🟢"  # Low usage
        elif percentage < 80:
            emoji = "🟡"  # Medium usage
        elif percentage < 95:
            emoji = "🟠"  # High usage
        else:
            emoji = "🔴"  # Critical usage
    
    return percentage, emoji

async def traffic_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show the traffic usage menu."""
    user = update.effective_user
    query = update.callback_query
    
    # Get user's language
    language = context.user_data.get("language", "en")
    
    # Create keyboard with traffic options
    keyboard = [
        [InlineKeyboardButton("📊 آمار مصرف", callback_data=TRAFFIC_DETAILS)],
        [InlineKeyboardButton("↻ بروزرسانی اطلاعات", callback_data=TRAFFIC_MAIN)],
        [InlineKeyboardButton("🔄 ریست ترافیک", callback_data=TRAFFIC_RESET)],
        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")],
    ]
    
    try:
        # Get user's active subscription
        db_user = User.objects.get(telegram_id=user.id)
        subscription = Subscription.objects.filter(user=db_user, status='active').first()
        
        if not subscription:
            # No active subscription
            message = "📊 *وضعیت مصرف ترافیک*\n\n" \
                      "⚠️ شما هیچ اشتراک فعالی ندارید. ابتدا باید یک اشتراک خریداری کنید."
            
            # Replace keyboard with buy subscription button
            keyboard = [
                [InlineKeyboardButton("🛒 خرید اشتراک", callback_data="buy_subscription")],
                [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")],
            ]
        else:
            # Get traffic data from the server
            traffic_data = None
            
            # Check if subscription has required fields
            if subscription.server and subscription.inbound_id and subscription.client_email:
                # Get traffic data
                client = ThreeXUIClient(subscription.server)
                traffic_data = client.get_client_traffic(subscription.inbound_id, subscription.client_email)
            
            # Build message
            message = "📊 *وضعیت مصرف ترافیک*\n\n"
            
            if traffic_data:
                # Calculate traffic usage
                upload = traffic_data.get("up", 0)
                download = traffic_data.get("down", 0)
                total_used = upload + download
                traffic_limit = subscription.data_limit_gb * 1024 * 1024 * 1024 if subscription.data_limit_gb > 0 else 0
                
                # Format traffic data
                upload_str = format_size(upload)
                download_str = format_size(download)
                total_used_str = format_size(total_used)
                
                if traffic_limit > 0:
                    traffic_limit_str = format_size(traffic_limit)
                    usage_percentage, usage_emoji = get_traffic_percentage(total_used, traffic_limit)
                    
                    message += f"{usage_emoji} *مصرف ترافیک:* {usage_percentage}% ({total_used_str} از {traffic_limit_str})\n"
                else:
                    message += f"♾️ *مصرف ترافیک:* {total_used_str} (بدون محدودیت)\n"
                
                message += f"⬆️ *آپلود:* {upload_str}\n"
                message += f"⬇️ *دانلود:* {download_str}\n"
                
                # Add expiry info
                if subscription.end_date:
                    expiry_str = format_days_left(subscription.end_date)
                    message += f"\n⏳ *زمان باقیمانده:* {expiry_str}\n"
                
                # Add server info
                if subscription.server:
                    message += f"\n🌐 *سرور:* {subscription.server.location}\n"
                
                # Add last update time
                message += f"\n🕒 *آخرین بروزرسانی:* {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}"
            else:
                message += "⚠️ اطلاعات مصرف ترافیک در دسترس نیست. لطفاً با پشتیبانی تماس بگیرید."
    
    except Exception as e:
        logger.error(f"Error in traffic_menu: {e}")
        message = "⚠️ خطایی در دریافت اطلاعات مصرف ترافیک رخ داد. لطفاً بعداً دوباره تلاش کنید."
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if query:
        await query.answer()
        await query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await update.message.reply_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    return VIEWING_TRAFFIC

async def traffic_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show detailed traffic statistics."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    try:
        # Get user's active subscription
        db_user = User.objects.get(telegram_id=user.id)
        subscription = Subscription.objects.filter(user=db_user, status='active').first()
        
        if not subscription:
            await query.edit_message_text(
                text="⚠️ شما هیچ اشتراک فعالی ندارید. ابتدا باید یک اشتراک خریداری کنید.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🛒 خرید اشتراک", callback_data="buy_subscription")],
                    [InlineKeyboardButton("🔙 بازگشت", callback_data=TRAFFIC_MAIN)]
                ])
            )
            return VIEWING_TRAFFIC
        
        # Check if subscription has required fields
        if not subscription.server or not subscription.inbound_id or not subscription.client_email:
            await query.edit_message_text(
                text="⚠️ اطلاعات کافی برای نمایش جزئیات مصرف ترافیک موجود نیست. لطفاً با پشتیبانی تماس بگیرید.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("💬 تماس با پشتیبانی", callback_data="support")],
                    [InlineKeyboardButton("🔙 بازگشت", callback_data=TRAFFIC_MAIN)]
                ])
            )
            return VIEWING_TRAFFIC
        
        # Update status message
        await query.edit_message_text(
            text="⏳ در حال دریافت اطلاعات مصرف ترافیک... لطفاً صبر کنید.",
            reply_markup=None
        )
        
        # Get traffic data from the server
        client = ThreeXUIClient(subscription.server)
        traffic_data = client.get_client_traffic(subscription.inbound_id, subscription.client_email)
        
        if not traffic_data:
            await query.edit_message_text(
                text="⚠️ دریافت اطلاعات مصرف ترافیک با خطا مواجه شد. لطفاً بعداً دوباره تلاش کنید.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 بازگشت", callback_data=TRAFFIC_MAIN)]
                ])
            )
            return VIEWING_TRAFFIC
        
        # Extract traffic data
        upload = traffic_data.get("up", 0)
        download = traffic_data.get("down", 0)
        total_used = upload + download
        traffic_limit = subscription.data_limit_gb * 1024 * 1024 * 1024 if subscription.data_limit_gb > 0 else 0
        
        # Calculate metrics
        upload_percentage = 0 if total_used == 0 else int((upload / total_used) * 100)
        download_percentage = 0 if total_used == 0 else int((download / total_used) * 100)
        
        # Format traffic data
        upload_str = format_size(upload)
        download_str = format_size(download)
        total_used_str = format_size(total_used)
        
        # Build message with detailed stats
        message = "📊 *آمار دقیق مصرف ترافیک*\n\n"
        
        # Subscription info
        message += f"📅 *تاریخ شروع:* {subscription.start_date.strftime('%Y-%m-%d')}\n"
        if subscription.end_date:
            message += f"⏳ *زمان باقیمانده:* {format_days_left(subscription.end_date)}\n"
        
        # Traffic usage
        message += f"\n📈 *آمار مصرف:*\n"
        
        if traffic_limit > 0:
            traffic_limit_str = format_size(traffic_limit)
            remaining = max(0, traffic_limit - total_used)
            remaining_str = format_size(remaining)
            usage_percentage, usage_emoji = get_traffic_percentage(total_used, traffic_limit)
            
            message += f"{usage_emoji} *کل مصرف:* {usage_percentage}% ({total_used_str} از {traffic_limit_str})\n"
            message += f"📉 *باقیمانده:* {remaining_str}\n"
        else:
            message += f"♾️ *کل مصرف:* {total_used_str} (بدون محدودیت)\n"
        
        message += f"⬆️ *آپلود:* {upload_str} ({upload_percentage}%)\n"
        message += f"⬇️ *دانلود:* {download_str} ({download_percentage}%)\n"
        
        # Server info
        message += f"\n🌐 *اطلاعات سرور:*\n"
        message += f"🏁 *لوکیشن:* {subscription.server.location}\n"
        message += f"🔌 *پروتکل:* {subscription.get_protocol_display() if hasattr(subscription, 'get_protocol_display') else 'VMESS'}\n"
        
        # Usage tips
        message += f"\n💡 *نکات:*\n"
        
        if traffic_limit > 0 and usage_percentage > 80:
            message += "⚠️ مصرف ترافیک شما نزدیک به پایان است. در صورت نیاز، ترافیک اضافی خریداری کنید.\n"
        
        if subscription.end_date and (subscription.end_date - timezone.now()).days < 5:
            message += "⚠️ اشتراک شما به زودی منقضی می‌شود. برای جلوگیری از قطع سرویس، آن را تمدید کنید.\n"
        
        # Create keyboard
        keyboard = [
            [InlineKeyboardButton("🔄 ریست ترافیک", callback_data=TRAFFIC_RESET)],
            [InlineKeyboardButton("⏱ تمدید اشتراک", callback_data=TRAFFIC_EXTEND)],
            [InlineKeyboardButton("🔙 بازگشت", callback_data=TRAFFIC_MAIN)]
        ]
        
        await query.edit_message_text(
            text=message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
        
    except Exception as e:
        logger.error(f"Error in traffic_details: {e}")
        await query.edit_message_text(
            text=f"⚠️ خطا در دریافت جزئیات مصرف ترافیک: {str(e)}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت", callback_data=TRAFFIC_MAIN)]
            ])
        )
    
    return VIEWING_DETAILS

async def reset_traffic(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Reset user's traffic usage."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    # Confirmation buttons
    keyboard = [
        [InlineKeyboardButton("✅ بله، ریست کن", callback_data=f"{TRAFFIC_RESET}_confirm")],
        [InlineKeyboardButton("❌ خیر، انصراف", callback_data=TRAFFIC_MAIN)]
    ]
    
    # Check if it's a confirmation
    if query.data == f"{TRAFFIC_RESET}_confirm":
        try:
            # Get user's active subscription
            db_user = User.objects.get(telegram_id=user.id)
            subscription = Subscription.objects.filter(user=db_user, status='active').first()
            
            if not subscription:
                await query.edit_message_text(
                    text="⚠️ شما هیچ اشتراک فعالی ندارید.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 بازگشت", callback_data=TRAFFIC_MAIN)]
                    ])
                )
                return VIEWING_TRAFFIC
            
            # Check if subscription has required fields
            if not subscription.server or not subscription.inbound_id or not subscription.client_email:
                await query.edit_message_text(
                    text="⚠️ اطلاعات کافی برای ریست ترافیک موجود نیست. لطفاً با پشتیبانی تماس بگیرید.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("💬 تماس با پشتیبانی", callback_data="support")],
                        [InlineKeyboardButton("🔙 بازگشت", callback_data=TRAFFIC_MAIN)]
                    ])
                )
                return VIEWING_TRAFFIC
            
            # Update status message
            await query.edit_message_text(
                text="⏳ در حال ریست کردن ترافیک... لطفاً صبر کنید.",
                reply_markup=None
            )
            
            # Reset traffic
            client = ThreeXUIClient(subscription.server)
            result = client.reset_client_traffic(subscription.inbound_id, subscription.client_email)
            
            if result:
                # Update subscription data usage
                subscription.data_usage_gb = 0
                subscription.save()
                
                await query.edit_message_text(
                    text="✅ ترافیک مصرفی شما با موفقیت ریست شد.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("📊 مشاهده وضعیت", callback_data=TRAFFIC_MAIN)]
                    ])
                )
            else:
                await query.edit_message_text(
                    text="⚠️ ریست ترافیک با خطا مواجه شد. لطفاً با پشتیبانی تماس بگیرید.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("💬 تماس با پشتیبانی", callback_data="support")],
                        [InlineKeyboardButton("🔙 بازگشت", callback_data=TRAFFIC_MAIN)]
                    ])
                )
            
        except Exception as e:
            logger.error(f"Error in reset_traffic: {e}")
            await query.edit_message_text(
                text=f"⚠️ خطا در ریست ترافیک: {str(e)}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 بازگشت", callback_data=TRAFFIC_MAIN)]
                ])
            )
        
        return VIEWING_TRAFFIC
    
    # Show confirmation message
    message = "🔄 *ریست ترافیک*\n\n" \
              "آیا مطمئن هستید که می‌خواهید آمار مصرف ترافیک خود را ریست کنید؟\n\n" \
              "توجه: این عملیات آمار مصرف ترافیک را به صفر برمی‌گرداند، اما حجم کلی اشتراک شما تغییر نمی‌کند."
    
    await query.edit_message_text(
        text=message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )
    
    return VIEWING_TRAFFIC

async def extend_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Extend the user's subscription."""
    query = update.callback_query
    await query.answer()
    
    # Redirect to buy handler
    message = "⏱ *تمدید اشتراک*\n\n" \
              "برای تمدید اشتراک خود، لطفاً به بخش خرید اشتراک مراجعه کنید و گزینه تمدید را انتخاب نمایید."
    
    await query.edit_message_text(
        text=message,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🛒 خرید و تمدید اشتراک", callback_data="buy_subscription")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data=TRAFFIC_MAIN)]
        ]),
        parse_mode=ParseMode.MARKDOWN
    )
    
    return VIEWING_TRAFFIC

def get_traffic_handler() -> ConversationHandler:
    """Create and return the traffic monitoring conversation handler."""
    return ConversationHandler(
        entry_points=[
            CommandHandler("traffic", traffic_menu),
            CallbackQueryHandler(traffic_menu, pattern=f"^{TRAFFIC_CB}$"),
        ],
        states={
            VIEWING_TRAFFIC: [
                CallbackQueryHandler(traffic_menu, pattern=f"^{TRAFFIC_MAIN}$"),
                CallbackQueryHandler(traffic_details, pattern=f"^{TRAFFIC_DETAILS}$"),
                CallbackQueryHandler(reset_traffic, pattern=f"^{TRAFFIC_RESET}(_confirm)?$"),
                CallbackQueryHandler(extend_subscription, pattern=f"^{TRAFFIC_EXTEND}$"),
            ],
            VIEWING_DETAILS: [
                CallbackQueryHandler(traffic_menu, pattern=f"^{TRAFFIC_MAIN}$"),
                CallbackQueryHandler(reset_traffic, pattern=f"^{TRAFFIC_RESET}(_confirm)?$"),
                CallbackQueryHandler(extend_subscription, pattern=f"^{TRAFFIC_EXTEND}$"),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(traffic_menu, pattern=f"^{TRAFFIC_BACK}$"),
            CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern="^main_menu$"),
        ],
        name="vpn_traffic",
        persistent=False,
    ) 