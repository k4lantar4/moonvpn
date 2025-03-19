"""
VPN Packages management handler for the Telegram bot.

This module implements handlers for:
- Listing available VPN packages/plans
- Displaying package details
- Package purchase and subscription
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
from django.db import transaction

# Import models
try:
    from main.models import User, Server, Subscription, Package, Payment
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
    
    class Package:
        @staticmethod
        def get_available_packages():
            return [
                {"id": 1, "name": "Basic", "duration_days": 30, "data_limit_gb": 50, "price": 150000},
                {"id": 2, "name": "Standard", "duration_days": 30, "data_limit_gb": 100, "price": 250000},
                {"id": 3, "name": "Premium", "duration_days": 30, "data_limit_gb": 200, "price": 350000},
            ]
    
    class Payment:
        @staticmethod
        def create_payment(user_id, amount, package_id, payment_type):
            return {"id": 1, "status": "pending", "amount": amount}
    
    class Inbound:
        @staticmethod
        def get_by_id(inbound_id):
            return {"id": 1, "server_id": 1, "protocol": "vmess"}
    
    class Client:
        @staticmethod
        def get_by_email(email):
            return {"id": 1, "uuid": "test-uuid", "email": "test@example.com"}
    
    class ThreeXUIClient:
        def __init__(self, server):
            self.server = server
        
        def get_client_url(self, inbound_id, email):
            return {"vmess": "vmess://test-config", "vless": "vless://test-config"}
        
        def add_client(self, inbound_id, email, uuid=None, traffic_limit_gb=0, expiry_time=None):
            return True

# Setup logging
logger = logging.getLogger("telegram_bot")

# Conversation states
(
    VIEWING_PACKAGES,
    SELECTING_PACKAGE,
    SELECTING_SERVER,
    CONFIRMING_PURCHASE,
    PROCESSING_PAYMENT,
    PAYMENT_VERIFICATION,
) = range(6)

# Callback data patterns
PACKAGES_CB = "vpn_packages"
LIST_PACKAGES = f"{PACKAGES_CB}_list"
SELECT_PACKAGE = f"{PACKAGES_CB}_select"
PACKAGE_DETAILS = f"{PACKAGES_CB}_details"
SELECT_SERVER = f"{PACKAGES_CB}_server"
CONFIRM_PURCHASE = f"{PACKAGES_CB}_confirm"
CANCEL_PURCHASE = f"{PACKAGES_CB}_cancel"
PROCESS_PAYMENT = f"{PACKAGES_CB}_payment"
VERIFY_PAYMENT = f"{PACKAGES_CB}_verify"
PACKAGES_BACK = f"{PACKAGES_CB}_back"

# Helper functions
def format_price(price: int) -> str:
    """Format price with thousand separators."""
    return f"{price:,} تومان"

def format_duration(days: int) -> str:
    """Format duration in a human-readable format."""
    if days % 30 == 0:
        months = days // 30
        if months == 1:
            return "1 ماه"
        return f"{months} ماه"
    elif days % 7 == 0:
        weeks = days // 7
        if weeks == 1:
            return "1 هفته"
        return f"{weeks} هفته"
    else:
        if days == 1:
            return "1 روز"
        return f"{days} روز"

def get_package_icon(package_id: int) -> str:
    """Get appropriate icon for a package based on its tier."""
    package_icons = {
        1: "🥉",  # Bronze / Basic
        2: "🥈",  # Silver / Standard
        3: "🥇",  # Gold / Premium
        4: "💎",  # Diamond / Ultra
        5: "👑",  # Crown / Enterprise
    }
    return package_icons.get(package_id, "📦")
    
def format_data_limit(gb: int) -> str:
    """Format data limit in a human-readable format."""
    if gb == 0:
        return "بدون محدودیت"
    elif gb >= 1000:
        return f"{gb/1000:.1f} ترابایت"
    else:
        return f"{gb} گیگابایت"

def get_best_server_for_user() -> int:
    """Find the best server for new users based on current load."""
    try:
        servers = Server.objects.filter(is_active=True)
        
        if not servers.exists():
            return None
        
        best_server = None
        lowest_load = float('inf')
        
        for server in servers:
            # Calculate current load
            user_count = Subscription.objects.filter(server=server, status='active').count()
            load_percentage = user_count / max(1, server.max_users) * 100
            
            if load_percentage < lowest_load:
                lowest_load = load_percentage
                best_server = server
        
        return best_server.id if best_server else servers.first().id
        
    except Exception as e:
        logger.error(f"Error finding best server: {e}")
        return None

async def packages_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show the packages menu."""
    user = update.effective_user
    query = update.callback_query
    
    # Get user's language
    language = context.user_data.get("language", "en")
    
    # Check if user is registered
    try:
        db_user = User.objects.get(telegram_id=user.id)
    except User.DoesNotExist:
        # Create user if not exists
        db_user = User.objects.create(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            language_code=language
        )
    except Exception as e:
        logger.error(f"Error retrieving/creating user: {e}")
        message = "⚠️ خطایی در سیستم رخ داده است. لطفاً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید."
        
        if query:
            await query.answer()
            await query.edit_message_text(
                text=message,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")]])
            )
        else:
            await update.message.reply_text(
                text=message,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")]])
            )
        return ConversationHandler.END
    
    # Create keyboard with package options
    keyboard = [
        [InlineKeyboardButton("🛒 خرید پکیج جدید", callback_data=LIST_PACKAGES)],
        [InlineKeyboardButton("⏱ تمدید اشتراک", callback_data=f"{PACKAGES_CB}_extend")],
        [InlineKeyboardButton("⬆️ ارتقاء پکیج", callback_data=f"{PACKAGES_CB}_upgrade")],
        [InlineKeyboardButton("📋 وضعیت اشتراک", callback_data="vpn_traffic")],
        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")],
    ]
    
    message = "🛍 *پکیج‌های اشتراک VPN*\n\n" \
              "از این بخش می‌توانید پکیج‌های مختلف وی‌پی‌ان را مشاهده و خریداری کنید.\n" \
              "همچنین می‌توانید اشتراک خود را تمدید یا ارتقاء دهید.\n\n" \
              "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:"
    
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
    
    return VIEWING_PACKAGES

async def list_packages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show a list of available packages."""
    query = update.callback_query
    await query.answer()
    
    # Get available packages
    try:
        packages = Package.objects.filter(is_active=True).order_by('price')
        
        if not packages.exists():
            await query.edit_message_text(
                text="⚠️ در حال حاضر پکیجی برای فروش موجود نیست. لطفاً بعداً دوباره تلاش کنید.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 بازگشت", callback_data=PACKAGES_CB)]
                ])
            )
            return VIEWING_PACKAGES
        
        # Build message
        message = "🛒 *پکیج‌های موجود*\n\n"
        message += "لطفاً پکیج مورد نظر خود را انتخاب کنید:\n\n"
        
        # Create keyboard with package options
        keyboard = []
        
        for package in packages:
            icon = get_package_icon(package.id)
            duration = format_duration(package.duration_days)
            data_limit = format_data_limit(package.data_limit_gb)
            price = format_price(package.price)
            
            # Add package to keyboard
            keyboard.append([
                InlineKeyboardButton(
                    f"{icon} {package.name} - {duration} - {price}",
                    callback_data=f"package_{package.id}"
                )
            ])
        
        # Add back button
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data=PACKAGES_CB)])
        
        # Send message with package options
        await query.edit_message_text(
            text=message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
        
    except Exception as e:
        logger.error(f"Error listing packages: {e}")
        await query.edit_message_text(
            text="⚠️ خطایی در دریافت لیست پکیج‌ها رخ داد. لطفاً بعداً دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت", callback_data=PACKAGES_CB)]
            ])
        )
    
    return SELECTING_PACKAGE

async def show_package_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show details of a selected package."""
    query = update.callback_query
    await query.answer()
    
    # Get selected package ID from callback data
    callback_data = query.data
    if not callback_data.startswith("package_"):
        # Invalid callback data
        await query.edit_message_text(
            text="⚠️ خطایی رخ داد. لطفاً دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت", callback_data=PACKAGES_CB)]
            ])
        )
        return VIEWING_PACKAGES
    
    try:
        package_id = int(callback_data.split("_")[1])
        
        # Get package details
        package = Package.objects.get(id=package_id)
        
        # Store package ID in context
        context.user_data["selected_package_id"] = package_id
        
        # Format package details
        icon = get_package_icon(package.id)
        duration = format_duration(package.duration_days)
        data_limit = format_data_limit(package.data_limit_gb)
        price = format_price(package.price)
        
        # Build message with package details
        message = f"{icon} *پکیج {package.name}*\n\n"
        message += f"⏱ *مدت زمان:* {duration}\n"
        message += f"📊 *حجم ترافیک:* {data_limit}\n"
        message += f"💰 *قیمت:* {price}\n\n"
        
        # Add package description if available
        if package.description:
            message += f"📝 *توضیحات:*\n{package.description}\n\n"
        
        # Add package features if available
        if package.features:
            message += "✨ *ویژگی‌ها:*\n"
            features = package.features.split('\n')
            for feature in features:
                message += f"• {feature.strip()}\n"
            message += "\n"
        
        message += "برای خرید این پکیج، روی دکمه «خرید» کلیک کنید."
        
        # Create keyboard
        keyboard = [
            [InlineKeyboardButton("🛒 خرید", callback_data=f"{SELECT_SERVER}_{package_id}")],
            [InlineKeyboardButton("🔙 بازگشت به لیست پکیج‌ها", callback_data=LIST_PACKAGES)]
        ]
        
        await query.edit_message_text(
            text=message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
        
    except Exception as e:
        logger.error(f"Error showing package details: {e}")
        await query.edit_message_text(
            text="⚠️ خطایی در دریافت جزئیات پکیج رخ داد. لطفاً بعداً دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت", callback_data=LIST_PACKAGES)]
            ])
        )
    
    return SELECTING_PACKAGE

async def select_server(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Let user select a server location."""
    query = update.callback_query
    await query.answer()
    
    # Get package ID from callback data
    callback_data = query.data
    if not callback_data.startswith(f"{SELECT_SERVER}_"):
        # Invalid callback data
        await query.edit_message_text(
            text="⚠️ خطایی رخ داد. لطفاً دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت", callback_data=LIST_PACKAGES)]
            ])
        )
        return SELECTING_PACKAGE
    
    package_id = int(callback_data.split("_")[2])
    context.user_data["selected_package_id"] = package_id
    
    try:
        # Get package details
        package = Package.objects.get(id=package_id)
        
        # Get available servers
        servers = Server.objects.filter(is_active=True).order_by('location')
        
        if not servers.exists():
            await query.edit_message_text(
                text="⚠️ در حال حاضر هیچ سروری در دسترس نیست. لطفاً بعداً دوباره تلاش کنید.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 بازگشت", callback_data=f"package_{package_id}")]
                ])
            )
            return SELECTING_PACKAGE
            
        # Find the best server based on load
        best_server_id = get_best_server_for_user()
        if best_server_id:
            context.user_data["recommended_server_id"] = best_server_id
        
        # Build message
        message = f"🌐 *انتخاب سرور*\n\n"
        message += f"شما در حال خرید پکیج *{package.name}* هستید.\n"
        message += f"لطفاً لوکیشن مورد نظر خود را انتخاب کنید:\n\n"
        
        # Create keyboard with server options
        keyboard = []
        
        # Add recommended server if available
        if best_server_id:
            try:
                best_server = Server.objects.get(id=best_server_id)
                keyboard.append([
                    InlineKeyboardButton(
                        f"✅ پیشنهادی: {best_server.location} (بهترین کیفیت)",
                        callback_data=f"server_{best_server_id}"
                    )
                ])
            except Exception as e:
                logger.error(f"Error getting recommended server: {e}")
        
        # Add other servers
        for server in servers:
            # Skip if it's the recommended server (already added)
            if best_server_id and server.id == best_server_id:
                continue
                
            # Get server emoji based on location
            from handlers.vpn_location import get_server_emoji
            location_emoji = get_server_emoji(server.location)
            
            # Calculate server load
            user_count = Subscription.objects.filter(server=server, status='active').count()
            load_percentage = min(100, int((user_count / max(1, server.max_users)) * 100))
            
            # Determine load status
            if load_percentage < 50:
                load_status = "🟢"  # Low load
            elif load_percentage < 80:
                load_status = "🟡"  # Medium load
            else:
                load_status = "🔴"  # High load
            
            keyboard.append([
                InlineKeyboardButton(
                    f"{location_emoji} {server.location} {load_status}",
                    callback_data=f"server_{server.id}"
                )
            ])
        
        # Add option to let system choose best server
        keyboard.append([
            InlineKeyboardButton(
                "🔄 انتخاب خودکار بهترین سرور",
                callback_data="server_auto"
            )
        ])
        
        # Add back button
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data=f"package_{package_id}")])
        
        await query.edit_message_text(
            text=message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
        
    except Exception as e:
        logger.error(f"Error in select_server: {e}")
        await query.edit_message_text(
            text="⚠️ خطایی در دریافت لیست سرورها رخ داد. لطفاً بعداً دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت", callback_data=f"package_{package_id}")]
            ])
        )
    
    return SELECTING_SERVER

async def confirm_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Confirm purchase details."""
    query = update.callback_query
    await query.answer()
    
    # Get selected server ID from callback data
    callback_data = query.data
    if not callback_data.startswith("server_"):
        # Invalid callback data
        await query.edit_message_text(
            text="⚠️ خطایی رخ داد. لطفاً دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت", callback_data=PACKAGES_CB)]
            ])
        )
        return VIEWING_PACKAGES
    
    # Get package ID from context
    package_id = context.user_data.get("selected_package_id")
    if not package_id:
        await query.edit_message_text(
            text="⚠️ اطلاعات پکیج یافت نشد. لطفاً دوباره از منوی اصلی شروع کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به منوی پکیج‌ها", callback_data=PACKAGES_CB)]
            ])
        )
        return VIEWING_PACKAGES
    
    try:
        # Get server ID
        if callback_data == "server_auto":
            server_id = context.user_data.get("recommended_server_id") or get_best_server_for_user()
            if not server_id:
                await query.edit_message_text(
                    text="⚠️ انتخاب خودکار سرور با خطا مواجه شد. لطفاً یک سرور را به صورت دستی انتخاب کنید.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 بازگشت به انتخاب سرور", callback_data=f"{SELECT_SERVER}_{package_id}")]
                    ])
                )
                return SELECTING_SERVER
        else:
            server_id = int(callback_data.split("_")[1])
        
        # Store server ID in context
        context.user_data["selected_server_id"] = server_id
        
        # Get package and server details
        package = Package.objects.get(id=package_id)
        server = Server.objects.get(id=server_id)
        
        # Format package and server details
        package_icon = get_package_icon(package.id)
        duration = format_duration(package.duration_days)
        data_limit = format_data_limit(package.data_limit_gb)
        price = format_price(package.price)
        
        # Get server emoji
        from handlers.vpn_location import get_server_emoji
        server_emoji = get_server_emoji(server.location)
        
        # Build message with purchase details
        message = "🧾 *تأیید خرید*\n\n"
        message += f"*پکیج انتخابی:* {package_icon} {package.name}\n"
        message += f"*سرور:* {server_emoji} {server.location}\n"
        message += f"*مدت زمان:* {duration}\n"
        message += f"*حجم ترافیک:* {data_limit}\n"
        message += f"*مبلغ قابل پرداخت:* {price}\n\n"
        message += "لطفاً در صورت تأیید، روی دکمه «تأیید و پرداخت» کلیک کنید."
        
        # Create keyboard
        keyboard = [
            [InlineKeyboardButton("✅ تأیید و پرداخت", callback_data=CONFIRM_PURCHASE)],
            [InlineKeyboardButton("🔙 بازگشت به انتخاب سرور", callback_data=f"{SELECT_SERVER}_{package_id}")],
            [InlineKeyboardButton("❌ انصراف", callback_data=CANCEL_PURCHASE)]
        ]
        
        await query.edit_message_text(
            text=message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
        
    except Exception as e:
        logger.error(f"Error in confirm_purchase: {e}")
        await query.edit_message_text(
            text=f"⚠️ خطا در تأیید خرید: {str(e)}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت", callback_data=f"{SELECT_SERVER}_{package_id}")]
            ])
        )
    
    return CONFIRMING_PURCHASE

async def process_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process payment request."""
    query = update.callback_query
    
    # Validate callback data
    if query.data != CONFIRM_PURCHASE:
        await query.answer("⚠️ داده نامعتبر.", show_alert=True)
        return CONFIRMING_PURCHASE
    
    await query.answer()
    
    # Get user information
    user = update.effective_user
    
    # Get package and server IDs from context
    package_id = context.user_data.get("selected_package_id")
    server_id = context.user_data.get("selected_server_id")
    
    if not package_id or not server_id:
        await query.edit_message_text(
            text="⚠️ اطلاعات خرید ناقص است. لطفاً دوباره از منوی پکیج‌ها شروع کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به منوی پکیج‌ها", callback_data=PACKAGES_CB)]
            ])
        )
        return VIEWING_PACKAGES
    
    try:
        # Get package, server, and user details
        package = Package.objects.get(id=package_id)
        server = Server.objects.get(id=server_id)
        db_user = User.objects.get(telegram_id=user.id)
        
        # Create a payment record
        payment = Payment.objects.create(
            user=db_user,
            amount=package.price,
            package_id=package_id,
            server_id=server_id,
            payment_type="card",
            status="pending"
        )
        
        # Store payment ID in context
        context.user_data["payment_id"] = payment.id
        
        # Get admin bank details (should be configured in settings)
        try:
            from django.conf import settings
            admin_card = settings.PAYMENT_CARD
            admin_name = settings.PAYMENT_NAME
            admin_bank = settings.PAYMENT_BANK
        except:
            # Fallback defaults (should be overridden in settings)
            admin_card = "6037-9970-1234-5678"
            admin_name = "حمید رضایی"
            admin_bank = "ملی"
        
        # Format price
        price = format_price(package.price)
        
        # Build payment instructions message
        message = "💳 *پرداخت کارت به کارت*\n\n"
        message += f"لطفاً مبلغ *{price}* را به شماره کارت زیر واریز کنید:\n\n"
        message += f"```\n{admin_card}\n```\n"
        message += f"*به نام:* {admin_name}\n"
        message += f"*بانک:* {admin_bank}\n\n"
        
        message += "⚠️ *نکات مهم:*\n"
        message += "• پس از واریز، شماره پیگیری یا تصویر رسید را ارسال کنید.\n"
        message += "• اشتراک شما به محض تأیید پرداخت فعال می‌شود.\n"
        message += "• شماره کارت را کپی کنید و از صحت آن اطمینان حاصل کنید.\n\n"
        
        message += "🔢 *کد پیگیری خرید:* `" + str(payment.id) + "`\n\n"
        message += "پس از واریز، شماره پیگیری یا تصویر رسید بانکی را ارسال کنید."
        
        # Create keyboard
        keyboard = [
            [InlineKeyboardButton("❌ انصراف از خرید", callback_data=CANCEL_PURCHASE)]
        ]
        
        await query.edit_message_text(
            text=message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Send a message to admins about new payment
        try:
            admin_ids = getattr(settings, "ADMIN_IDS", [])
            for admin_id in admin_ids:
                admin_message = f"🔔 *درخواست خرید جدید*\n\n"
                admin_message += f"*کاربر:* {user.first_name} ({user.id})\n"
                admin_message += f"*پکیج:* {package.name}\n"
                admin_message += f"*سرور:* {server.location}\n"
                admin_message += f"*مبلغ:* {price}\n"
                admin_message += f"*کد پیگیری:* `{payment.id}`\n\n"
                admin_message += "منتظر تأیید پرداخت..."
                
                try:
                    await context.bot.send_message(
                        chat_id=admin_id,
                        text=admin_message,
                        parse_mode=ParseMode.MARKDOWN
                    )
                except Exception as e:
                    logger.error(f"Failed to send admin notification to {admin_id}: {e}")
        except Exception as e:
            logger.error(f"Failed to send admin notifications: {e}")
        
    except Exception as e:
        logger.error(f"Error processing payment: {e}")
        await query.edit_message_text(
            text=f"⚠️ خطا در پردازش پرداخت: {str(e)}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت", callback_data=PACKAGES_CB)]
            ])
        )
        return VIEWING_PACKAGES
    
    return PAYMENT_VERIFICATION

async def cancel_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the purchase process."""
    query = update.callback_query
    await query.answer()
    
    if query.data != CANCEL_PURCHASE:
        return CONFIRMING_PURCHASE
    
    # Get payment ID from context
    payment_id = context.user_data.get("payment_id")
    
    # Update payment status if it exists
    if payment_id:
        try:
            payment = Payment.objects.get(id=payment_id)
            payment.status = "cancelled"
            payment.save()
        except Exception as e:
            logger.error(f"Error cancelling payment: {e}")
    
    # Clear user data
    context.user_data.pop("selected_package_id", None)
    context.user_data.pop("selected_server_id", None)
    context.user_data.pop("payment_id", None)
    context.user_data.pop("recommended_server_id", None)
    
    await query.edit_message_text(
        text="❌ خرید لغو شد. می‌توانید هر زمان که خواستید دوباره خرید کنید.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 بازگشت به منوی پکیج‌ها", callback_data=PACKAGES_CB)]
        ])
    )
    
    return VIEWING_PACKAGES

async def verify_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Verify payment receipt sent by user."""
    user = update.effective_user
    payment_id = context.user_data.get("payment_id")
    
    if not payment_id:
        await update.message.reply_text(
            text="⚠️ اطلاعات پرداخت یافت نشد. لطفاً دوباره از منوی پکیج‌ها شروع کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به منوی پکیج‌ها", callback_data=PACKAGES_CB)]
            ])
        )
        return VIEWING_PACKAGES
    
    try:
        # Get payment details
        payment = Payment.objects.get(id=payment_id)
        
        if payment.status != "pending":
            await update.message.reply_text(
                text=f"⚠️ وضعیت پرداخت شما '{payment.status}' است و قابل تأیید نیست.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 بازگشت به منوی پکیج‌ها", callback_data=PACKAGES_CB)]
                ])
            )
            return VIEWING_PACKAGES
        
        # Check if the message is text or photo
        reference_code = None
        photo_file_id = None
        
        if update.message.text:
            reference_code = update.message.text
            payment.reference_code = reference_code
        elif update.message.photo:
            photo_file_id = update.message.photo[-1].file_id
            payment.receipt_photo = photo_file_id
            
            # Add caption as reference code if available
            if update.message.caption:
                payment.reference_code = update.message.caption
        else:
            await update.message.reply_text(
                text="⚠️ لطفاً رسید پرداخت را به صورت عکس یا شماره پیگیری ارسال کنید.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("❌ انصراف از خرید", callback_data=CANCEL_PURCHASE)]
                ])
            )
            return PAYMENT_VERIFICATION
        
        # Save payment record status
        payment.status = "verifying"
        payment.save()
        
        # Send confirmation to user
        await update.message.reply_text(
            text="✅ اطلاعات پرداخت شما دریافت شد و در حال بررسی است.\n\n"
                 "پس از تأیید پرداخت، اشتراک شما فعال خواهد شد و اطلاعات اتصال برای شما ارسال می‌شود.\n\n"
                 "با تشکر از صبر و شکیبایی شما.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")]
            ])
        )
        
        # Send notification to admins
        try:
            from django.conf import settings
            admin_ids = getattr(settings, "ADMIN_IDS", [])
            
            for admin_id in admin_ids:
                admin_message = f"🔔 *اطلاعات پرداخت دریافت شد*\n\n"
                admin_message += f"*کاربر:* {user.first_name} ({user.id})\n"
                admin_message += f"*کد پیگیری خرید:* `{payment.id}`\n"
                
                if reference_code:
                    admin_message += f"*شماره پیگیری بانکی:* `{reference_code}`\n"
                
                admin_message += "\nلطفاً پرداخت را بررسی و تأیید کنید."
                
                # Send message to admin
                sent_message = await context.bot.send_message(
                    chat_id=admin_id,
                    text=admin_message,
                    parse_mode=ParseMode.MARKDOWN
                )
                
                # If photo was sent, forward it to admin
                if photo_file_id:
                    await context.bot.send_photo(
                        chat_id=admin_id,
                        photo=photo_file_id,
                        caption=f"رسید پرداخت برای کد پیگیری: {payment.id}"
                    )
                
                # Add admin verification buttons
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=f"آیا پرداخت با کد پیگیری {payment.id} را تأیید می‌کنید؟",
                    reply_markup=InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton("✅ تأیید", callback_data=f"admin_verify_{payment.id}"),
                            InlineKeyboardButton("❌ رد", callback_data=f"admin_reject_{payment.id}")
                        ]
                    ])
                )
                
        except Exception as e:
            logger.error(f"Error sending admin notification: {e}")
        
    except Exception as e:
        logger.error(f"Error verifying payment: {e}")
        await update.message.reply_text(
            text=f"⚠️ خطا در پردازش اطلاعات پرداخت: {str(e)}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به منوی پکیج‌ها", callback_data=PACKAGES_CB)]
            ])
        )
    
    # Clear user context
    context.user_data.pop("payment_id", None)
    context.user_data.pop("selected_package_id", None)
    context.user_data.pop("selected_server_id", None)
    
    return ConversationHandler.END

# Admin handlers for payment verification
async def admin_verify_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin callback to verify payment."""
    query = update.callback_query
    await query.answer()
    
    if not query.data.startswith("admin_verify_"):
        return
    
    try:
        # Get payment ID from callback data
        payment_id = int(query.data.split("_")[2])
        
        # Get payment from database
        payment = Payment.objects.get(id=payment_id)
        
        if payment.status not in ["pending", "verifying"]:
            await query.edit_message_text(
                text=f"⚠️ وضعیت پرداخت '{payment.status}' است و قابل تأیید نیست."
            )
            return
        
        # Get payment details
        user = payment.user
        
        # Update payment status
        payment.status = "approved"
        payment.verified_by = update.effective_user.id
        payment.verified_at = timezone.now()
        payment.save()
        
        # Handle different payment types
        if payment.payment_type == "extension" and payment.subscription_id:
            # Handle subscription extension
            await handle_subscription_extension(payment, context, query)
        elif payment.payment_type == "upgrade" and payment.subscription_id:
            # Handle subscription upgrade
            await handle_subscription_upgrade(payment, context, query)
        else:
            # Handle new subscription (default)
            await handle_new_subscription(payment, context, query)
                
    except Exception as e:
        logger.error(f"Error in admin_verify_payment: {e}")
        await query.edit_message_text(
            text=f"⚠️ خطا در تأیید پرداخت: {str(e)}"
        )

async def handle_new_subscription(payment, context, query):
    """Handle new subscription creation after payment verification."""
    try:
        # Get package and server details
        package = Package.objects.get(id=payment.package_id)
        server = Server.objects.get(id=payment.server_id)
        user = payment.user
        
        # Calculate expiry date
        expiry_date = timezone.now() + timedelta(days=package.duration_days)
        
        # Get best inbound for the server
        inbound = None
        # Try to get an inbound with the same protocol as user's previous subscription
        existing_sub = Subscription.objects.filter(user=user, status='active').first()
        
        if existing_sub and existing_sub.inbound:
            protocol = existing_sub.inbound.protocol
            inbound = Inbound.objects.filter(server=server, protocol=protocol, is_active=True).first()
        
        # If no matching inbound, get any active inbound
        if not inbound:
            inbound = Inbound.objects.filter(server=server, is_active=True).first()
        
        if not inbound:
            raise ValueError("No active inbound found for server")
        
        # Create client email
        email = f"{user.username or f'user{user.id}'}_{server.name}_{timezone.now().strftime('%Y%m%d%H%M%S')}"
        
        # Create subscription
        subscription = Subscription.objects.create(
            user=user,
            server=server,
            inbound=inbound,
            package=package,
            client_email=email,
            data_limit_gb=package.data_limit_gb,
            data_used_gb=0,
            expiry_date=expiry_date,
            status='active',
            payment=payment
        )
        
        # Connect to 3x-UI panel and create client
        client_api = ThreeXUIClient(server)
        
        # Add client to 3x-UI panel
        success = client_api.add_client(
            inbound_id=inbound.panel_id,
            email=email,
            traffic_limit_gb=package.data_limit_gb,
            expiry_time=int(expiry_date.timestamp()) if package.duration_days > 0 else 0
        )
        
        if not success:
            raise ValueError("Failed to create client on the VPN panel")
        
        # Get client URL
        client_url = client_api.get_client_url(
            inbound_id=inbound.panel_id,
            email=email
        )
        
        if not client_url:
            client_url = {"vmess": "Error generating URL", "vless": "Error generating URL"}
        
        # Store client URL
        subscription.connection_data = client_url
        subscription.save()
        
        # Send notification to user
        user_message = f"✅ *پرداخت شما تأیید شد*\n\n"
        user_message += f"*نام پکیج:* {package.name}\n"
        user_message += f"*سرور:* {server.location}\n"
        user_message += f"*مدت زمان:* {format_duration(package.duration_days)}\n"
        user_message += f"*حجم ترافیک:* {format_data_limit(package.data_limit_gb)}\n\n"
        
        user_message += "🔐 *اطلاعات اتصال*\n\n"
        
        # Add connection URLs based on protocol
        if inbound.protocol == "vmess" and client_url.get("vmess"):
            user_message += f"*لینک اتصال VMess:*\n`{client_url.get('vmess')}`\n\n"
        
        if inbound.protocol == "vless" and client_url.get("vless"):
            user_message += f"*لینک اتصال VLess:*\n`{client_url.get('vless')}`\n\n"
        
        user_message += "برای مشاهده آموزش اتصال، دستور /help را ارسال کنید."
        
        # Send message to user
        try:
            await context.bot.send_message(
                chat_id=user.telegram_id,
                text=user_message,
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception as e:
            logger.error(f"Failed to send notification to user: {e}")
        
        # Notify admin of success
        await query.edit_message_text(
            text=f"✅ پرداخت با کد پیگیری {payment.id} تأیید شد و اشتراک جدید کاربر فعال گردید."
        )
    
    except Exception as e:
        logger.error(f"Error in handle_new_subscription: {e}")
        raise

async def handle_subscription_extension(payment, context, query):
    """Handle subscription extension after payment verification."""
    try:
        # Get subscription details
        subscription_id = payment.subscription_id
        subscription = Subscription.objects.get(id=subscription_id)
        
        # Get extension months
        extension_months = payment.extension_months or 1
        extension_days = extension_months * 30
        
        # Calculate new expiry date
        current_expiry = subscription.expiry_date or timezone.now()
        new_expiry = current_expiry + timedelta(days=extension_days)
        
        # Update subscription
        old_expiry_str = subscription.expiry_date.strftime("%Y-%m-%d") if subscription.expiry_date else "نامشخص"
        new_expiry_str = new_expiry.strftime("%Y-%m-%d")
        
        subscription.expiry_date = new_expiry
        subscription.save()
        
        # Update client in 3x-UI panel
        client_api = ThreeXUIClient(subscription.server)
        
        # Update client expiry time
        success = client_api.update_client(
            inbound_id=subscription.inbound.panel_id,
            email=subscription.client_email,
            expiry_time=int(new_expiry.timestamp())
        )
        
        if not success:
            logger.warning(f"Failed to update client expiry in panel for subscription {subscription_id}")
        
        # Send notification to user
        user_message = f"✅ *تمدید اشتراک شما با موفقیت انجام شد*\n\n"
        user_message += f"*پکیج:* {subscription.package.name}\n"
        user_message += f"*سرور:* {subscription.server.location}\n"
        user_message += f"*تمدید:* {extension_months} ماه\n"
        user_message += f"*تاریخ انقضای قبلی:* {old_expiry_str}\n"
        user_message += f"*تاریخ انقضای جدید:* {new_expiry_str}\n\n"
        user_message += "از خرید شما متشکریم."
        
        # Send message to user
        try:
            await context.bot.send_message(
                chat_id=payment.user.telegram_id,
                text=user_message,
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception as e:
            logger.error(f"Failed to send extension notification to user: {e}")
        
        # Notify admin of success
        await query.edit_message_text(
            text=f"✅ پرداخت با کد پیگیری {payment.id} تأیید شد و اشتراک کاربر به مدت {extension_months} ماه تمدید گردید."
        )
    
    except Exception as e:
        logger.error(f"Error in handle_subscription_extension: {e}")
        raise

async def handle_subscription_upgrade(payment, context, query):
    """Handle subscription upgrade after payment verification."""
    try:
        # Get subscription and package details
        subscription_id = payment.subscription_id
        subscription = Subscription.objects.get(id=subscription_id)
        
        old_package = subscription.package
        new_package = Package.objects.get(id=payment.package_id)
        
        # Store old data for notification
        old_package_name = old_package.name
        old_data_limit = subscription.data_limit_gb
        
        # Update subscription with new package details
        subscription.package = new_package
        subscription.data_limit_gb = new_package.data_limit_gb
        
        # Calculate remaining data - keep the same percentage of data used
        if old_data_limit > 0:
            used_percentage = subscription.data_used_gb / old_data_limit
            subscription.data_used_gb = min(
                subscription.data_used_gb,  # Keep current usage if less than new limit
                new_package.data_limit_gb * used_percentage  # Maintain same usage percentage
            )
        
        subscription.save()
        
        # Update client in 3x-UI panel
        client_api = ThreeXUIClient(subscription.server)
        
        # Update client traffic limit
        success = client_api.update_client(
            inbound_id=subscription.inbound.panel_id,
            email=subscription.client_email,
            traffic_limit_gb=new_package.data_limit_gb
        )
        
        if not success:
            logger.warning(f"Failed to update client traffic limit in panel for subscription {subscription_id}")
        
        # Send notification to user
        user_message = f"✅ *ارتقاء اشتراک شما با موفقیت انجام شد*\n\n"
        user_message += f"*پکیج قبلی:* {old_package_name}\n"
        user_message += f"*پکیج جدید:* {new_package.name}\n"
        user_message += f"*سرور:* {subscription.server.location}\n"
        user_message += f"*حجم ترافیک قبلی:* {format_data_limit(old_data_limit)}\n"
        user_message += f"*حجم ترافیک جدید:* {format_data_limit(new_package.data_limit_gb)}\n\n"
        user_message += "از خرید شما متشکریم."
        
        # Send message to user
        try:
            await context.bot.send_message(
                chat_id=payment.user.telegram_id,
                text=user_message,
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception as e:
            logger.error(f"Failed to send upgrade notification to user: {e}")
        
        # Notify admin of success
        await query.edit_message_text(
            text=f"✅ پرداخت با کد پیگیری {payment.id} تأیید شد و اشتراک کاربر از {old_package_name} به {new_package.name} ارتقاء یافت."
        )
    
    except Exception as e:
        logger.error(f"Error in handle_subscription_upgrade: {e}")
        raise

async def admin_reject_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin callback to reject payment."""
    query = update.callback_query
    await query.answer()
    
    if not query.data.startswith("admin_reject_"):
        return
    
    try:
        # Get payment ID from callback data
        payment_id = int(query.data.split("_")[2])
        
        # Get payment from database
        payment = Payment.objects.get(id=payment_id)
        
        if payment.status not in ["pending", "verifying"]:
            await query.edit_message_text(
                text=f"⚠️ وضعیت پرداخت '{payment.status}' است و قابل رد کردن نیست."
            )
            return
        
        # Update payment status
        payment.status = "rejected"
        payment.verified_by = update.effective_user.id
        payment.verified_at = timezone.now()
        payment.save()
        
        # Notify user
        try:
            user = payment.user
            
            user_message = "❌ *پرداخت شما تأیید نشد*\n\n"
            user_message += "متأسفانه اطلاعات پرداخت شما مورد تأیید قرار نگرفت.\n"
            user_message += "دلایل احتمالی:\n"
            user_message += "• عدم مطابقت مبلغ واریزی\n"
            user_message += "• اشکال در رسید پرداخت\n"
            user_message += "• تأخیر در واریز وجه\n\n"
            user_message += "لطفاً با پشتیبانی تماس بگیرید یا مجدداً تلاش کنید."
            
            await context.bot.send_message(
                chat_id=user.telegram_id,
                text=user_message,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🛒 خرید مجدد", callback_data=PACKAGES_CB)],
                    [InlineKeyboardButton("👨‍💻 تماس با پشتیبانی", callback_data="support")]
                ])
            )
        
        except Exception as e:
            logger.error(f"Failed to send rejection notification to user: {e}")
        
        # Notify admin of rejection
        await query.edit_message_text(
            text=f"❌ پرداخت با کد پیگیری {payment_id} رد شد و به کاربر اطلاع‌رسانی گردید."
        )
        
    except Exception as e:
        logger.error(f"Error in admin_reject_payment: {e}")
        await query.edit_message_text(
            text=f"⚠️ خطا در رد پرداخت: {str(e)}"
        )

def register_handlers(application):
    """Register all package-related handlers."""
    
    # Register conversation handler for package purchase flow
    package_conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(packages_menu, pattern=f"^{PACKAGES_CB}$"),
            CommandHandler("packages", packages_menu),
            CommandHandler("buy", packages_menu),
        ],
        states={
            VIEWING_PACKAGES: [
                CallbackQueryHandler(list_packages, pattern=f"^{LIST_PACKAGES}$"),
                CallbackQueryHandler(extend_subscription, pattern=f"^{PACKAGES_CB}_extend$"),
                CallbackQueryHandler(upgrade_subscription, pattern=f"^{PACKAGES_CB}_upgrade$"),
                CallbackQueryHandler(packages_menu, pattern=f"^{PACKAGES_CB}$"),
            ],
            SELECTING_PACKAGE: [
                CallbackQueryHandler(show_package_details, pattern=r"^package_\d+$"),
                CallbackQueryHandler(select_server, pattern=f"^{SELECT_SERVER}_\\d+$"),
                CallbackQueryHandler(show_extension_options, pattern=r"^extend_\d+$"),
                CallbackQueryHandler(show_upgrade_options, pattern=r"^upgrade_\d+$"),
                CallbackQueryHandler(list_packages, pattern=f"^{LIST_PACKAGES}$"),
                CallbackQueryHandler(packages_menu, pattern=f"^{PACKAGES_CB}$"),
            ],
            SELECTING_SERVER: [
                CallbackQueryHandler(confirm_purchase, pattern=r"^server_\d+$"),
                CallbackQueryHandler(confirm_purchase, pattern=r"^server_auto$"),
                CallbackQueryHandler(show_package_details, pattern=r"^package_\d+$"),
                CallbackQueryHandler(packages_menu, pattern=f"^{PACKAGES_CB}$"),
            ],
            CONFIRMING_PURCHASE: [
                CallbackQueryHandler(process_payment, pattern=f"^{CONFIRM_PURCHASE}$"),
                CallbackQueryHandler(process_extension, pattern=r"^extend_confirm_\d+_\d+$"),
                CallbackQueryHandler(process_upgrade, pattern=r"^upgrade_confirm_\d+_\d+$"),
                CallbackQueryHandler(cancel_purchase, pattern=f"^{CANCEL_PURCHASE}$"),
                CallbackQueryHandler(select_server, pattern=f"^{SELECT_SERVER}_\\d+$"),
                CallbackQueryHandler(packages_menu, pattern=f"^{PACKAGES_CB}$"),
            ],
            PAYMENT_VERIFICATION: [
                CallbackQueryHandler(cancel_purchase, pattern=f"^{CANCEL_PURCHASE}$"),
                MessageHandler(filters.TEXT | filters.PHOTO, verify_payment),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(cancel_purchase, pattern=f"^{CANCEL_PURCHASE}$"),
            CommandHandler("cancel", cancel_purchase),
            CallbackQueryHandler(packages_menu, pattern="main_menu"),
        ],
        name="packages_conversation",
    )
    
    application.add_handler(package_conv_handler)
    
    # Register admin handlers for payment verification
    application.add_handler(CallbackQueryHandler(admin_verify_payment, pattern=r"^admin_verify_\d+$"))
    application.add_handler(CallbackQueryHandler(admin_reject_payment, pattern=r"^admin_reject_\d+$"))

async def extend_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show available subscriptions for extension."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    try:
        # Get user from database
        db_user = User.objects.get(telegram_id=user.id)
        
        # Get active subscriptions
        active_subs = Subscription.objects.filter(
            user=db_user,
            status='active'
        ).select_related('server', 'package', 'inbound')
        
        if not active_subs.exists():
            await query.edit_message_text(
                text="❌ شما در حال حاضر هیچ اشتراک فعالی ندارید. ابتدا یک اشتراک خریداری کنید.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🛒 خرید اشتراک", callback_data=LIST_PACKAGES)],
                    [InlineKeyboardButton("🔙 بازگشت", callback_data=PACKAGES_CB)]
                ])
            )
            return VIEWING_PACKAGES
        
        # Build message
        message = "⏱ *تمدید اشتراک*\n\n"
        message += "اشتراک‌های فعال شما که می‌توانید تمدید کنید:\n\n"
        
        # Create keyboard with subscription options
        keyboard = []
        
        for sub in active_subs:
            # Add server emoji
            from handlers.vpn_location import get_server_emoji
            server_emoji = get_server_emoji(sub.server.location)
            
            # Calculate days left
            days_left = (sub.expiry_date - timezone.now()).days if sub.expiry_date else 0
            
            # Format traffic info
            traffic_used = f"{sub.data_used_gb:.1f}" if sub.data_used_gb else "0"
            traffic_total = f"{sub.data_limit_gb}" if sub.data_limit_gb else "نامحدود"
            traffic_info = f"{traffic_used}/{traffic_total} GB"
            
            # Add subscription to keyboard
            keyboard.append([
                InlineKeyboardButton(
                    f"{server_emoji} {sub.server.location} - {traffic_info} - {days_left} روز",
                    callback_data=f"extend_{sub.id}"
                )
            ])
        
        # Add back button
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data=PACKAGES_CB)])
        
        # Send message with subscription options
        await query.edit_message_text(
            text=message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Set next state
        return SELECTING_PACKAGE
        
    except Exception as e:
        logger.error(f"Error in extend_subscription: {e}")
        await query.edit_message_text(
            text="⚠️ خطایی در دریافت اطلاعات اشتراک رخ داد. لطفاً بعداً دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت", callback_data=PACKAGES_CB)]
            ])
        )
        return VIEWING_PACKAGES

async def upgrade_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show available subscriptions for upgrade."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    try:
        # Get user from database
        db_user = User.objects.get(telegram_id=user.id)
        
        # Get active subscriptions
        active_subs = Subscription.objects.filter(
            user=db_user,
            status='active'
        ).select_related('server', 'package', 'inbound')
        
        if not active_subs.exists():
            await query.edit_message_text(
                text="❌ شما در حال حاضر هیچ اشتراک فعالی ندارید. ابتدا یک اشتراک خریداری کنید.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🛒 خرید اشتراک", callback_data=LIST_PACKAGES)],
                    [InlineKeyboardButton("🔙 بازگشت", callback_data=PACKAGES_CB)]
                ])
            )
            return VIEWING_PACKAGES
        
        # Build message
        message = "⬆️ *ارتقاء اشتراک*\n\n"
        message += "اشتراک‌های فعال شما که می‌توانید ارتقاء دهید:\n\n"
        
        # Create keyboard with subscription options
        keyboard = []
        
        for sub in active_subs:
            # Add server emoji
            from handlers.vpn_location import get_server_emoji
            server_emoji = get_server_emoji(sub.server.location)
            
            # Get current package info
            package_name = sub.package.name if sub.package else "پکیج نامشخص"
            
            # Check if higher packages exist
            higher_packages_exist = Package.objects.filter(price__gt=sub.package.price, is_active=True).exists()
            if not higher_packages_exist:
                continue
            
            # Add subscription to keyboard
            keyboard.append([
                InlineKeyboardButton(
                    f"{server_emoji} {sub.server.location} - {package_name}",
                    callback_data=f"upgrade_{sub.id}"
                )
            ])
        
        if not keyboard:
            # No upgradeable subscriptions
            await query.edit_message_text(
                text="❌ هیچ اشتراک قابل ارتقاء یافت نشد.\n\nاشتراک‌های شما در بالاترین سطح قرار دارند یا امکان ارتقاء در حال حاضر فراهم نیست.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 بازگشت", callback_data=PACKAGES_CB)]
                ])
            )
            return VIEWING_PACKAGES
        
        # Add back button
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data=PACKAGES_CB)])
        
        # Send message with subscription options
        await query.edit_message_text(
            text=message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Set next state
        return SELECTING_PACKAGE
        
    except Exception as e:
        logger.error(f"Error in upgrade_subscription: {e}")
        await query.edit_message_text(
            text="⚠️ خطایی در دریافت اطلاعات اشتراک رخ داد. لطفاً بعداً دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت", callback_data=PACKAGES_CB)]
            ])
        )
        return VIEWING_PACKAGES

async def show_extension_options(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show options for extending a subscription."""
    query = update.callback_query
    await query.answer()
    
    # Get subscription ID from callback data
    callback_data = query.data
    if not callback_data.startswith("extend_"):
        return VIEWING_PACKAGES
    
    subscription_id = int(callback_data.split("_")[1])
    context.user_data["extend_subscription_id"] = subscription_id
    
    try:
        # Get subscription details
        subscription = Subscription.objects.get(id=subscription_id)
        
        # Get extension options from the same package
        package = subscription.package
        
        # Store current subscription and package info in context
        context.user_data["current_package_id"] = package.id
        context.user_data["current_server_id"] = subscription.server.id
        
        # Format package details
        icon = get_package_icon(package.id)
        duration = format_duration(package.duration_days)
        data_limit = format_data_limit(package.data_limit_gb)
        price = format_price(package.price)
        
        # Calculate days left in current subscription
        days_left = (subscription.expiry_date - timezone.now()).days if subscription.expiry_date else 0
        
        # Build message
        message = f"⏱ *تمدید اشتراک*\n\n"
        message += f"*اشتراک فعلی:* {icon} {package.name}\n"
        message += f"*سرور:* {get_server_emoji(subscription.server.location)} {subscription.server.location}\n"
        message += f"*روزهای باقی‌مانده:* {days_left} روز\n"
        message += f"*وضعیت ترافیک:* {subscription.data_used_gb:.1f}/{subscription.data_limit_gb} GB\n\n"
        
        message += "لطفاً مدت زمان تمدید را انتخاب کنید:\n"
        
        # Create keyboard with extension options
        keyboard = []
        
        # Add common extension durations
        extension_options = [
            {"months": 1, "label": "۱ ماه", "callback": f"extend_confirm_{subscription_id}_1"},
            {"months": 3, "label": "۳ ماه (۵٪ تخفیف)", "callback": f"extend_confirm_{subscription_id}_3"},
            {"months": 6, "label": "۶ ماه (۱۰٪ تخفیف)", "callback": f"extend_confirm_{subscription_id}_6"},
            {"months": 12, "label": "۱۲ ماه (۱۵٪ تخفیف)", "callback": f"extend_confirm_{subscription_id}_12"},
        ]
        
        for option in extension_options:
            months = option["months"]
            days = months * 30
            
            # Calculate price with discount
            base_price = package.price * months
            discount = 0
            if months == 3:
                discount = 0.05
            elif months == 6:
                discount = 0.10
            elif months == 12:
                discount = 0.15
            
            final_price = int(base_price * (1 - discount))
            
            keyboard.append([
                InlineKeyboardButton(
                    f"{option['label']} - {format_price(final_price)}",
                    callback_data=option["callback"]
                )
            ])
        
        # Add back button
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data=f"{PACKAGES_CB}_extend")])
        
        await query.edit_message_text(
            text=message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
        
    except Exception as e:
        logger.error(f"Error in show_extension_options: {e}")
        await query.edit_message_text(
            text=f"⚠️ خطا در دریافت اطلاعات تمدید: {str(e)}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت", callback_data=f"{PACKAGES_CB}_extend")]
            ])
        )
    
    return CONFIRMING_PURCHASE

async def show_upgrade_options(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show options for upgrading a subscription."""
    query = update.callback_query
    await query.answer()
    
    # Get subscription ID from callback data
    callback_data = query.data
    if not callback_data.startswith("upgrade_"):
        return VIEWING_PACKAGES
    
    subscription_id = int(callback_data.split("_")[1])
    context.user_data["upgrade_subscription_id"] = subscription_id
    
    try:
        # Get subscription details
        subscription = Subscription.objects.get(id=subscription_id)
        
        # Get upgrade options
        current_package = subscription.package
        
        # Get higher tier packages
        better_packages = Package.objects.filter(
            price__gt=current_package.price,
            is_active=True
        ).order_by('price')
        
        if not better_packages.exists():
            await query.edit_message_text(
                text="❌ در حال حاضر پکیج بالاتری برای ارتقاء وجود ندارد.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 بازگشت", callback_data=f"{PACKAGES_CB}_upgrade")]
                ])
            )
            return VIEWING_PACKAGES
        
        # Store current subscription info in context
        context.user_data["current_package_id"] = current_package.id
        context.user_data["current_server_id"] = subscription.server.id
        
        # Calculate days left in current subscription
        days_left = (subscription.expiry_date - timezone.now()).days if subscription.expiry_date else 0
        
        # Build message
        message = f"⬆️ *ارتقاء اشتراک*\n\n"
        message += f"*اشتراک فعلی:* {get_package_icon(current_package.id)} {current_package.name}\n"
        message += f"*سرور:* {get_server_emoji(subscription.server.location)} {subscription.server.location}\n"
        message += f"*روزهای باقی‌مانده:* {days_left} روز\n"
        message += f"*وضعیت ترافیک:* {subscription.data_used_gb:.1f}/{subscription.data_limit_gb} GB\n\n"
        
        message += "پکیج‌های قابل ارتقاء:\n"
        
        # Create keyboard with upgrade options
        keyboard = []
        
        for package in better_packages:
            # Calculate price difference considering days left in current subscription
            days_total = current_package.duration_days
            price_per_day = current_package.price / max(1, days_total)
            remaining_value = price_per_day * days_left
            
            # Calculate upgrade price (new package price minus remaining value of current package)
            upgrade_price = max(0, package.price - remaining_value)
            upgrade_price = int(upgrade_price)  # Round to integer
            
            # Format package details
            icon = get_package_icon(package.id)
            data_limit = format_data_limit(package.data_limit_gb)
            
            keyboard.append([
                InlineKeyboardButton(
                    f"{icon} {package.name} - {data_limit} - {format_price(upgrade_price)}",
                    callback_data=f"upgrade_confirm_{subscription_id}_{package.id}"
                )
            ])
        
        # Add back button
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data=f"{PACKAGES_CB}_upgrade")])
        
        await query.edit_message_text(
            text=message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
        
    except Exception as e:
        logger.error(f"Error in show_upgrade_options: {e}")
        await query.edit_message_text(
            text=f"⚠️ خطا در دریافت اطلاعات ارتقاء: {str(e)}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت", callback_data=f"{PACKAGES_CB}_upgrade")]
            ])
        )
    
    return CONFIRMING_PURCHASE

async def process_extension(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process subscription extension."""
    query = update.callback_query
    await query.answer()
    
    # Get subscription ID and extension months from callback data
    callback_data = query.data
    if not callback_data.startswith("extend_confirm_"):
        return CONFIRMING_PURCHASE
    
    parts = callback_data.split("_")
    subscription_id = int(parts[2])
    months = int(parts[3])
    
    # Store extension details in context
    context.user_data["extend_subscription_id"] = subscription_id
    context.user_data["extend_months"] = months
    
    try:
        # Get subscription details
        subscription = Subscription.objects.get(id=subscription_id)
        package = subscription.package
        
        # Calculate extension price with discount
        base_price = package.price * months
        discount = 0
        if months == 3:
            discount = 0.05
        elif months == 6:
            discount = 0.10
        elif months == 12:
            discount = 0.15
        
        final_price = int(base_price * (1 - discount))
        
        # Store price in context
        context.user_data["payment_amount"] = final_price
        context.user_data["payment_type"] = "extension"
        
        # Create a payment record
        user = update.effective_user
        db_user = User.objects.get(telegram_id=user.id)
        
        payment = Payment.objects.create(
            user=db_user,
            amount=final_price,
            package_id=package.id,
            server_id=subscription.server.id,
            subscription_id=subscription_id,
            payment_type="extension",
            extension_months=months,
            status="pending"
        )
        
        # Store payment ID in context
        context.user_data["payment_id"] = payment.id
        
        # Get admin bank details
        try:
            from django.conf import settings
            admin_card = settings.PAYMENT_CARD
            admin_name = settings.PAYMENT_NAME
            admin_bank = settings.PAYMENT_BANK
        except:
            # Fallback defaults
            admin_card = "6037-9970-1234-5678"
            admin_name = "حمید رضایی"
            admin_bank = "ملی"
        
        # Format price
        price = format_price(final_price)
        
        # Build payment instructions message
        message = "💳 *پرداخت تمدید اشتراک*\n\n"
        message += f"*نوع عملیات:* تمدید اشتراک به مدت {months} ماه\n"
        message += f"*پکیج:* {package.name}\n"
        message += f"*سرور:* {subscription.server.location}\n"
        message += f"*مبلغ قابل پرداخت:* {price}\n\n"
        
        message += f"لطفاً مبلغ *{price}* را به شماره کارت زیر واریز کنید:\n\n"
        message += f"```\n{admin_card}\n```\n"
        message += f"*به نام:* {admin_name}\n"
        message += f"*بانک:* {admin_bank}\n\n"
        
        message += "⚠️ *نکات مهم:*\n"
        message += "• پس از واریز، شماره پیگیری یا تصویر رسید را ارسال کنید.\n"
        message += "• تمدید اشتراک شما به محض تأیید پرداخت انجام می‌شود.\n"
        message += "• شماره کارت را کپی کنید و از صحت آن اطمینان حاصل کنید.\n\n"
        
        message += "🔢 *کد پیگیری خرید:* `" + str(payment.id) + "`\n\n"
        message += "پس از واریز، شماره پیگیری یا تصویر رسید بانکی را ارسال کنید."
        
        # Create keyboard
        keyboard = [
            [InlineKeyboardButton("❌ انصراف از تمدید", callback_data=CANCEL_PURCHASE)]
        ]
        
        await query.edit_message_text(
            text=message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Send a message to admins about new extension payment
        try:
            from django.conf import settings
            admin_ids = getattr(settings, "ADMIN_IDS", [])
            for admin_id in admin_ids:
                admin_message = f"🔔 *درخواست تمدید اشتراک*\n\n"
                admin_message += f"*کاربر:* {user.first_name} ({user.id})\n"
                admin_message += f"*عملیات:* تمدید به مدت {months} ماه\n"
                admin_message += f"*پکیج:* {package.name}\n"
                admin_message += f"*سرور:* {subscription.server.location}\n"
                admin_message += f"*مبلغ:* {price}\n"
                admin_message += f"*کد پیگیری:* `{payment.id}`\n\n"
                admin_message += "منتظر تأیید پرداخت..."
                
                try:
                    await context.bot.send_message(
                        chat_id=admin_id,
                        text=admin_message,
                        parse_mode=ParseMode.MARKDOWN
                    )
                except Exception as e:
                    logger.error(f"Failed to send admin notification to {admin_id}: {e}")
        except Exception as e:
            logger.error(f"Failed to send admin notifications: {e}")
        
        return PAYMENT_VERIFICATION
        
    except Exception as e:
        logger.error(f"Error in process_extension: {e}")
        await query.edit_message_text(
            text=f"⚠️ خطا در پردازش تمدید: {str(e)}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت", callback_data=f"{PACKAGES_CB}_extend")]
            ])
        )
        return VIEWING_PACKAGES

async def process_upgrade(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process subscription upgrade."""
    query = update.callback_query
    await query.answer()
    
    # Get subscription ID and target package ID from callback data
    callback_data = query.data
    if not callback_data.startswith("upgrade_confirm_"):
        return CONFIRMING_PURCHASE
    
    parts = callback_data.split("_")
    subscription_id = int(parts[2])
    target_package_id = int(parts[3])
    
    # Store upgrade details in context
    context.user_data["upgrade_subscription_id"] = subscription_id
    context.user_data["upgrade_target_package_id"] = target_package_id
    
    try:
        # Get subscription and packages details
        subscription = Subscription.objects.get(id=subscription_id)
        current_package = subscription.package
        target_package = Package.objects.get(id=target_package_id)
        
        # Calculate days left in current subscription
        days_left = (subscription.expiry_date - timezone.now()).days if subscription.expiry_date else 0
        
        # Calculate upgrade price
        days_total = current_package.duration_days
        price_per_day = current_package.price / max(1, days_total)
        remaining_value = price_per_day * days_left
        
        # Calculate upgrade price (new package price minus remaining value of current package)
        upgrade_price = max(0, target_package.price - remaining_value)
        upgrade_price = int(upgrade_price)  # Round to integer
        
        # Store price in context
        context.user_data["payment_amount"] = upgrade_price
        context.user_data["payment_type"] = "upgrade"
        
        # Create a payment record
        user = update.effective_user
        db_user = User.objects.get(telegram_id=user.id)
        
        payment = Payment.objects.create(
            user=db_user,
            amount=upgrade_price,
            package_id=target_package_id,
            server_id=subscription.server.id,
            subscription_id=subscription_id,
            payment_type="upgrade",
            status="pending"
        )
        
        # Store payment ID in context
        context.user_data["payment_id"] = payment.id
        
        # Get admin bank details
        try:
            from django.conf import settings
            admin_card = settings.PAYMENT_CARD
            admin_name = settings.PAYMENT_NAME
            admin_bank = settings.PAYMENT_BANK
        except:
            # Fallback defaults
            admin_card = "6037-9970-1234-5678"
            admin_name = "حمید رضایی"
            admin_bank = "ملی"
        
        # Format price
        price = format_price(upgrade_price)
        
        # Build payment instructions message
        message = "💳 *پرداخت ارتقاء اشتراک*\n\n"
        message += f"*نوع عملیات:* ارتقاء از {current_package.name} به {target_package.name}\n"
        message += f"*سرور:* {subscription.server.location}\n"
        message += f"*حجم ترافیک فعلی:* {format_data_limit(current_package.data_limit_gb)}\n"
        message += f"*حجم ترافیک جدید:* {format_data_limit(target_package.data_limit_gb)}\n"
        message += f"*مبلغ قابل پرداخت:* {price}\n\n"
        
        message += f"لطفاً مبلغ *{price}* را به شماره کارت زیر واریز کنید:\n\n"
        message += f"```\n{admin_card}\n```\n"
        message += f"*به نام:* {admin_name}\n"
        message += f"*بانک:* {admin_bank}\n\n"
        
        message += "⚠️ *نکات مهم:*\n"
        message += "• پس از واریز، شماره پیگیری یا تصویر رسید را ارسال کنید.\n"
        message += "• ارتقاء اشتراک شما به محض تأیید پرداخت انجام می‌شود.\n"
        message += "• شماره کارت را کپی کنید و از صحت آن اطمینان حاصل کنید.\n\n"
        
        message += "🔢 *کد پیگیری خرید:* `" + str(payment.id) + "`\n\n"
        message += "پس از واریز، شماره پیگیری یا تصویر رسید بانکی را ارسال کنید."
        
        # Create keyboard
        keyboard = [
            [InlineKeyboardButton("❌ انصراف از ارتقاء", callback_data=CANCEL_PURCHASE)]
        ]
        
        await query.edit_message_text(
            text=message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Send a message to admins about new upgrade payment
        try:
            from django.conf import settings
            admin_ids = getattr(settings, "ADMIN_IDS", [])
            for admin_id in admin_ids:
                admin_message = f"🔔 *درخواست ارتقاء اشتراک*\n\n"
                admin_message += f"*کاربر:* {user.first_name} ({user.id})\n"
                admin_message += f"*عملیات:* ارتقاء از {current_package.name} به {target_package.name}\n"
                admin_message += f"*سرور:* {subscription.server.location}\n"
                admin_message += f"*مبلغ:* {price}\n"
                admin_message += f"*کد پیگیری:* `{payment.id}`\n\n"
                admin_message += "منتظر تأیید پرداخت..."
                
                try:
                    await context.bot.send_message(
                        chat_id=admin_id,
                        text=admin_message,
                        parse_mode=ParseMode.MARKDOWN
                    )
                except Exception as e:
                    logger.error(f"Failed to send admin notification to {admin_id}: {e}")
        except Exception as e:
            logger.error(f"Failed to send admin notifications: {e}")
        
        return PAYMENT_VERIFICATION
        
    except Exception as e:
        logger.error(f"Error in process_upgrade: {e}")
        await query.edit_message_text(
            text=f"⚠️ خطا در پردازش ارتقاء: {str(e)}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت", callback_data=f"{PACKAGES_CB}_upgrade")]
            ])
        )
        return VIEWING_PACKAGES 