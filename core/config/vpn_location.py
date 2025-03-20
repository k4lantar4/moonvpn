"""
VPN Location management handler for the Telegram bot.

This module implements handlers for:
- Listing available VPN server locations
- Changing user's active VPN location
- Getting connection details for each location
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from telegram.constants import ParseMode

from django.db import transaction
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
            return {"id": 1, "uuid": "test-uuid", "email": "test@example.com"}
    
    class ThreeXUIClient:
        def __init__(self, server):
            self.server = server
        
        def get_client_url(self, inbound_id, email):
            return {"vmess": "vmess://test-config", "vless": "vless://test-config"}
        
        def update_client(self, inbound_id, email, **kwargs):
            return True

# Setup logging
logger = logging.getLogger("telegram_bot")

# Conversation states
(
    SELECTING_LOCATION,
    CONFIRMING_CHANGE,
    SELECTING_PROTOCOL
) = range(3)

# Callback data patterns
LOCATION_CB = "vpn_location"
LIST_LOCATIONS = f"{LOCATION_CB}_list"
CHANGE_LOCATION = f"{LOCATION_CB}_change"
CONFIRM_LOCATION = f"{LOCATION_CB}_confirm"
CANCEL_CHANGE = f"{LOCATION_CB}_cancel"
GET_CONFIG = f"{LOCATION_CB}_config"
SELECT_PROTOCOL = f"{LOCATION_CB}_protocol"
BACK_TO_LOCATIONS = f"{LOCATION_CB}_back"

def get_server_emoji(location: str) -> str:
    """Get flag emoji for a server location."""
    location_emojis = {
        "netherlands": "🇳🇱",
        "germany": "🇩🇪",
        "france": "🇫🇷",
        "united states": "🇺🇸",
        "united kingdom": "🇬🇧",
        "canada": "🇨🇦",
        "japan": "🇯🇵",
        "singapore": "🇸🇬",
        "australia": "🇦🇺",
        "brazil": "🇧🇷",
        "india": "🇮🇳",
        "russia": "🇷🇺",
        "south africa": "🇿🇦",
        "iran": "🇮🇷",
        "turkey": "🇹🇷", 
    }
    
    # Default to a globe emoji if location not found
    lower_location = location.lower()
    
    for key, emoji in location_emojis.items():
        if key in lower_location:
            return emoji
    
    return "🌍"

async def location_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show the location management menu."""
    user = update.effective_user
    query = update.callback_query
    
    # Get user's language
    language = context.user_data.get("language", "en")
    
    # Create keyboard with location options
    keyboard = [
        [InlineKeyboardButton("📍 لیست لوکیشن‌ها", callback_data=LIST_LOCATIONS)],
        [InlineKeyboardButton("🔄 تغییر لوکیشن", callback_data=CHANGE_LOCATION)],
        [InlineKeyboardButton("📋 دریافت کانفیگ", callback_data=GET_CONFIG)],
        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = "🌐 *مدیریت لوکیشن سرویس شما*\n\n" \
              "از این بخش می‌توانید لوکیشن‌های موجود را مشاهده کنید، لوکیشن فعلی خود را تغییر دهید، " \
              "و کانفیگ مربوط به سرویس خود را دریافت کنید.\n\n" \
              "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:"
    
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
    
    return SELECTING_LOCATION

async def list_locations(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show a list of available server locations."""
    query = update.callback_query
    await query.answer()
    
    # Get active servers from database
    try:
        servers = Server.objects.filter(is_active=True).order_by('location')
        
        if not servers.exists():
            await query.edit_message_text(
                text="⚠️ در حال حاضر هیچ سروری در دسترس نیست. لطفاً بعداً دوباره تلاش کنید.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 بازگشت", callback_data=LOCATION_CB)]
                ])
            )
            return SELECTING_LOCATION
        
        # Count users on each server and calculate load
        server_info = []
        for server in servers:
            # Get server usage stats
            user_count = Subscription.objects.filter(server=server, status='active').count()
            load_percentage = min(100, int((user_count / max(1, server.max_users)) * 100))
            
            # Determine load status emoji
            if load_percentage < 50:
                load_status = "🟢"  # Low load
            elif load_percentage < 80:
                load_status = "🟡"  # Medium load
            else:
                load_status = "🔴"  # High load
            
            server_info.append({
                "id": server.id,
                "name": server.name,
                "location": server.location,
                "emoji": get_server_emoji(server.location),
                "load": load_percentage,
                "load_status": load_status
            })
        
        # Build message
        message = "📍 *لوکیشن‌های موجود*\n\n"
        
        for info in server_info:
            message += f"{info['load_status']} {info['emoji']} *{info['location']}*\n"
            message += f"    ├ نام: {info['name']}\n"
            message += f"    └ وضعیت بار: {info['load']}%\n\n"
        
        # Add a note about choosing location
        message += "_برای تغییر لوکیشن، به منوی اصلی بازگشته و گزینه «تغییر لوکیشن» را انتخاب کنید._"
        
        await query.edit_message_text(
            text=message,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت", callback_data=LOCATION_CB)]
            ]),
            parse_mode=ParseMode.MARKDOWN
        )
        
    except Exception as e:
        logger.error(f"Error retrieving locations: {e}")
        await query.edit_message_text(
            text="⚠️ خطایی در دریافت لیست لوکیشن‌ها رخ داد. لطفاً بعداً دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت", callback_data=LOCATION_CB)]
            ])
        )
    
    return SELECTING_LOCATION

async def change_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show available locations for changing."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    user_id = user.id
    
    try:
        # Get the user's database record
        db_user = User.objects.filter(telegram_id=user_id).first()
        
        if not db_user:
            await query.edit_message_text(
                text="⚠️ اطلاعات کاربری شما یافت نشد. لطفاً با پشتیبانی تماس بگیرید.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 بازگشت", callback_data=LOCATION_CB)]
                ])
            )
            return SELECTING_LOCATION
        
        # Check if user has active subscriptions
        active_subs = Subscription.objects.filter(user=db_user, status='active')
        
        if not active_subs.exists():
            await query.edit_message_text(
                text="⚠️ شما هیچ اشتراک فعالی ندارید. ابتدا باید یک اشتراک خریداری کنید.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🛒 خرید اشتراک", callback_data="buy_subscription")],
                    [InlineKeyboardButton("🔙 بازگشت", callback_data=LOCATION_CB)]
                ])
            )
            return SELECTING_LOCATION
        
        # Get current server and other available servers
        current_subscription = active_subs.first()
        current_server = current_subscription.server
        
        # Get all active servers
        available_servers = Server.objects.filter(is_active=True).exclude(id=current_server.id if current_server else None)
        
        if not available_servers.exists():
            await query.edit_message_text(
                text="⚠️ در حال حاضر سرور دیگری برای تغییر لوکیشن در دسترس نیست.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 بازگشت", callback_data=LOCATION_CB)]
                ])
            )
            return SELECTING_LOCATION
        
        # Build message and keyboard
        message = "🔄 *تغییر لوکیشن سرویس*\n\n"
        
        if current_server:
            message += f"لوکیشن فعلی: {get_server_emoji(current_server.location)} *{current_server.location}*\n\n"
        
        message += "لوکیشن جدید را انتخاب کنید:\n"
        
        # Create keyboard with server options
        keyboard = []
        for server in available_servers:
            emoji = get_server_emoji(server.location)
            keyboard.append([
                InlineKeyboardButton(
                    f"{emoji} {server.location}",
                    callback_data=f"server_{server.id}"
                )
            ])
        
        # Add back button
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data=LOCATION_CB)])
        
        await query.edit_message_text(
            text=message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
        
    except Exception as e:
        logger.error(f"Error in change_location: {e}")
        await query.edit_message_text(
            text="⚠️ خطایی در دریافت لیست لوکیشن‌ها رخ داد. لطفاً بعداً دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت", callback_data=LOCATION_CB)]
            ])
        )
    
    return CONFIRMING_CHANGE

async def confirm_location_change(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Confirm changing to the selected location."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    user_id = user.id
    
    # Get selected server ID from callback data
    callback_data = query.data
    if not callback_data.startswith("server_"):
        # Invalid callback data
        await query.edit_message_text(
            text="⚠️ خطایی رخ داد. لطفاً دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت", callback_data=LOCATION_CB)]
            ])
        )
        return SELECTING_LOCATION
    
    try:
        server_id = int(callback_data.split("_")[1])
        context.user_data["selected_server_id"] = server_id
        
        # Get server details
        server = Server.objects.get(id=server_id)
        
        # Get user's active subscription
        db_user = User.objects.get(telegram_id=user_id)
        subscription = Subscription.objects.filter(user=db_user, status='active').first()
        
        if not subscription:
            await query.edit_message_text(
                text="⚠️ اشتراک فعالی برای شما یافت نشد. لطفاً ابتدا یک اشتراک خریداری کنید.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🛒 خرید اشتراک", callback_data="buy_subscription")],
                    [InlineKeyboardButton("🔙 بازگشت", callback_data=LOCATION_CB)]
                ])
            )
            return SELECTING_LOCATION
        
        # Store current server and subscription info for the change
        context.user_data["current_server_id"] = subscription.server.id if subscription.server else None
        context.user_data["subscription_id"] = subscription.id
        
        # Build confirmation message
        message = "🔄 *تأیید تغییر لوکیشن*\n\n"
        message += f"آیا مطمئن هستید که می‌خواهید لوکیشن خود را به {get_server_emoji(server.location)} *{server.location}* تغییر دهید؟\n\n"
        message += "توجه: پس از تغییر لوکیشن، کانفیگ جدیدی دریافت خواهید کرد و کانفیگ قبلی غیرفعال خواهد شد."
        
        keyboard = [
            [InlineKeyboardButton("✅ بله، تغییر بده", callback_data=CONFIRM_LOCATION)],
            [InlineKeyboardButton("❌ خیر، انصراف", callback_data=CANCEL_CHANGE)]
        ]
        
        await query.edit_message_text(
            text=message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
        
    except Exception as e:
        logger.error(f"Error in confirm_location_change: {e}")
        await query.edit_message_text(
            text="⚠️ خطایی در پردازش درخواست رخ داد. لطفاً بعداً دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت", callback_data=LOCATION_CB)]
            ])
        )
    
    return CONFIRMING_CHANGE

async def process_location_change(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process the location change request."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    user_id = user.id
    
    # Check if user confirmed the change
    if query.data != CONFIRM_LOCATION:
        await query.edit_message_text(
            text="❌ تغییر لوکیشن لغو شد.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به منوی لوکیشن", callback_data=LOCATION_CB)]
            ])
        )
        return SELECTING_LOCATION
    
    try:
        # Get data from context
        subscription_id = context.user_data.get("subscription_id")
        new_server_id = context.user_data.get("selected_server_id")
        
        if not subscription_id or not new_server_id:
            await query.edit_message_text(
                text="⚠️ اطلاعات کافی برای تغییر لوکیشن موجود نیست. لطفاً دوباره تلاش کنید.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 بازگشت", callback_data=LOCATION_CB)]
                ])
            )
            return SELECTING_LOCATION
        
        # Update status message
        await query.edit_message_text(
            text="⏳ در حال تغییر لوکیشن... لطفاً صبر کنید.",
            reply_markup=None
        )
        
        # Get subscription and server objects
        subscription = Subscription.objects.get(id=subscription_id)
        new_server = Server.objects.get(id=new_server_id)
        
        # Perform location change transaction
        with transaction.atomic():
            # 1. Disable old client if exists
            if subscription.client_email and subscription.inbound_id and subscription.server:
                old_client = ThreeXUIClient(subscription.server)
                old_client.remove_client(subscription.inbound_id, subscription.client_email)
            
            # 2. Create new client on new server
            # Find a suitable inbound on the new server
            inbound = Inbound.objects.filter(server=new_server, enable=True).first()
            
            if not inbound:
                raise Exception(f"No suitable inbound found on server {new_server.name}")
            
            # Generate a unique email for the client if needed
            if not subscription.client_email:
                username = subscription.user.username or f"user_{subscription.user.id}"
                subscription.client_email = f"{username}_{subscription.id}@moonvpn.ir"
            
            # Create new client
            new_client = ThreeXUIClient(new_server)
            
            # Calculate expiry time and traffic limit
            expiry_time = subscription.end_date
            traffic_limit_gb = subscription.data_limit_gb
            
            # Add client to new server
            result = new_client.add_client(
                inbound.inbound_id,
                subscription.client_email,
                traffic_limit_gb=traffic_limit_gb,
                expiry_time=expiry_time
            )
            
            if not result:
                raise Exception("Failed to create client on new server")
            
            # 3. Update subscription with new server and inbound
            subscription.server = new_server
            subscription.inbound_id = inbound.inbound_id
            subscription.save()
            
            # Get client config URLs
            client_url = new_client.get_client_url(inbound.inbound_id, subscription.client_email)
            
            if not client_url:
                logger.warning(f"Could not get client URL for {subscription.client_email}")
                client_url = {}
            
            # Store the configuration in context for the next step
            context.user_data["client_config"] = client_url
            context.user_data["new_server"] = {
                "name": new_server.name,
                "location": new_server.location,
                "emoji": get_server_emoji(new_server.location)
            }
        
        # Success message
        message = "✅ *تغییر لوکیشن با موفقیت انجام شد*\n\n"
        message += f"لوکیشن جدید: {context.user_data['new_server']['emoji']} *{context.user_data['new_server']['location']}*\n\n"
        message += "برای دریافت کانفیگ جدید، روی دکمه زیر کلیک کنید:"
        
        keyboard = [
            [InlineKeyboardButton("📋 دریافت کانفیگ جدید", callback_data=SELECT_PROTOCOL)],
            [InlineKeyboardButton("🔙 بازگشت به منوی لوکیشن", callback_data=LOCATION_CB)]
        ]
        
        await query.edit_message_text(
            text=message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
        
    except Exception as e:
        logger.error(f"Error in process_location_change: {e}")
        await query.edit_message_text(
            text=f"⚠️ خطا در تغییر لوکیشن: {str(e)}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت", callback_data=LOCATION_CB)]
            ])
        )
    
    return SELECTING_PROTOCOL

async def select_protocol(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Let user select which protocol config to receive."""
    query = update.callback_query
    await query.answer()
    
    # Get client config from context
    client_config = context.user_data.get("client_config", {})
    
    if not client_config:
        await query.edit_message_text(
            text="⚠️ اطلاعات کانفیگ در دسترس نیست. لطفاً دوباره بخش «دریافت کانفیگ» را از منو انتخاب کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت", callback_data=LOCATION_CB)]
            ])
        )
        return SELECTING_LOCATION
    
    # Create protocol selection keyboard
    keyboard = []
    
    # Add available protocols
    if client_config.get("vmess"):
        keyboard.append([InlineKeyboardButton("📡 VMess", callback_data="protocol_vmess")])
    
    if client_config.get("vless"):
        keyboard.append([InlineKeyboardButton("📡 VLESS", callback_data="protocol_vless")])
    
    if client_config.get("trojan"):
        keyboard.append([InlineKeyboardButton("📡 Trojan", callback_data="protocol_trojan")])
    
    if client_config.get("shadowsocks"):
        keyboard.append([InlineKeyboardButton("📡 Shadowsocks", callback_data="protocol_shadowsocks")])
    
    # Add back button
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data=LOCATION_CB)])
    
    # Send message
    message = "📋 *دریافت کانفیگ*\n\n" \
              "لطفاً پروتکل مورد نظر خود را انتخاب کنید:"
    
    await query.edit_message_text(
        text=message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )
    
    return SELECTING_PROTOCOL

async def send_config(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send the selected protocol configuration to the user."""
    query = update.callback_query
    await query.answer()
    
    # Get the selected protocol from callback data
    callback_data = query.data
    if not callback_data.startswith("protocol_"):
        await query.edit_message_text(
            text="⚠️ خطایی رخ داد. لطفاً دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت", callback_data=LOCATION_CB)]
            ])
        )
        return SELECTING_LOCATION
    
    protocol = callback_data.split("_")[1]
    
    # Get client config from context
    client_config = context.user_data.get("client_config", {})
    config_text = client_config.get(protocol, "")
    
    if not config_text:
        await query.edit_message_text(
            text=f"⚠️ کانفیگ {protocol} در دسترس نیست. لطفاً پروتکل دیگری انتخاب کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به انتخاب پروتکل", callback_data=SELECT_PROTOCOL)],
                [InlineKeyboardButton("🔙 بازگشت به منوی لوکیشن", callback_data=LOCATION_CB)]
            ])
        )
        return SELECTING_PROTOCOL
    
    # Get server info
    server_info = context.user_data.get("new_server", {})
    server_name = server_info.get("name", "Unknown")
    server_location = server_info.get("location", "Unknown")
    server_emoji = server_info.get("emoji", "🌍")
    
    # Create QR code (optional)
    try:
        import qrcode
        from io import BytesIO
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECTION_L,
            box_size=10,
            border=4,
        )
        qr.add_data(config_text)
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save to BytesIO
        bio = BytesIO()
        img.save(bio, 'PNG')
        bio.seek(0)
        
        # Send QR code as photo
        await update.effective_chat.send_photo(
            photo=bio,
            caption=f"🔐 *کانفیگ {protocol.upper()} - {server_location}*\n\n"
                   f"برای استفاده، این QR کد را با نرم‌افزار کلاینت خود اسکن کنید.",
            parse_mode=ParseMode.MARKDOWN
        )
    except ImportError:
        logger.warning("qrcode library not available, skipping QR code generation")
    except Exception as e:
        logger.error(f"Error generating QR code: {e}")
    
    # Send configuration as text
    message = f"🔐 *کانفیگ {protocol.upper()} - {server_location}*\n\n"
    message += "کانفیگ شما:\n`" + config_text + "`\n\n"
    message += "این کانفیگ را در اپلیکیشن کلاینت خود کپی کنید."
    
    # Send as a new message to ensure it can be copied easily
    await update.effective_chat.send_message(
        text=message,
        parse_mode=ParseMode.MARKDOWN
    )
    
    # Update the original message
    await query.edit_message_text(
        text=f"✅ کانفیگ {protocol.upper()} برای سرور {server_emoji} *{server_location}* با موفقیت ارسال شد.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📋 دریافت کانفیگ با پروتکل دیگر", callback_data=SELECT_PROTOCOL)],
            [InlineKeyboardButton("🔙 بازگشت به منوی لوکیشن", callback_data=LOCATION_CB)]
        ]),
        parse_mode=ParseMode.MARKDOWN
    )
    
    return SELECTING_PROTOCOL

async def get_config(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Get the configuration for the user's active subscription."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    user_id = user.id
    
    try:
        # Get user's active subscription
        db_user = User.objects.get(telegram_id=user_id)
        subscription = Subscription.objects.filter(user=db_user, status='active').first()
        
        if not subscription:
            await query.edit_message_text(
                text="⚠️ شما هیچ اشتراک فعالی ندارید. ابتدا باید یک اشتراک خریداری کنید.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🛒 خرید اشتراک", callback_data="buy_subscription")],
                    [InlineKeyboardButton("🔙 بازگشت", callback_data=LOCATION_CB)]
                ])
            )
            return SELECTING_LOCATION
        
        # Check if subscription has client details
        if not subscription.client_email or not subscription.inbound_id or not subscription.server:
            await query.edit_message_text(
                text="⚠️ اطلاعات کانفیگ برای اشتراک شما یافت نشد. لطفاً با پشتیبانی تماس بگیرید.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("💬 تماس با پشتیبانی", callback_data="support")],
                    [InlineKeyboardButton("🔙 بازگشت", callback_data=LOCATION_CB)]
                ])
            )
            return SELECTING_LOCATION
        
        # Get client configuration
        client = ThreeXUIClient(subscription.server)
        client_url = client.get_client_url(subscription.inbound_id, subscription.client_email)
        
        if not client_url:
            await query.edit_message_text(
                text="⚠️ دریافت کانفیگ با خطا مواجه شد. لطفاً با پشتیبانی تماس بگیرید.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("💬 تماس با پشتیبانی", callback_data="support")],
                    [InlineKeyboardButton("🔙 بازگشت", callback_data=LOCATION_CB)]
                ])
            )
            return SELECTING_LOCATION
        
        # Store configuration in context
        context.user_data["client_config"] = client_url
        context.user_data["new_server"] = {
            "name": subscription.server.name,
            "location": subscription.server.location,
            "emoji": get_server_emoji(subscription.server.location)
        }
        
        # Redirect to protocol selection
        return await select_protocol(update, context)
        
    except Exception as e:
        logger.error(f"Error in get_config: {e}")
        await query.edit_message_text(
            text=f"⚠️ خطا در دریافت کانفیگ: {str(e)}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت", callback_data=LOCATION_CB)]
            ])
        )
    
    return SELECTING_LOCATION

def get_location_handler() -> ConversationHandler:
    """Create and return the VPN location management conversation handler."""
    return ConversationHandler(
        entry_points=[
            CommandHandler("location", location_menu),
            CallbackQueryHandler(location_menu, pattern=f"^{LOCATION_CB}$"),
        ],
        states={
            SELECTING_LOCATION: [
                CallbackQueryHandler(list_locations, pattern=f"^{LIST_LOCATIONS}$"),
                CallbackQueryHandler(change_location, pattern=f"^{CHANGE_LOCATION}$"),
                CallbackQueryHandler(get_config, pattern=f"^{GET_CONFIG}$"),
            ],
            CONFIRMING_CHANGE: [
                CallbackQueryHandler(confirm_location_change, pattern=r"^server_\d+$"),
                CallbackQueryHandler(process_location_change, pattern=f"^{CONFIRM_LOCATION}$"),
                CallbackQueryHandler(location_menu, pattern=f"^{CANCEL_CHANGE}$"),
            ],
            SELECTING_PROTOCOL: [
                CallbackQueryHandler(select_protocol, pattern=f"^{SELECT_PROTOCOL}$"),
                CallbackQueryHandler(send_config, pattern=r"^protocol_[a-z]+$"),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(location_menu, pattern=f"^{LOCATION_CB}$"),
            CallbackQueryHandler(location_menu, pattern=f"^{BACK_TO_LOCATIONS}$"),
            CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern="^main_menu$"),
        ],
        name="vpn_location",
        persistent=False,
    ) 