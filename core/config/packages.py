"""
MoonVPN Telegram Bot - Packages Handler.

This module provides functionality to display and select VPN packages.
"""

import logging
from typing import List, Dict, Any

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, ConversationHandler, CommandHandler

from core.database.models.package import Package
from core.database.models.server import Server
from bot.constants import CallbackPatterns, States

logger = logging.getLogger(__name__)

# Package image URL
PACKAGE_IMAGE = "https://example.com/path/to/packages_image.jpg"  # Replace with actual image URL or file_id

async def show_packages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show available packages with beautiful cards."""
    query = update.callback_query
    
    if query:
        await query.answer()
    
    # Get all active packages
    # In a real implementation, this would fetch from the database
    packages = get_all_packages()
    
    message = "🎁 <b>پکیج‌های VPN ویژه</b>\n\n"
    message += "لطفا یکی از پکیج‌های زیر را انتخاب کنید:\n\n"
    
    # Create keyboard for packages
    keyboard = []
    
    for i, package in enumerate(packages, 1):
        # Create a beautiful description for each package
        package_description = (
            f"📦 <b>{package['name']}</b>\n"
            f"⏱ مدت زمان: {package['duration_days']} روز\n"
            f"📊 ترافیک: {package['traffic_gb']} گیگابایت\n"
            f"💰 قیمت: {package['price']:,} تومان\n"
            f"{package['description']}\n"
            "➖➖➖➖➖➖➖➖➖➖➖➖\n"
        )
        
        message += package_description
        
        # Add button for each package
        keyboard.append([
            InlineKeyboardButton(f"📦 خرید پکیج {package['name']}", 
                               callback_data=f"{CallbackPatterns.PACKAGE_SELECT}_{package['id']}")
        ])
    
    # Add navigation buttons
    keyboard.append([
        InlineKeyboardButton("🔙 بازگشت", callback_data=CallbackPatterns.BUY_ACCOUNT),
        InlineKeyboardButton("🏠 منوی اصلی", callback_data=CallbackPatterns.MAIN_MENU)
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Try to edit message or send a new one
    if query:
        try:
            if hasattr(query.message, 'photo'):
                await query.edit_message_caption(
                    caption=message,
                    reply_markup=reply_markup,
                    parse_mode="HTML"
                )
            else:
                await query.edit_message_text(
                    text=message,
                    reply_markup=reply_markup,
                    parse_mode="HTML"
                )
        except Exception as e:
            logger.error(f"Error updating package message: {e}")
            try:
                await query.message.reply_text(
                    text=message,
                    reply_markup=reply_markup,
                    parse_mode="HTML"
                )
            except Exception as e2:
                logger.error(f"Failed to send new package message: {e2}")
    else:
        # This is a direct command
        try:
            await update.message.reply_photo(
                photo=PACKAGE_IMAGE,
                caption=message,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Error sending package message with image: {e}")
            await update.message.reply_text(
                text=message,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
    
    return States.SELECTING_PACKAGE

async def select_package(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle package selection."""
    query = update.callback_query
    await query.answer()
    
    # Extract package id from callback data
    package_id = query.data.split("_")[1]
    context.user_data['selected_package_id'] = package_id
    
    # Get package details
    package = get_package_by_id(package_id)
    
    if not package:
        await query.message.reply_text("❌ پکیج مورد نظر یافت نشد. لطفا دوباره تلاش کنید.")
        return States.SELECTING_PACKAGE
    
    # Get servers for this package
    servers = get_servers_for_package(package_id)
    
    if not servers:
        await query.message.reply_text("❌ متأسفانه در حال حاضر سروری برای این پکیج در دسترس نیست. لطفا پکیج دیگری انتخاب کنید.")
        return States.SELECTING_PACKAGE
    
    # Store package in context
    context.user_data['package'] = package
    
    # Create message for location selection
    message = (
        f"🌍 <b>انتخاب لوکیشن</b>\n\n"
        f"پکیج انتخابی شما: <b>{package['name']}</b>\n"
        f"⏱ مدت زمان: {package['duration_days']} روز\n"
        f"📊 ترافیک: {package['traffic_gb']} گیگابایت\n"
        f"💰 قیمت: {package['price']:,} تومان\n\n"
        f"اکنون لطفا لوکیشن مورد نظر خود را انتخاب کنید:"
    )
    
    # Create keyboard for servers/locations
    keyboard = []
    
    for server in servers:
        flag = get_country_flag(server['country'])
        keyboard.append([
            InlineKeyboardButton(f"{flag} {server['location']} - {server['country']}", 
                               callback_data=f"{CallbackPatterns.LOCATION_SELECT}_{server['id']}")
        ])
    
    # Add back button
    keyboard.append([
        InlineKeyboardButton("🔙 بازگشت به پکیج‌ها", callback_data=f"{CallbackPatterns.PACKAGE_SELECT}")
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Edit message
    try:
        await query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error updating location message: {e}")
        await query.message.reply_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
    
    return States.SELECTING_LOCATION

def get_all_packages() -> List[Dict[str, Any]]:
    """Get all active packages from database."""
    # This would typically fetch from your database
    # Using hardcoded data for demonstration
    return [
        {
            "id": "basic",
            "name": "پکیج اقتصادی",
            "description": "✅ مناسب برای استفاده روزانه\n✅ اتصال همزمان 1 دستگاه",
            "duration_days": 30,
            "traffic_gb": 30,
            "price": 59000,
            "is_active": True
        },
        {
            "id": "standard",
            "name": "پکیج استاندارد",
            "description": "✅ سرعت بالاتر\n✅ اتصال همزمان 2 دستگاه",
            "duration_days": 30,
            "traffic_gb": 60,
            "price": 89000,
            "is_active": True
        },
        {
            "id": "premium",
            "name": "پکیج ویژه",
            "description": "✅ بالاترین سرعت\n✅ اتصال همزمان 3 دستگاه\n✅ پشتیبانی اختصاصی",
            "duration_days": 30,
            "traffic_gb": 100,
            "price": 129000,
            "is_active": True
        },
        {
            "id": "vip",
            "name": "پکیج VIP",
            "description": "✅ کیفیت فوق العاده\n✅ اتصال همزمان 5 دستگاه\n✅ پشتیبانی اختصاصی\n✅ تضمین سرعت",
            "duration_days": 30,
            "traffic_gb": 200,
            "price": 199000,
            "is_active": True
        }
    ]

def get_package_by_id(package_id: str) -> Dict[str, Any]:
    """Get package details by ID."""
    packages = get_all_packages()
    for package in packages:
        if package['id'] == package_id:
            return package
    return None

def get_servers_for_package(package_id: str) -> List[Dict[str, Any]]:
    """Get available servers for a package."""
    # This would typically fetch from your database based on package compatibility
    # Using hardcoded data for demonstration
    return [
        {
            "id": "server1",
            "name": "Germany 1",
            "location": "Frankfurt",
            "country": "Germany",
            "is_active": True
        },
        {
            "id": "server2",
            "name": "Netherlands 1",
            "location": "Amsterdam",
            "country": "Netherlands",
            "is_active": True
        },
        {
            "id": "server3",
            "name": "France 1",
            "location": "Paris",
            "country": "France",
            "is_active": True
        },
        {
            "id": "server4",
            "name": "US East",
            "location": "New York",
            "country": "United States",
            "is_active": True
        }
    ]

def get_country_flag(country: str) -> str:
    """Get flag emoji for a country."""
    flags = {
        "Germany": "🇩🇪",
        "Netherlands": "🇳🇱",
        "France": "🇫🇷",
        "United States": "🇺🇸",
        "United Kingdom": "🇬🇧",
        "Canada": "🇨🇦",
        "Japan": "🇯🇵",
        "Singapore": "🇸🇬",
        "Turkey": "🇹🇷"
    }
    return flags.get(country, "🌍")

def get_packages_handlers() -> List:
    """Return all handlers related to packages."""
    return [
        CommandHandler("packages", show_packages),
        CallbackQueryHandler(show_packages, pattern=f"^{CallbackPatterns.PACKAGE_SELECT}$"),
        CallbackQueryHandler(select_package, pattern=f"^{CallbackPatterns.PACKAGE_SELECT}_")
    ] 