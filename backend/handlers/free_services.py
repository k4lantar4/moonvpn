"""
MoonVPN Telegram Bot - Free Services Handler.

This module provides functionality to offer limited free VPN and proxy services.
"""

import logging
import random
import string
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, 
    CallbackQueryHandler, 
    CommandHandler, 
    ConversationHandler
)

from core.database.models.user import User
from bot.constants import CallbackPatterns, States

logger = logging.getLogger(__name__)

# Free services image URL
FREE_VPN_IMAGE = "https://example.com/path/to/free_vpn.jpg"  # Replace with actual image URL or file_id
FREE_PROXY_IMAGE = "https://example.com/path/to/free_proxy.jpg"  # Replace with actual image URL or file_id

# States for the free services conversation
(
    FREE_SERVICES_MAIN,
    FREE_VPN_DETAIL,
    FREE_PROXY_DETAIL,
) = range(3)

async def free_services_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show free services menu."""
    user = update.effective_user
    message = update.message or update.callback_query.message
    
    # Get user from database
    db_user = User.get_by_telegram_id(user.id) if hasattr(User, 'get_by_telegram_id') else None
    
    # Create message for free services
    free_services_text = (
        "🎁 <b>خدمات رایگان MoonVPN</b>\n\n"
        "کاربر گرامی، می‌توانید از خدمات رایگان زیر استفاده کنید:\n\n"
        "1️⃣ <b>VPN رایگان (محدود)</b>\n"
        "• ترافیک: 200 مگابایت\n"
        "• مدت زمان: 1 روز\n"
        "• سرورهای محدود\n\n"
        "2️⃣ <b>پروکسی MTProto و SOCKS5</b>\n"
        "• سرعت مناسب\n"
        "• بدون محدودیت زمانی\n"
        "• مناسب برای تلگرام و وب‌گردی\n\n"
        "این خدمات رایگان با هدف آشنایی شما با کیفیت سرویس‌های ما ارائه می‌شوند."
        " برای دریافت ترافیک بیشتر و سرعت بالاتر، از پکیج‌های ویژه ما استفاده کنید."
    )
    
    # Create keyboard for free services
    keyboard = [
        [
            InlineKeyboardButton("🔐 دریافت VPN رایگان", callback_data=f"{CallbackPatterns.FREE_SERVICE}_vpn"),
            InlineKeyboardButton("🔄 دریافت پروکسی رایگان", callback_data=f"{CallbackPatterns.FREE_SERVICE}_proxy")
        ],
        [
            InlineKeyboardButton("📖 راهنمای استفاده از VPN", callback_data=f"{CallbackPatterns.HELP}_connection"),
            InlineKeyboardButton("📋 راهنمای پروکسی", callback_data=f"{CallbackPatterns.FREE_SERVICE}_proxy_help")
        ],
        [InlineKeyboardButton("🛒 خرید اشتراک VIP", callback_data=f"{CallbackPatterns.BUY_ACCOUNT}")],
        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data=CallbackPatterns.MAIN_MENU)]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send or edit message
    try:
        if update.callback_query:
            await update.callback_query.answer()
            
            if hasattr(update.callback_query.message, 'photo'):
                await update.callback_query.edit_message_caption(
                    caption=free_services_text,
                    reply_markup=reply_markup,
                    parse_mode="HTML"
                )
            else:
                await update.callback_query.edit_message_text(
                    text=free_services_text,
                    reply_markup=reply_markup,
                    parse_mode="HTML"
                )
        else:
            try:
                await message.reply_photo(
                    photo=FREE_VPN_IMAGE,
                    caption=free_services_text,
                    reply_markup=reply_markup,
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.error(f"Error sending free services with image: {e}")
                await message.reply_text(
                    text=free_services_text,
                    reply_markup=reply_markup,
                    parse_mode="HTML"
                )
    except Exception as e:
        logger.error(f"Error in free services command: {e}")
    
    return FREE_SERVICES_MAIN

async def get_free_vpn(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Generate and provide free VPN account."""
    query = update.callback_query
    await query.answer()
    user = update.effective_user
    
    # Check if user has already claimed a free VPN
    # In a real implementation, check database
    has_active_free_vpn = False  # Placeholder
    can_get_new_one = True  # Placeholder
    
    if has_active_free_vpn:
        # User already has an active free VPN
        free_vpn_account = get_user_free_vpn(user.id)  # Placeholder function
        expiry_time = datetime.now() + timedelta(hours=24)  # Placeholder
        
        vpn_text = (
            "🔐 <b>VPN رایگان شما</b>\n\n"
            "شما از قبل یک اکانت VPN رایگان فعال دارید:\n\n"
            f"📱 کانفیگ شما: <code>{free_vpn_account['config']}</code>\n\n"
            f"⏱ زمان باقی‌مانده: {format_remaining_time(expiry_time)}\n"
            f"📊 ترافیک باقی‌مانده: {free_vpn_account['remaining_traffic']} مگابایت\n\n"
            "برای استفاده، کانفیگ را کپی کرده و در اپلیکیشن وارد کنید.\n"
            "برای راهنمای اتصال، روی دکمه «راهنمای اتصال» کلیک کنید."
        )
        
        # Create keyboard
        keyboard = [
            [
                InlineKeyboardButton("📋 کپی کانفیگ", callback_data=f"{CallbackPatterns.FREE_SERVICE}_copy_vpn"),
                InlineKeyboardButton("📱 راهنمای اتصال", callback_data=f"{CallbackPatterns.HELP}_connection")
            ],
            [InlineKeyboardButton("🔙 بازگشت", callback_data=f"{CallbackPatterns.FREE_SERVICE}")]
        ]
    elif not can_get_new_one:
        # User can't get a new free VPN yet
        next_available = datetime.now() + timedelta(days=1)  # Placeholder
        
        vpn_text = (
            "⏳ <b>محدودیت VPN رایگان</b>\n\n"
            "شما قبلاً از سرویس VPN رایگان استفاده کرده‌اید و در حال حاضر امکان دریافت مجدد آن را ندارید.\n\n"
            f"⏱ زمان تا درخواست بعدی: {format_remaining_time(next_available)}\n\n"
            "برای استفاده بدون محدودیت، یکی از پکیج‌های ویژه ما را خریداری کنید."
        )
        
        # Create keyboard
        keyboard = [
            [InlineKeyboardButton("🛒 خرید اشتراک VIP", callback_data=f"{CallbackPatterns.BUY_ACCOUNT}")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data=f"{CallbackPatterns.FREE_SERVICE}")]
        ]
    else:
        # Generate new free VPN account
        free_vpn_account = generate_free_vpn(user.id)  # Placeholder function
        expiry_time = datetime.now() + timedelta(hours=24)  # Placeholder
        
        vpn_text = (
            "🎁 <b>VPN رایگان شما آماده است!</b>\n\n"
            "کانفیگ VPN رایگان شما با موفقیت ایجاد شد:\n\n"
            f"📱 کانفیگ شما: <code>{free_vpn_account['config']}</code>\n\n"
            f"⏱ مدت زمان: 24 ساعت (منقضی در {expiry_time.strftime('%Y-%m-%d %H:%M')})\n"
            f"📊 ترافیک: 200 مگابایت\n"
            f"🌍 سرور: {free_vpn_account['server']}\n\n"
            "<b>نحوه استفاده:</b>\n"
            "1. کانفیگ را کپی کنید\n"
            "2. اپلیکیشن مناسب را نصب کنید\n"
            "3. کانفیگ را در اپلیکیشن وارد کنید\n"
            "4. به اینترنت وصل شوید\n\n"
            "برای راهنمای کامل، روی دکمه «راهنمای اتصال» کلیک کنید."
        )
        
        # Create keyboard
        keyboard = [
            [
                InlineKeyboardButton("📋 کپی کانفیگ", callback_data=f"{CallbackPatterns.FREE_SERVICE}_copy_vpn"),
                InlineKeyboardButton("📱 راهنمای اتصال", callback_data=f"{CallbackPatterns.HELP}_connection")
            ],
            [
                InlineKeyboardButton("🔄 تازه‌سازی", callback_data=f"{CallbackPatterns.FREE_SERVICE}_refresh_vpn"),
                InlineKeyboardButton("🛒 خرید اشتراک VIP", callback_data=f"{CallbackPatterns.BUY_ACCOUNT}")
            ],
            [InlineKeyboardButton("🔙 بازگشت", callback_data=f"{CallbackPatterns.FREE_SERVICE}")]
        ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Edit message
    try:
        if hasattr(query.message, 'photo'):
            await query.edit_message_caption(
                caption=vpn_text,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
        else:
            await query.edit_message_text(
                text=vpn_text,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
    except Exception as e:
        logger.error(f"Error showing free VPN: {e}")
    
    return FREE_VPN_DETAIL

async def get_free_proxy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Generate and provide free proxy server details."""
    query = update.callback_query
    await query.answer()
    user = update.effective_user
    
    # Generate proxy information
    # In real implementation, get from database or generate
    mtproto_proxy = generate_mtproto_proxy()  # Placeholder function
    socks5_proxy = generate_socks5_proxy()  # Placeholder function
    
    proxy_text = (
        "🔄 <b>پروکسی‌های رایگان</b>\n\n"
        "<b>MTProto Proxy (مخصوص تلگرام):</b>\n"
        f"🔗 لینک: <code>{mtproto_proxy['link']}</code>\n"
        f"🔑 سیکرت: <code>{mtproto_proxy['secret']}</code>\n"
        f"🌍 سرور: <code>{mtproto_proxy['server']}</code>\n"
        f"🔌 پورت: <code>{mtproto_proxy['port']}</code>\n\n"
        
        "<b>SOCKS5 Proxy (همه منظوره):</b>\n"
        f"🌍 سرور: <code>{socks5_proxy['server']}</code>\n"
        f"🔌 پورت: <code>{socks5_proxy['port']}</code>\n"
        f"👤 نام کاربری: <code>{socks5_proxy['username']}</code>\n"
        f"🔑 رمز عبور: <code>{socks5_proxy['password']}</code>\n\n"
        
        "<b>نکات مهم:</b>\n"
        "• این پروکسی‌ها هر 24 ساعت به‌روزرسانی می‌شوند\n"
        "• کیفیت و سرعت آنها محدود است\n"
        "• برای استفاده بدون محدودیت، اشتراک VIP تهیه کنید"
    )
    
    # Create keyboard
    keyboard = [
        [
            InlineKeyboardButton("📋 کپی MTProto", callback_data=f"{CallbackPatterns.FREE_SERVICE}_copy_mtproto"),
            InlineKeyboardButton("📋 کپی SOCKS5", callback_data=f"{CallbackPatterns.FREE_SERVICE}_copy_socks")
        ],
        [
            InlineKeyboardButton("📱 راهنمای استفاده", callback_data=f"{CallbackPatterns.FREE_SERVICE}_proxy_help"),
            InlineKeyboardButton("🔄 تازه‌سازی", callback_data=f"{CallbackPatterns.FREE_SERVICE}_refresh_proxy")
        ],
        [InlineKeyboardButton("🔙 بازگشت", callback_data=f"{CallbackPatterns.FREE_SERVICE}")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Edit message
    try:
        if hasattr(query.message, 'photo'):
            await query.edit_message_media(
                media=InputMediaPhoto(
                    media=FREE_PROXY_IMAGE,
                    caption=proxy_text,
                    parse_mode="HTML"
                ),
                reply_markup=reply_markup
            )
        else:
            await query.edit_message_text(
                text=proxy_text,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
    except Exception as e:
        logger.error(f"Error showing free proxy: {e}")
        try:
            await query.edit_message_text(
                text=proxy_text,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
        except Exception as e2:
            logger.error(f"Error showing free proxy (fallback): {e2}")
    
    return FREE_PROXY_DETAIL

async def show_proxy_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show help guide for using proxies."""
    query = update.callback_query
    await query.answer()
    
    help_text = (
        "📖 <b>راهنمای استفاده از پروکسی</b>\n\n"
        "<b>MTProto Proxy در تلگرام:</b>\n"
        "1. در تلگرام به تنظیمات بروید\n"
        "2. گزینه «داده‌ها و حافظه» را انتخاب کنید\n"
        "3. گزینه «تنظیمات پروکسی» را انتخاب کنید\n"
        "4. روی «پروکسی جدید» کلیک کنید\n"
        "5. گزینه «MTPROTO Proxy» را انتخاب کنید\n"
        "6. اطلاعات سرور، پورت و سیکرت را وارد کنید\n"
        "7. روی «ذخیره» کلیک کنید\n\n"
        
        "<b>SOCKS5 Proxy در مرورگرها:</b>\n"
        "1. به تنظیمات مرورگر خود بروید\n"
        "2. به بخش «پیشرفته» و سپس «شبکه» بروید\n"
        "3. تنظیمات پروکسی را باز کنید\n"
        "4. گزینه پروکسی SOCKS5 را انتخاب کنید\n"
        "5. آدرس سرور و پورت را وارد کنید\n"
        "6. اگر گزینه‌ای برای نام کاربری و رمز عبور وجود داشت، آنها را وارد کنید\n"
        "7. تنظیمات را ذخیره کنید\n\n"
        
        "<b>نکته مهم:</b> پروکسی‌های رایگان ممکن است سرعت و پایداری کمتری داشته باشند. برای تجربه بهتر، از سرویس‌های VPN ما استفاده کنید."
    )
    
    # Create keyboard
    keyboard = [
        [InlineKeyboardButton("🔙 بازگشت به پروکسی‌ها", callback_data=f"{CallbackPatterns.FREE_SERVICE}_proxy")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Edit message
    try:
        await query.edit_message_text(
            text=help_text,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error showing proxy help: {e}")
    
    return FREE_PROXY_DETAIL

async def copy_config(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle copy config callback."""
    query = update.callback_query
    config_type = query.data.split("_")[-1]
    
    if config_type == "vpn":
        # Get user's free VPN config
        # In real implementation, fetch from database
        free_vpn_account = get_user_free_vpn(update.effective_user.id)  # Placeholder function
        await query.answer("کانفیگ VPN کپی شد!")
        return FREE_VPN_DETAIL
    elif config_type == "mtproto":
        # Get MTProto proxy info
        # In real implementation, fetch from database
        mtproto_proxy = generate_mtproto_proxy()  # Placeholder function
        await query.answer("پروکسی MTProto کپی شد!")
        return FREE_PROXY_DETAIL
    elif config_type == "socks":
        # Get SOCKS5 proxy info
        # In real implementation, fetch from database
        socks5_proxy = generate_socks5_proxy()  # Placeholder function
        await query.answer("پروکسی SOCKS5 کپی شد!")
        return FREE_PROXY_DETAIL
    else:
        await query.answer("خطا در کپی کردن!")
        return FREE_SERVICES_MAIN

async def refresh_service(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle refresh service callback."""
    query = update.callback_query
    service_type = query.data.split("_")[-1]
    
    await query.answer("در حال به‌روزرسانی...")
    
    if service_type == "vpn":
        # Refresh VPN service
        return await get_free_vpn(update, context)
    elif service_type == "proxy":
        # Refresh proxy service
        return await get_free_proxy(update, context)
    else:
        return FREE_SERVICES_MAIN

async def free_services_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle callbacks from free services menu."""
    query = update.callback_query
    await query.answer()
    
    # Parse the callback data
    callback_data = query.data
    parts = callback_data.split("_")
    
    if len(parts) < 2:
        # Default to main menu
        return await free_services_command(update, context)
    
    action = parts[1]
    
    if action == "vpn":
        # Show free VPN options
        return await get_free_vpn(update, context)
    elif action == "proxy":
        # Show free proxy options
        return await get_free_proxy(update, context)
    elif action == "proxy_help":
        # Show proxy help guide
        return await show_proxy_help(update, context)
    elif action.startswith("copy_"):
        # Handle copy config actions
        return await copy_config(update, context)
    elif action.startswith("refresh_"):
        # Handle refresh service actions
        return await refresh_service(update, context)
    else:
        # Default to main menu
        return await free_services_command(update, context)

# Helper functions

def generate_free_vpn(user_id: int) -> Dict[str, Any]:
    """Generate a free VPN configuration.
    
    In a real implementation, this would create an account in the VPN server
    and return the configuration details.
    """
    # Mock data for demonstration
    server = random.choice(["هلند", "آلمان", "فرانسه"])
    uuid = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
    
    # Generate a fake config string
    config = f"vless://{uuid}@free.moonvpn.ir:443?security=tls&type=ws&path=%2Ffree#MoonVPN_Free_{server}"
    
    return {
        "user_id": user_id,
        "server": server,
        "config": config,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "expires_at": (datetime.now() + timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S"),
        "total_traffic": 200,  # MB
        "remaining_traffic": 200,  # MB
    }

def get_user_free_vpn(user_id: int) -> Optional[Dict[str, Any]]:
    """Get user's free VPN account if it exists.
    
    In a real implementation, this would fetch from the database.
    """
    # Mock data for demonstration
    return generate_free_vpn(user_id)

def generate_mtproto_proxy() -> Dict[str, Any]:
    """Generate MTProto proxy information.
    
    In a real implementation, this would return actual proxy server details.
    """
    # Mock data for demonstration
    server = "mtproto.free.moonvpn.ir"
    port = "443"
    secret = "ee" + ''.join(random.choices(string.hexdigits.lower(), k=30))
    link = f"https://t.me/proxy?server={server}&port={port}&secret={secret}"
    
    return {
        "server": server,
        "port": port,
        "secret": secret,
        "link": link
    }

def generate_socks5_proxy() -> Dict[str, Any]:
    """Generate SOCKS5 proxy information.
    
    In a real implementation, this would return actual proxy server details.
    """
    # Mock data for demonstration
    server = "socks.free.moonvpn.ir"
    port = "1080"
    username = "free_" + ''.join(random.choices(string.ascii_lowercase, k=5))
    password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    
    return {
        "server": server,
        "port": port,
        "username": username,
        "password": password
    }

def format_remaining_time(target_time: datetime) -> str:
    """Format the remaining time until a target datetime."""
    now = datetime.now()
    if target_time < now:
        return "منقضی شده"
    
    diff = target_time - now
    hours, remainder = divmod(diff.total_seconds(), 3600)
    minutes, _ = divmod(remainder, 60)
    
    if hours >= 24:
        days = int(hours // 24)
        hours = int(hours % 24)
        return f"{days} روز و {hours} ساعت"
    else:
        return f"{int(hours)} ساعت و {int(minutes)} دقیقه"

def get_free_services_handlers() -> List:
    """Return all handlers related to free services."""
    
    free_services_conversation = ConversationHandler(
        entry_points=[
            CommandHandler("free", free_services_command),
            CallbackQueryHandler(free_services_command, pattern=f"^{CallbackPatterns.FREE_SERVICES}$")
        ],
        states={
            FREE_SERVICES_MAIN: [
                CallbackQueryHandler(free_services_callback, pattern=f"^{CallbackPatterns.FREE_SERVICE}_"),
                CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern=f"^{CallbackPatterns.MAIN_MENU}$"),
                CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern=f"^{CallbackPatterns.BUY_ACCOUNT}$")
            ],
            FREE_VPN_DETAIL: [
                CallbackQueryHandler(free_services_callback, pattern=f"^{CallbackPatterns.FREE_SERVICE}_"),
                CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern=f"^{CallbackPatterns.BUY_ACCOUNT}$")
            ],
            FREE_PROXY_DETAIL: [
                CallbackQueryHandler(free_services_callback, pattern=f"^{CallbackPatterns.FREE_SERVICE}_"),
                CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern=f"^{CallbackPatterns.BUY_ACCOUNT}$")
            ]
        },
        fallbacks=[
            CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern=f"^{CallbackPatterns.MAIN_MENU}$"),
            CommandHandler("start", lambda u, c: ConversationHandler.END)
        ],
        name="free_services_conversation",
        persistent=False
    )
    
    return [free_services_conversation] 